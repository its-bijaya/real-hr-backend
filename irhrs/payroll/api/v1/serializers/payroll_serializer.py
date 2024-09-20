import json

from django.contrib.auth import get_user_model
from datetime import timedelta
from django.db import transaction
from django.db.models import Q, F, ExpressionWrapper, DateField
from django.db.transaction import atomic
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField, ReadOnlyField
from rest_framework.utils import model_meta

from irhrs.core.constants.organization import GLOBAL, PAYROLL_APPROVAL_NEEDED_EMAIL, PAYROLL_CONFIRMATION_BY_HR
from irhrs.core.constants.payroll import SALARY_DEDUCTION, PENDING
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.change_request import get_changes
from irhrs.core.utils.common import get_today
from irhrs.core.utils.email import send_email_as_per_settings
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.organization.api.v1.serializers.division import \
    OrganizationDivisionSerializer
from irhrs.organization.api.v1.serializers.fiscal_year import FiscalYearSerializer
from irhrs.organization.api.v1.serializers.organization import OrganizationSerializer
from irhrs.organization.models import Organization, FY, FiscalYear
from irhrs.payroll.models import (
    Package,
    Heading,
    HeadingDependency,
    PackageHeadingDependency,
    PackageHeading,
    HEADING_TYPES_NULL_FIELDS,
    DEFAULT_HEADING_FIELDS_OF_PAYROLL_SETTING_TYPE,
    SalaryHolding,
    Payroll,
    ReportRowRecord,
    UserExperiencePackageSlot,
    EmployeePayroll,
    OverviewConfig,
    OrganizationPayrollConfig,
    ReportSalaryBreakDownRangeConfig,
    ExternalTaxDiscount,
    EmployeePayrollHistory, PayrollEditHistoryAmount, APPROVED,
    CONFIRMED, APPROVAL_PENDING, REJECTED, GENERATED, PayrollApproval, PayrollApprovalHistory,
    SignedPayrollHistory, EmployeePayrollComment, CREATED_PACKAGE, UPDATED_PACKAGE,
    ASSIGNED, CLONED_PACKAGE)
from irhrs.payroll.tasks import create_package_activity
from irhrs.payroll.utils import helpers
from irhrs.payroll.models.advance_salary_request import AdvanceSalaryRepayment
from irhrs.payroll.utils.calculator_variable import CalculatorVariable
from irhrs.payroll.utils.mixins import InputChoiceSerializer
from irhrs.payroll.utils.rule_validator import Equation
from irhrs.permission.constants.permissions import GENERATE_PAYROLL_PERMISSION, \
    PAYROLL_REPORT_PERMISSION
from irhrs.users.api.v1.serializers.experience import UserExperienceSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer, \
    UserThumbnailSerializer, UserThickSerializer
from irhrs.users.models import UserExperience
from irhrs.users.models import UserLegalInfo
from irhrs.users.models.other import UserBank

Employee = get_user_model()

PayrollEmployeeSerializer = UserThinSerializer


class RelatedFieldStr(serializers.RelatedField):
    def to_representation(self, value):
        if value:
            return value.__str__()
        else:
            return None


class HeadingOrderSerializer(serializers.ModelSerializer):
    payroll_setting_type = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()

    class Meta:
        model = Heading
        fields = ('id', 'order', 'payroll_setting_type', 'name')


class HeadingSerializer(InputChoiceSerializer, DynamicFieldsModelSerializer):
    label = serializers.ReadOnlyField(source='__str__')
    # order = serializers.IntegerField(
    #     validators=[UniqueValidator(queryset=Heading.objects.all())]
    # )

    organization = serializers.SlugRelatedField(
        queryset=Organization.objects.all(),
        many=False,
        slug_field='slug'
    )
    rules = serializers.JSONField(allow_null=False)
    is_heading_used = serializers.ReadOnlyField(allow_null=True)

    # next_order = serializers.ReadOnlyField(source='get_next_heading_order')

    class Meta:
        model = Heading
        fields = '__all__'

    def validate_name(self, value):
        value = ' '.join(value.split())
        if value.replace(' ', '').isalpha():
            return value
        else:
            raise serializers.ValidationError(
                'Only alphabetic characters are accepted')

    def validate(self, obj):
        self.validate_heading_name(
            instance=self.instance,
            heading_name=obj.get('name'),
            organization=obj.get('organization'),
        )
        conditional_null_fields = [
            'duration_unit',
            'taxable',
            'benefit_type',
            'absent_days_impact'
        ]

        none_mapping = HEADING_TYPES_NULL_FIELDS

        heading_type = obj.get('type')
        organization = obj.get('organization')
        payroll_setting_type = obj.get('payroll_setting_type')

        from irhrs.payroll.utils.generate import (
            raise_validation_error_if_payroll_in_generated_or_processing_state
        )
        raise_validation_error_if_payroll_in_generated_or_processing_state(organization)

        validation_dict = dict()

        available_types = DEFAULT_HEADING_FIELDS_OF_PAYROLL_SETTING_TYPE.get(
            payroll_setting_type, {'available_types': []}
        ).get('available_types', [])
        available_types += ['Type1Cnst', 'Type2Cnst']

        if heading_type not in available_types:
            validation_dict['type'] = [f'{heading_type} is not available for {payroll_setting_type}']

        duration_unit = obj.get('duration_unit', None)
        hourly_heading_source = obj.get('hourly_heading_source', None)

        # START: Only accept not of type 'Type1Cnst'|'Type2Cnst' hourly heading names tracked by RHRS
        if duration_unit == 'Hourly' and heading_type in ['Addition', 'Deduction'] and not hourly_heading_source:
            validation_dict['hourly_heading_source'] = ['This field is required if duration unit is set to Hourly.']
        elif not (duration_unit == 'Hourly' and heading_type in ['Addition', 'Deduction']):
            obj['hourly_heading_source'] = None
        # END: Only accept heading names tracked by RHRS

        # START: Daily Heading Validation
        deduct_amount_on_leave = obj.get('deduct_amount_on_leave', None)
        pay_when_present_holiday_offday = obj.get('pay_when_present_holiday_offday', None)
        deduct_amount_on_remote_work = obj.get('deduct_amount_on_remote_work', None)

        if duration_unit == 'Daily':
            if deduct_amount_on_leave is None:
                validation_dict['deduct_amount_on_leave'] = ['This field is required for Daily heading.']
            if pay_when_present_holiday_offday is None:
                validation_dict['pay_when_present_holiday_offday'] = ['This field is required for Daily heading.']
            if deduct_amount_on_remote_work is None:
                validation_dict['deduct_amount_on_remote_work'] = ['This field is required for Daily heading']
        else:
            obj['deduct_amount_on_leave'] = None
            obj['pay_when_present_holiday_offday'] = None
            obj['deduct_amount_on_remote_work'] = None
        # END: Daily Heading Validation


        if heading_type in none_mapping.keys():
            for key in conditional_null_fields:
                if key in none_mapping[heading_type]:
                    obj[key] = None
                else:
                    if obj.get(key) is None:
                        validation_dict[key] = ['This field is required']

        else:
            for key in conditional_null_fields:
                if obj.get(key) is None:
                    validation_dict[key] = ['This field is required']

        if not validation_dict.keys():
            heading = Heading(**obj)
            is_valid, rule_validator = heading.rule_is_valid()
            if not is_valid:
                validation_dict['rules'] = rule_validator.error_messages
            else:
                obj['dependencies'] = rule_validator.actual_dependent_headings

        if validation_dict.keys():
            raise serializers.ValidationError(validation_dict)

        if self.instance and self.instance.is_heading_used:
            changes = get_changes(obj, self.instance, show_all_changes=False)
            change_set = set(changes.keys()) - {"rules", "year_to_date", "dependencies",
                                                "is_editable"}

            if change_set:
                raise serializers.ValidationError("Can only update rules and ytd if package is used.")

        return obj

    # def get_validators(self):
    #     validators = super().get_validators()
    #     if not self.instance:
    #         validators = list(filter(lambda v: v.fields != ('organization', 'order'), validators))
    #     return validators

    @staticmethod
    def validate_heading_name(instance, heading_name, organization):
        """
        Ensures the heading name for the organization does not duplicate.
        """
        if Heading.objects.filter(
            organization=organization,
            name__iexact=heading_name,
        ).exclude(
            Q(id=instance.id) if instance else Q()
        ).exists():
            raise serializers.ValidationError({
                'name': _(
                    'The heading with the name '
                    + heading_name
                    + ' already exists for '
                    + organization.name
                )
            })

    def create(self, validated_data):
        dependencies = validated_data.pop('dependencies')
        instance = None
        with transaction.atomic():
            try:
                Heading.objects.get(
                    organization=validated_data.get('organization'),
                    order=validated_data.get('order')
                )
                Heading.objects.filter(
                    order__gte=validated_data.get('order'),
                    organization=validated_data.get('organization'),
                ).update(
                    order=F('order') + 1
                )
                instance = super().create(validated_data)

            except Heading.DoesNotExist:
                instance = super().create(validated_data)

            HeadingDependency.objects.bulk_create(
                [
                    HeadingDependency(source=instance, target=target)
                    for target in dependencies
                ]
            )
            return instance

    def update(self, instance, validated_data):
        dependencies = validated_data.pop('dependencies')
        obj = None
        try:
            obj = Heading.objects.get(
                organization=validated_data.get('organization'),
                order=validated_data.get('order')
            )
        except Heading.DoesNotExist:
            pass
        if not obj or (obj and (obj.id == instance.id)):
            instance = super().update(instance, validated_data)
            HeadingDependency.objects.filter(source=instance).delete()
            HeadingDependency.objects.bulk_create(
                [
                    HeadingDependency(source=instance, target=target)
                    for target in dependencies
                ]
            )
            return instance
        else:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                'Order with particular organization already exists')


class PackageHeadingSerializer(InputChoiceSerializer,
                               serializers.ModelSerializer):
    heading_name = RelatedFieldStr(source='heading', read_only=True)
    payroll_setting_type = serializers.ReadOnlyField(
        source='heading.payroll_setting_type')
    year_to_date = serializers.ReadOnlyField(source='heading.year_to_date')

    def validate(self, obj):
        conditional_null_fields = [
            'duration_unit',
            'taxable',
            'benefit_type',
            'absent_days_impact'
        ]

        from irhrs.payroll.utils.generate import (
            raise_validation_error_if_payroll_in_generated_or_processing_state
        )
        package = obj.get("package")

        if package:
            raise_validation_error_if_payroll_in_generated_or_processing_state(
                organization=package.organization
            )
        none_mapping = HEADING_TYPES_NULL_FIELDS

        heading_type = obj.get('type')
        payroll_setting_type = getattr(obj.get('heading'), 'payroll_setting_type')

        field_errors = dict()

        available_types = DEFAULT_HEADING_FIELDS_OF_PAYROLL_SETTING_TYPE.get(
            payroll_setting_type, {'available_types': []}
        ).get('available_types', [])
        available_types += ['Type1Cnst', 'Type2Cnst']

        if heading_type not in available_types:
            field_errors['type'] = [f'{heading_type} is not available for {payroll_setting_type}']

        duration_unit = obj.get('duration_unit', None)

        # To convert blank to None
        hourly_heading_source = obj.get('hourly_heading_source') or None

        # START: Only accept not of type 'Type1Cnst'|'Type2Cnst' hourly heading names tracked by RHRS
        if duration_unit == 'Hourly' and heading_type in ['Addition', 'Deduction'] and not hourly_heading_source:
            field_errors['hourly_heading_source'] = ['This field is required if duration unit is set to Hourly.']
        elif not (duration_unit == 'Hourly' and heading_type in ['Addition', 'Deduction']):
            obj['hourly_heading_source'] = None
        # END: Only accept heading names tracked by RHRS

        # START: Daily heading validation
        deduct_amount_on_leave = obj.get('deduct_amount_on_leave', None)
        pay_when_present_holiday_offday = obj.get('pay_when_present_holiday_offday', None)
        deduct_amount_on_remote_work = obj.get('deduct_amount_on_remote_work', None)
        if duration_unit == 'Daily':
            if deduct_amount_on_leave is None:
                field_errors['deduct_amount_on_leave'] = ['This field is required for Daily heading.']
            if pay_when_present_holiday_offday is None:
                field_errors['pay_when_present_holiday_offday'] = ['This field is required for Daily heading.']
            if deduct_amount_on_remote_work is None:
                field_errors['deduct_amount_on_remote_work'] = ['This field is required for Daily heading.']
        else:
            obj['deduct_amount_on_leave'] = None
            obj['pay_when_present_holiday_offday'] = None
            obj['deduct_amount_on_remote_work'] = None
        # END: Daily heading validation

        if heading_type in none_mapping.keys():
            for key in conditional_null_fields:
                if key in none_mapping[heading_type]:
                    obj[key] = None
                else:
                    if obj.get(key) is None:
                        field_errors[key] = ['This field is required']

        else:
            for key in conditional_null_fields:
                if obj.get(key) is None:
                    field_errors[key] = ['This field is required']

        if self.instance and self.instance.is_used_package_heading:
            field_errors['non_field_errors'] = [
                'This package heading cannot be changed']

        if not field_errors.keys():
            kh_kwargs = obj
            kh_kwargs['type'] = obj.get('heading').type
            kh_kwargs['absent_days_impact'] = obj.get(
                'heading').absent_days_impact
            kh_kwargs['duration_unit'] = obj.get('heading').duration_unit
            kh_kwargs['hourly_heading_source'] = obj.get('heading').hourly_heading_source
            kh_kwargs['taxable'] = obj.get('heading').taxable
            kh_kwargs['benefit_type'] = obj.get('heading').benefit_type
            heading = PackageHeading(**kh_kwargs)
            is_valid, rule_validator = heading.rule_is_valid()
            if not is_valid:
                field_errors['rules'] = rule_validator.error_messages
            else:
                obj['dependencies'] = rule_validator.actual_dependent_headings

        if field_errors.keys():
            raise serializers.ValidationError(field_errors)

        return obj

    def create(self, validated_data):
        dependencies = validated_data.pop('dependencies')
        instance = None
        with transaction.atomic():
            try:
                PackageHeading.objects.get(
                    package=validated_data.get('package'),
                    order=validated_data.get('order')
                )
                PackageHeading.objects.filter(
                    order__gte=validated_data.get('order'),
                    package=validated_data.get('package'),
                ).update(
                    order=F('order') + 1
                )
                instance = super().create(validated_data)

            except PackageHeading.DoesNotExist:
                instance = super().create(validated_data)

            PackageHeadingDependency.objects.bulk_create(
                [
                    PackageHeadingDependency(source=instance, target=target)
                    for target in dependencies
                ]
            )
            makes_dependency = self.context.get('makes_dependency')
            if makes_dependency:
                PackageHeadingDependency.objects.bulk_create(
                    [
                        PackageHeadingDependency(source=source, target=instance)
                        for source in makes_dependency
                    ]
                )
            return instance

    def update(self, instance, validated_data):
        if not instance.is_editable:
            raise ValidationError('Cannot update rule when editable rule option is turned off')

        dependencies = validated_data.pop('dependencies')
        obj = None

        try:
            obj = PackageHeading.objects.get(
                package=validated_data.get('package'),
                order=validated_data.get('order')
            )
        except PackageHeading.DoesNotExist:
            pass
        if not obj or (obj and (obj.id == instance.id)):
            instance = super().update(instance, validated_data)
            PackageHeadingDependency.objects.filter(source=instance).delete()
            PackageHeadingDependency.objects.bulk_create(
                [
                    PackageHeadingDependency(source=instance, target=target)
                    for target in dependencies
                ]
            )
            return instance
        else:
            raise ValidationError(
                'Order with particular package already exists')

    class Meta:
        model = PackageHeading
        # exclude = ('order',)
        fields = (
            'id',
            'heading',
            'deduct_amount_on_leave',
            'pay_when_present_holiday_offday',
            'deduct_amount_on_remote_work',
            'hourly_heading_source',
            'package',
            'dependencies',
            'makes_dependency',
            'heading_name',
            'payroll_setting_type',
            'absent_days_impact',
            'type',
            'duration_unit',
            'taxable',
            'benefit_type',
            'order',
            'rules',
            'is_editable',
            'year_to_date'
        )


class BasicViewPackageSerializer(DynamicFieldsModelSerializer):
    heading_name = RelatedFieldStr(source='heading', read_only=True)
    is_condition_rule = serializers.SerializerMethodField()
    rule_variables = serializers.SerializerMethodField()
    functions = serializers.SerializerMethodField()

    class Meta:
        model = PackageHeading
        fields = (
            'id',
            'heading',
            'package',
            'heading_name',
            'absent_days_impact',
            'type',
            'duration_unit',
            'taxable',
            'benefit_type',
            'order',
            'rules',
            'is_editable',
            'is_condition_rule',
            'rule_variables',
            'functions'
        )

    @staticmethod
    def get_is_condition_rule(obj):
        rules = getattr(obj, 'rules', None)
        if not rules:
            return False
        json_rules = json.loads(rules)
        return True if len(json_rules) > 1 else False

    def get_rule_variables(self, obj):
        calculator_variable = CalculatorVariable(
            obj.package.organization.slug,
            order=obj.order,
            current_duration_unit=obj.duration_unit,
            current_heading_type=obj.type,
            package=obj.package.id
        )
        return list(
            calculator_variable.get_heading_scoped_variables()
        )

    @staticmethod
    def get_functions(obj):
        return CalculatorVariable.get_registered_methods()


class PackageListSerializer(InputChoiceSerializer,
                            serializers.ModelSerializer):
    label = serializers.ReadOnlyField(source='__str__')
    next_order = serializers.ReadOnlyField(source='get_next_heading_order')
    organization = serializers.SlugRelatedField(
        queryset=Organization.objects.all(),
        many=False,
        slug_field='slug'
    )

    class Meta:
        model = Package
        fields = '__all__'


class PackageSerializer(InputChoiceSerializer, serializers.ModelSerializer):
    label = serializers.ReadOnlyField(source='__str__')
    # designation_name = RelatedFieldStr(source='designation', read_only=True)
    package_headings = PackageHeadingSerializer(many=True, read_only=True)
    next_order = serializers.ReadOnlyField(source='get_next_heading_order')
    organization = serializers.SlugRelatedField(
        queryset=Organization.objects.all(),
        many=False,
        slug_field='slug'
    )

    def validate(self, obj):
        organization = obj.get('organization')
        package_name = obj.get('name')

        if Package.objects.filter(
            organization=organization, name=package_name
        ).exists():
            raise serializers.ValidationError({'package_name': [
                "Package with this name already  exists for this organization."]
            })

        if self.instance and self.instance.is_used_package:
            raise serializers.ValidationError('This package cannot be changed')

        return obj

    class Meta:
        model = Package
        fields = ('id', 'is_template', 'created_at', 'name',
                  'package_headings', 'next_order', 'organization')

    def create(self, validated_data):
        obj = super().create(validated_data)
        is_bulk = False
        request = self.context.get('request')
        if request:
            user = request.user
            title = f'{user.full_name} has {CREATED_PACKAGE} a package named "{obj.name}".'
            create_package_activity(title=title, package=obj, action=CREATED_PACKAGE)
        else:
            user = self.context.get('actor')
            title = f'{user.full_name} has {CLONED_PACKAGE} a package named "{obj.name}" by bulk package assign feature'
            if self.context.get('bulk'):
                create_package_activity(title=title, package=obj, action=CLONED_PACKAGE)

        return obj

    def update(self, instance, validated_data):
        old_package = instance
        user = self.context.get('request').user
        title = f'{user.full_name} has {UPDATED_PACKAGE} package name from "{old_package.name}" to "{validated_data.get("name")}"'
        create_package_activity(title=title, package=old_package, action=UPDATED_PACKAGE)
        return super().update(instance, validated_data)


class MinimalPackageDetailSerializer(PackageSerializer):
    class Meta(PackageSerializer.Meta):
        fields = (
            'id', 'created_at', 'name', 'next_order', 'organization'
        )


class UserExperiencePackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'


class UserExperiencePackageDetailSerializer(serializers.ModelSerializer):
    package = UserExperiencePackageSerializer(many=False)

    class Meta:
        model = UserExperiencePackageSlot
        fields = (
            'id',
            'user_experience',
            'package',
            'is_used_package',
            'backdated_calculation_generated',
            'backdated_calculation_from',
            'active_from_date'
        )


class UserExperiencePackageSlotCreateAndUpdateSerializer(
        serializers.ModelSerializer):
    active_from_date = serializers.DateField(required=False)


    class Meta:
        model = UserExperiencePackageSlot
        fields = '__all__'
        extra_kwargs = {'backdated_calculation_generated': {'read_only':True}}



    def get_latest_active_date(self,user_experience_latest_package,user_experience_packages):
        latest_active_date = user_experience_latest_package.active_from_date
        if self.instance:
            last_package = user_experience_packages.exclude(id=self.instance.id).last()
            if last_package:
                latest_active_date = last_package.active_from_date
        return latest_active_date

    def validate(self, obj):
        field_errors = dict()

        user_experience = obj.get('user_experience')
        from irhrs.payroll.utils.generate import (
            raise_validation_error_if_payroll_in_generated_or_processing_state
        )
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=user_experience.organization
        )
        active_from_date = obj.get('active_from_date')

        if user_experience:
            user_experience_start_date = user_experience.start_date
            if active_from_date<user_experience_start_date:
                raise serializers.ValidationError({
                    'active_from_date':f'Must be greater than {user_experience_start_date}'
                })

            last_paid = helpers.get_last_confirmed_payroll_generated_date(user_experience.user)
            last_payroll_generated = helpers.get_last_payroll_generated_date(user_experience.user)

            if last_paid and active_from_date < last_paid:
                raise serializers.ValidationError({
                    'active_from_date': _('This value can not be before last paid date'
                                            f' `{last_paid}`')
                })

            if last_payroll_generated and active_from_date < last_payroll_generated:
                raise serializers.ValidationError({
                    'active_from_date': f'This value can not be before last payroll generated date {last_payroll_generated}'
                })

        if self.instance and self.instance.is_used_package:
            raise serializers.ValidationError({
                'package': _(
                    'This package has been used to generate payroll so cannot be changed.'
                )
            })

        if self.instance and (
            self.instance.backdated_calculation_from and
            not self.instance.backdated_calculation_generated
        ):
            raise serializers.ValidationError({
                'package': _(
                    'The backdated calculation generation for this package is in progress.'
                    ' Please try again later.'
                )
            })

        user_experience_packages = user_experience.user_experience_packages.all(
        ).order_by(
            'active_from_date'
        )

        active_fiscal_year = FiscalYear.objects.active_for_date(
            organization=user_experience.organization,
            date_=active_from_date,
            category=GLOBAL
        )
        if not active_fiscal_year:
            raise serializers.ValidationError({
                "non_field_errors": ["Can not assign package. Fiscal year doesn't exist for given date."]
            })


        datework = FY(
            Organization.objects.get(slug=user_experience.organization.slug)
        )

        fiscal_years = datework.fiscal_objs()

        payroll_start_fiscal_year = OrganizationPayrollConfig.objects.filter(
            organization=user_experience.organization
        ).first()


        # TODO @wrufesh following first validation seems duplicate with local
        # symbol 'active_fiscal_year'
        if not fiscal_years:
            field_errors['non-field-errors'] = (
                'No fiscal years entry found'
            )
        elif not (payroll_start_fiscal_year and payroll_start_fiscal_year.start_fiscal_year):
            field_errors['non-field-errors'] = (
                'Please setup payroll start fiscal year first.'
            )
        else:
            first_fiscal_year_start_date = payroll_start_fiscal_year.start_fiscal_year.applicable_from
            # if data is for first package.(new or edit)
            if (not user_experience_packages) or (
                    len(user_experience_packages) == 1 and self.instance):
                if user_experience.end_date and (
                        user_experience.end_date < first_fiscal_year_start_date):
                    field_errors['active_from_date'] = (
                        'Cannot assign package to user experience before first fiscal year start date.'
                    )
                else:
                    if user_experience.start_date < first_fiscal_year_start_date:
                        obj['active_from_date'] = first_fiscal_year_start_date
                    else:
                        obj['active_from_date'] = user_experience.start_date
            else:
                user_experience_latest_package = user_experience_packages.last()

                if self.instance:
                    if self.instance != user_experience_latest_package:
                        field_errors['non-field-errors'] = (
                            'Only the last user experience package can be edited'
                        )

                    previous_package = user_experience_packages.exclude(id=self.instance.id).last()

                    if previous_package and previous_package.active_from_date >= active_from_date:
                        field_errors['active_from_date'] = f'{active_from_date} should be greater than active from date of previous packages.'

                if not self.instance or self.instance == user_experience_latest_package:

                    if active_from_date:
                        user_experience_latest_package_active_from_date = (
                            user_experience_latest_package.used_upto_date
                            or self.get_latest_active_date(
                                user_experience_latest_package,
                                user_experience_packages
                            )
                        )

                        if user_experience.end_date:
                            if not (
                                    (
                                        user_experience_latest_package_active_from_date
                                    ) < active_from_date < user_experience.end_date
                            ):
                                field_errors['active_from_date'] = (
                                    "Must be in between previous package start date and "
                                    "user experience end date"
                                )
                        else:
                            if not (
                                    user_experience_latest_package_active_from_date < active_from_date
                            ) and self.instance != user_experience_latest_package:
                                field_errors['active_from_date'] = (
                                    'Must be greater than previous package start date'
                                )

        backdated_calculation_from = obj.get('backdated_calculation_from')
        if backdated_calculation_from:
            if backdated_calculation_from >= active_from_date:
                field_errors['backdated_calculation_from'] = (
                    'Backdated calculation date should be smaller than package active from date.'
                )
            if backdated_calculation_from > get_today():
                field_errors['backdated_calculation_from'] = (
                    'Backdated calculation date cannot be a future date.'
                )
            latest_backdated_calculation_slots = UserExperiencePackageSlot.objects.filter(
                backdated_calculation_generated=True,
                user_experience__user=user_experience.user
            ).order_by('-active_from_date').all()
            latest_backdated_calculation_date = None
            for latest_backdated_calculation_slot in latest_backdated_calculation_slots:
                to_date_of_latest_backdated_date = latest_backdated_calculation_slot.active_from_date \
                    if latest_backdated_calculation_slot else None

                latest_backdated_date_payroll = Payroll.objects.none()
                if to_date_of_latest_backdated_date:
                    latest_backdated_date_payroll = Payroll.objects.filter(
                        employee_payrolls__employee=user_experience.user,
                        from_date__lte=to_date_of_latest_backdated_date,
                        to_date__gte=to_date_of_latest_backdated_date
                    ).first()

                if latest_backdated_date_payroll:
                    latest_backdated_date_payroll_to_date = latest_backdated_date_payroll.to_date
                    latest_backdated_calculation_date = latest_backdated_date_payroll
                    if backdated_calculation_from <= latest_backdated_date_payroll_to_date <= active_from_date:
                        field_errors['backdated_calculation_from'] = (
                                    f'Backdated calculation cannot overlap with previous backdated'
                                    f' calculation(i.e. {latest_backdated_date_payroll_to_date}).'
                                )
            backdate_cannot_be_before = max(
                payroll_start_fiscal_year.start_fiscal_year.start_at,
                user_experience.user.user_experiences.last().start_date
            )
            if latest_backdated_calculation_date:
                backdate_cannot_be_before = max(
                    payroll_start_fiscal_year.start_fiscal_year.start_at,
                    latest_backdated_calculation_date.to_date
                )
            if backdated_calculation_from < backdate_cannot_be_before:
                field_errors['backdated_calculation_from'] = (
                    'Backdated calculation date cannot be before employee joined date'
                    + '/ Payroll fiscal start date.'
                )
            last_paid = helpers.get_last_confirmed_payroll_generated_date(user_experience.user)
            if not last_paid:
                field_errors['backdated_calculation_from'] = (
                    f'No payroll is generated for this user yet for backdated calculations to be applicable.'
                )
            if last_paid and active_from_date != last_paid + timedelta(days=1):
                field_errors['active_from_date'] = (
                    f'This value must be equal to {last_paid + timedelta(days=1)}(last payroll generated day + 1 day) '
                    + 'if backdated calculation is present.'
                )

        if field_errors.keys():
            raise serializers.ValidationError(field_errors)
        return obj

    def create(self, validated_data):
        assigned_to = nested_getattr(validated_data.get('user_experience'), 'user')
        package = validated_data.get('package')
        user = self.context.get('request').user
        instance = super().create(validated_data)
        title = f'{user.full_name} has {ASSIGNED} a package named "{package.name}" to {assigned_to.full_name}.'
        create_package_activity(title=title, package=package, action=ASSIGNED,
                                assigned_to=assigned_to)
        return instance
    def update(self, instance, validated_data):
        assigned_to = nested_getattr(instance, 'user_experience.user')
        old_package = instance.package
        user = self.context.get('request').user
        instance = super().update(instance, validated_data)

        # get backdated_calculation_generated flag set from signal
        instance.refresh_from_db()
        title = f'{user.full_name} has {UPDATED_PACKAGE} {assigned_to.full_name}`s package from "{old_package.name}" to "{instance.package.name}"'
        create_package_activity(title=title, package=old_package, action=UPDATED_PACKAGE,
                                assigned_to=assigned_to)

        return instance

class UserExperiencePackageSlotBulkCreateSerializer(serializers.Serializer):
    users = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        many=True
    )
    package = serializers.PrimaryKeyRelatedField(
        queryset=Package.objects.all()
    )

    from_date = serializers.DateField()

    def get_user_experience(self, included_date, user):
        return UserExperience.objects.filter(
            user=user,
            start_date__gte=included_date
        ).filter(
            Q(
                Q(end_date__isnull=True) | Q(end_date__lte=included_date)
            )
        ).first()

    def validate(self, obj):
        field_errors = dict()
        field_errors['users'] = {}
        users = obj.get('users')
        package = obj.get('package')
        from_date = obj.get('from_date')
        validated_user_experience_package_serializers = {}
        for user in users:
            user_experience = self.get_user_experience(from_date, user)

            ser = UserExperiencePackageSlotCreateAndUpdateSerializer(
                data={
                    'user_experience': user_experience.id if user_experience else None,
                    'package': package.id,
                    'active_from_date': from_date
                }
            )
            if ser.is_valid():
                validated_user_experience_package_serializers[user.id] = ser
            else:
                field_errors['users'][user.id] = ser.errors
        # if field_errors['users']:
        #     raise serializers.ValidationError(field_errors)
        return validated_user_experience_package_serializers, field_errors

    def create(self, validated_objs):
        validated_user_serializers, fields_errors = validated_objs
        created_datas = {}
        for user_id in validated_user_serializers.keys():
            validated_user_serializers[user_id].save()
            created_datas[user_id] = validated_user_serializers[user_id].data
        return {
            'errors': fields_errors,
            'created': created_datas
        }


class SalaryHoldingSerializer(DynamicFieldsModelSerializer):
    def validate_employee(self, employee):
        if employee.detail.organization != self.context.get("organization"):
            raise serializers.ValidationError("Employee must be of same organization")

        if employee.salary_holdings.filter(released=False).exists():
            raise serializers.ValidationError("Employee's salary is already on hold")
        return employee

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields["employee"] = EmployeeThinSerializer(exclude_fields=['legal_info'])
        return fields

    class Meta:
        model = SalaryHolding
        fields = ['id', 'employee', "hold_remarks", "release_remarks", "from_date", "to_date", "released"]
        read_only_fields = ["id", "from_date", "to_date", "released", "release_remarks"]


class SalaryHoldingReleaseSerializer(DynamicFieldsModelSerializer):
    release_remarks = serializers.CharField(max_length=255, allow_blank=False, required=True)

    class Meta:
        model = SalaryHolding
        fields = ["release_remarks"]


class EmployeeSerializer(InputChoiceSerializer, serializers.ModelSerializer):
    label = serializers.ReadOnlyField(source='__str__')

    class Meta:
        model = Employee
        fields = '__all__'


class PayrollSerializer(DynamicFieldsModelSerializer):
    approval_pending = UserThumbnailSerializer(read_only=True)
    approval_required = SerializerMethodField()

    class Meta:
        model = Payroll
        fields = (
            'id',
            'title',
            'from_date',
            'to_date',
            'timestamp',
            'status',
            'approval_pending',
            'extra_data',
            'approval_required'
        )
        read_only_fields = ('id', 'title', 'from_date', 'to_date', 'timestamp', 'extra_data', 'user_note')

    @staticmethod
    def get_approval_required(instance):
        # Also Used in SignedPayrollHistorySerializer.
        return instance.organization.payroll_approval_settings.exists()

    def validate_status(self, status):
        if status not in [APPROVAL_PENDING, CONFIRMED]:
            raise serializers.ValidationError(
                _(f"Status can be on of {APPROVAL_PENDING}, {CONFIRMED}")
            )
        if self.instance:
            old_status = self.instance.status
            if status == APPROVAL_PENDING and old_status not in [GENERATED, REJECTED]:
                raise serializers.ValidationError(
                    _(f"Approval process can be started only from {GENERATED} or {REJECTED} status.")
                )
            elif status == CONFIRMED:
                if self.get_approval_required(self.instance):
                    if old_status != APPROVED:
                        raise serializers.ValidationError(
                            _(f"Can only be confirmed from {APPROVED} status.")
                        )

                # [HRIS-2544]
                # approved added separately because approval level can be deleted during
                # the approval process so if payroll is in approved stage above if may fail
                # and needed to catch here
                elif old_status not in [GENERATED, APPROVED]:
                    raise serializers.ValidationError(
                        _(f"Can only be confirmed from {GENERATED} or {APPROVED} status.")
                    )

        return status

    def create_approvals(self, instance):
        if instance.payroll_approvals.exists():
            # if old approvals found just
            instance.payroll_approvals.update(status=PENDING)
            instance.approval_pending = instance.payroll_approvals.order_by(
                'approval_level'
            ).first().user

        else:
            payroll_approval_settings = list(
                instance.organization.payroll_approval_settings.order_by(
                    'approval_level'
                ).values_list('user_id', 'approval_level')
            )
            if not payroll_approval_settings:
                raise serializers.ValidationError(
                    {"non_field_errors": _("Approval settings not found")}
                )
            approval_levels = [
                PayrollApproval(
                    user_id=user_id,
                    payroll=instance,
                    approval_level=approval_level
                )
                for user_id, approval_level in payroll_approval_settings
            ]
            PayrollApproval.objects.bulk_create(approval_levels)
            instance.approval_pending_id = payroll_approval_settings[0][0]

        PayrollApprovalHistory.objects.create(
            actor=self.request.user,
            action="started approval process",
            payroll=instance
        )
        instance.save()
        instance.refresh_from_db()
        recipient = instance.approval_pending
        sender = self.request.user
        add_notification(
            text=f"{sender} forwarded a payroll to approve.",
            actor=sender,
            action=instance,
            url=f'/user/payroll/approval/request',
            recipient=instance.approval_pending
        )
        if recipient:
            send_email_as_per_settings(
                recipients=recipient,
                subject=f"{sender} forwarded a payroll for approval.",
                email_text=f"{sender} forwarded a payroll from {instance.from_date} to {instance.to_date} for approval.",
                email_type=PAYROLL_APPROVAL_NEEDED_EMAIL
            )

    @atomic()
    def update(self, instance, validated_data):
        user = self.request.user
        if validated_data.get('status') == CONFIRMED:
            validated_data['approved_date'] = timezone.now()
            validated_data['approved_by'] = user

            EmployeePayroll.objects.filter(
                payroll=instance
            ).update(acknowledgement_status="Pending")

            for repayment in AdvanceSalaryRepayment.objects.filter(
                payroll_reference__payroll=instance
            ):
                repayment.paid = True
                repayment.paid_on = get_today()
                repayment.payment_type = SALARY_DEDUCTION
                repayment.remarks = "Settled via payroll."
                repayment.save()

            PayrollApprovalHistory.objects.create(
                actor=user,
                action="confirmed payroll",
                payroll=instance
            )
            recipient = Employee.objects.filter(
                employee_payrolls__payroll=instance
            )
            starting_date = instance.from_date
            ending_date = instance.to_date
            add_notification(
                text=f"Payslip for {starting_date} to {ending_date} has been generated.",
                recipient=recipient,
                actor=user,
                action=instance,
                url='/user/payroll/payslip',
            )

            for _recipient in recipient:
                email_text = f"Dear {_recipient.first_name}, " \
                            f"Payslip from {starting_date} to "\
                            f"{ending_date} has been generated."

                send_email_as_per_settings(
                    recipients=_recipient,
                    subject="Payslip has been generated.",
                    email_text=email_text,
                    email_type=PAYROLL_CONFIRMATION_BY_HR
                )
        elif validated_data.get('status') == APPROVAL_PENDING:
            self.create_approvals(instance)
        return super().update(instance, validated_data)


class SignedPayrollHistorySerializer(DynamicFieldsModelSerializer):

    def validate(self, attrs):
        payroll = self.context.get('payroll')

        has_approval_levels = PayrollSerializer.get_approval_required(payroll)

        if has_approval_levels and payroll.status not in [APPROVED, CONFIRMED]:
            raise serializers.ValidationError(
                _("Payroll should be approved/confirmed in case of presence of approval level.")
            )

        attrs['payroll'] = payroll
        return super().validate(attrs)

    class Meta:
        model = SignedPayrollHistory
        fields = ['attachment', 'is_latest', 'created_at']
        read_only_fields = ('is_latest', 'created_at')


class ReportRowRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportRowRecord
        fields = '__all__'


class UserExperienceWithResultAreaSerializer(UserExperienceSerializer):
    user_experience_packages = serializers.SerializerMethodField()

    class Meta(UserExperienceSerializer.Meta):
        fields = UserExperienceSerializer.Meta.fields + \
            ('user_experience_packages',)

    def get_user_experience_packages(self, instance):
        # UserExperiencePackageDetailSerializer
        user_experience_packages = instance.user_experience_packages.all()\
            .order_by('active_from_date')
        serializer = UserExperiencePackageDetailSerializer(
            user_experience_packages,
            many=True
        )
        return serializer.data


class UserPackageListSerializer(UserThickSerializer):
    experiences = serializers.SerializerMethodField()

    class Meta(UserThickSerializer.Meta):
        model = Employee
        fields = UserThickSerializer.Meta.fields + ['experiences']

    def get_experiences(self, instance):
        ctx = {'request': self.context['request']}
        return UserExperienceWithResultAreaSerializer(
            instance.user_experiences.all(),
            fields=['id', 'job_title', 'organization',
                    'user_experience_packages', 'result_areas',
                    'is_current', 'start_date', 'end_date'
                    ],
            context=ctx,
            many=True).data


class EmployeePayrollListSerializer(serializers.ModelSerializer):
    from_date = serializers.ReadOnlyField(source='payroll.from_date')
    to_date = serializers.ReadOnlyField(source='payroll.to_date')

    total_comment = serializers.ReadOnlyField(allow_null=True)

    class Meta:
        model = EmployeePayroll
        fields = ('id', 'employee', 'payroll', 'user_note', 'total_comment',
                  'from_date', 'to_date', 'acknowledgement_status')


class EmployeePayrollSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployeePayroll
        fields = ('id', 'acknowledgement_status')


class EmployeePayrollCommentSerializer(DynamicFieldsModelSerializer):
    commented_by = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    def create(self, validated_data):
        validated_data['employee_payroll'] = self.context.get('employee_payroll')
        instance = super().create(validated_data)
        self.send_notification(instance)
        return instance

    def send_notification(self, employee_payroll_comment):
        commented_by_self = employee_payroll_comment.commented_by == (
            employee_payroll_comment.employee_payroll.employee
        )

        if commented_by_self:
            notification_text = f"{employee_payroll_comment.commented_by.full_name} commented on " \
                                f"payslip of payroll " \
                                f"({employee_payroll_comment.employee_payroll.payroll.from_date} - {employee_payroll_comment.employee_payroll.payroll.to_date})"
            notify_organization(
                text=notification_text,
                url=f"/admin/{self.context.get('organization').slug}/payroll/response",
                actor=self.request.user,
                action=employee_payroll_comment,
                organization=employee_payroll_comment.employee_payroll.payroll.organization,
                permissions=[
                    GENERATE_PAYROLL_PERMISSION,
                    PAYROLL_REPORT_PERMISSION
                ]
            )

        else:
            notification_text = f"{employee_payroll_comment.commented_by.full_name} commented on " \
                                f"payslip of {employee_payroll_comment.employee_payroll.employee} payroll " \
                                f"({employee_payroll_comment.employee_payroll.payroll.from_date} - {employee_payroll_comment.employee_payroll.payroll.to_date})"

            add_notification(
                text=notification_text,
                url="/user/payroll/payslip",
                recipient=employee_payroll_comment.employee_payroll.employee,
                action=employee_payroll_comment
            )

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method == 'GET':
            if 'commented_by' in fields:
                fields['commented_by'] = UserThinSerializer()
        return fields

    class Meta:
        model = EmployeePayrollComment
        fields = '__all__'
        read_only_fields = ('employee_payroll', )


class EmployeeLegalInformation(DynamicFieldsModelSerializer):
    class Meta:
        model = UserLegalInfo
        fields = '__all__'


class EmployeeBank(DynamicFieldsModelSerializer):
    bank_name = SerializerMethodField()

    class Meta:
        model = UserBank
        fields = ('account_number', 'branch', 'bank_name')

    def get_bank_name(self, instance):
        return getattr(instance.bank, "name")


class EmployeeThinSerializer(DynamicFieldsModelSerializer):
    """
    A thin Serializer for User that displays username, and their display picture

    Currently Used in:
        > Model MessageToUser in field message_from
        > Model Organization in fields (organization_head, Organization_Admin,)
        > LikeSerializer
        > MessageToUser Serializer
        > Task Serializer
    """
    code = ReadOnlyField(source='detail.code')
    profile_picture = ReadOnlyField(
        source='profile_picture_thumb', allow_null=True
    )
    cover_picture = ReadOnlyField(
        source='cover_picture_thumb', allow_null=True
    )

    division = OrganizationDivisionSerializer(source='detail.division',
                                              fields=['name',
                                                      'slug'])
    joined_date = ReadOnlyField(source='detail.joined_date')
    job_title = SerializerMethodField()
    branch = SerializerMethodField()
    employee_level = SerializerMethodField()
    employee_level_hierarchy = SerializerMethodField()
    organization = OrganizationSerializer(
        source='detail.organization', fields=['name', 'abbreviation', 'slug', 'appearance'])
    legal_info = EmployeeLegalInformation()
    userbank = EmployeeBank()
    username = ReadOnlyField()
    marital_status = ReadOnlyField(source='detail.marital_status')

    class Meta:
        model = Employee
        fields = [
            'id',
            'code',
            'full_name',
            'profile_picture',
            'cover_picture',
            'division',
            'branch',
            'job_title',
            'email',
            'employee_level',
            'employee_level_hierarchy',
            'organization',
            'is_online',
            'last_online',
            'legal_info',
            'joined_date',
            'userbank',
            'username',
            'marital_status'
        ]
        read_only_fields = ('is_online', 'last_online',)

    def get_job_title(self, instance):
        detail = instance.detail
        return detail.job_title.title \
            if detail and detail.job_title else 'N/A'

    def get_employee_level(self, instance):
        detail = instance.detail
        return (
            detail.employment_level.title
            if detail and detail.employment_level
            else 'N/A'
        )

    @staticmethod
    def get_employee_level_hierarchy(instance):
        return nested_getattr(instance, 'detail.employment_level.order_field', default='N/A')

    def get_branch(self, instance):
        return nested_getattr(instance, 'detail.branch.name', default='N/A')

    def get_org(self, instance):
        detail = instance.detail
        return (
            detail.organization.abbreviation
            if detail and detail.organization
            else 'N/A'
        )


class ReportSalaryBreakDownRangeConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSalaryBreakDownRangeConfig
        fields = ('from_amount', 'to_amount')

    def validate(self, obj):
        from_amount = obj.get('from_amount')
        to_amount = obj.get('to_amount')
        validation_dict = dict()
        if from_amount > to_amount:
            validation_dict[
                'from_amount'] = 'Start amount should be less than end amount.'

        if validation_dict.keys():
            raise serializers.ValidationError(validation_dict)
        return obj


class OrganizationOverviewConfigSerializer(serializers.ModelSerializer):
    organization = serializers.ReadOnlyField(
        source='organization.slug'
    )

    salary_breakdown_ranges = ReportSalaryBreakDownRangeConfigSerializer(
        many=True,
        default=list(),
    )

    class Meta:
        model = OverviewConfig
        fields = '__all__'
        lookup_field = 'organization__slug'
        extra_kwargs = {
            'url': {'lookup_field': 'organization__slug'}
        }

    def update(self, instance, validated_data):
        salary_breakdown_ranges = validated_data.get('salary_breakdown_ranges')
        info = model_meta.get_field_info(instance)
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                field = getattr(instance, attr)
                if attr == 'salary_breakdown_ranges':
                    field.all().delete()
                else:
                    field.set(value)
            else:
                setattr(instance, attr, value)
        instance.save()

        if salary_breakdown_ranges:
            ReportSalaryBreakDownRangeConfig.objects.bulk_create(
                [
                    ReportSalaryBreakDownRangeConfig(
                        overview_config=instance,
                        from_amount=salary_breakdown_range.get('from_amount'),
                        to_amount=salary_breakdown_range.get('to_amount'),
                    ) for salary_breakdown_range in salary_breakdown_ranges
                ]
            )
        return instance


class OrganizationPayrollConfigUpdateSerializer(serializers.ModelSerializer):
    organization = serializers.ReadOnlyField(
        source='organization.slug'
    )
    can_edit_fiscal_year = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrganizationPayrollConfig
        fields = ('organization', 'start_fiscal_year', 'include_holiday_offday_in_calculation',
                  'enable_unit_of_work', 'can_edit_fiscal_year', 'payslip_template',
                  'display_heading_with_zero_value',
                  'payslip_note', 'show_generated_payslip')

    @staticmethod
    def is_organization_payroll_generated(organization):
        return ReportRowRecord.objects.filter(
            employee_payroll__payroll__organization=organization
        ).exists()

    def get_can_edit_fiscal_year(self, instance):
        return not self.is_organization_payroll_generated(instance.organization)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method.lower() == 'get':
            fields['start_fiscal_year'] = FiscalYearSerializer(
                fields=['id', 'name', 'slug']
            )
        return fields

    def validate(self, obj):
        validation_dict = dict()

        if ('start_fiscal_year' in obj) and self.is_organization_payroll_generated(
            # Confirmed that the instance is accessible as it is used for
            # update only
            self.instance.organization
        ):
            validation_dict['start_fiscal_year'] = (
                'Cannot change this field as it is used to generate payroll.'
            )

        if validation_dict.keys():
            raise serializers.ValidationError(validation_dict)

        return obj

    def validate_start_fiscal_year(self, fiscal_year):
        if self.instance and fiscal_year.organization != self.instance.organization:
            raise serializers.ValidationError(_('Fiscal year is from different organization.'))
        return fiscal_year


class ExternalTaxDiscountSerializer(DynamicFieldsModelSerializer):
    created_by = EmployeeThinSerializer(read_only=True)
    modified_by = EmployeeThinSerializer(read_only=True)

    class Meta:
        model = ExternalTaxDiscount
        fields = "__all__"
        read_only_fields = ["id", "created_by", "modified_by", "created_at", "modified_at"]

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields["fiscal_year"] = FiscalYearSerializer(fields=["id", "name", "start_at", "end_at"])
            fields["employee"] = EmployeeThinSerializer()
        return fields

    def validate_employee(self, attr):
        if not self.context.get('organization') == attr.detail.organization:
            raise serializers.ValidationError("User must be of same organization.")
        return attr

    def validate_fiscal_year(self, attr):
        if not self.context.get('organization') == attr.organization:
            raise serializers.ValidationError("Fiscal Year must be of same organization.")
        return attr


class PayrollEditHistoryAmountSerializer(DynamicFieldsModelSerializer):
    package = ReadOnlyField(source='heading.name')

    class Meta:
        model = PayrollEditHistoryAmount
        fields = (
            'old_amount', 'new_amount', 'package'
        )


class EmployeePayrollHistorySerializer(DynamicFieldsModelSerializer):
    edited_packages = SerializerMethodField('get_packages')
    created_by = UserThinSerializer(
        fields=('id', 'full_name', 'profile_picture', 'is_online', 'organization', 'is_current', 'job_title')
    )

    class Meta:
        model = EmployeePayrollHistory
        fields = (
            'edited_packages', 'created_at', 'created_by', 'remarks'
        )

    @staticmethod
    def get_packages(instance):
        return PayrollEditHistoryAmountSerializer(
            instance._amounts,
            many=True
        ).data


class PayrollNoteSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = EmployeePayroll
        fields = ['user_note']


class SwitchPackageHeadingOrderSerializer(serializers.Serializer):
    from_obj_order = serializers.IntegerField(min_value=0)
    to_obj_order = serializers.IntegerField(min_value=0)

    def get_fields(self):
        fields = super().get_fields()
        organization_slug = self.context.get(
            'request'
        ).query_params.get('package__organization__slug')
        fields['package_id'] = serializers.PrimaryKeyRelatedField(
            queryset=Package.objects.filter(organization__slug=organization_slug),
        )
        return fields
