import itertools

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, OuterRef, Subquery, Max
from django.db.transaction import atomic
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.utils.common import DummyObject
from irhrs.organization.models import Organization
from irhrs.payroll.api.v1.serializers.payroll_serializer import (
    PackageHeadingSerializer,
    UserExperiencePackageSlotCreateAndUpdateSerializer
)
from irhrs.payroll.models import (
    Heading,
    Package,
    DURATION_UNITS,
    HEADING_TYPES,
    PackageHeading,
    PackageHeadingDependency,
    UserExperiencePackageSlot
)
from irhrs.payroll.utils.generate import \
    validate_if_package_heading_updated_after_payroll_generated_previously
from irhrs.payroll.utils.headings import get_all_heading_dependencies
from irhrs.payroll.utils.package_clone import clone_package_from_another_package
from irhrs.payroll.utils.rule_validator import HeadingRuleValidator
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

User = get_user_model()


class HeadingSwitchSerializer(DummySerializer):
    from_obj_order = serializers.IntegerField()
    to_obj_order = serializers.IntegerField()
    organization__slug = serializers.SlugRelatedField(
        queryset=Organization.objects.all(),
        slug_field='slug'
    )

    def validate(self, attrs):
        from_obj_order = attrs.get('from_obj_order')
        to_obj_order = attrs.get('to_obj_order')
        organization = attrs.get('organization__slug')

        if not Heading.objects.filter(order=from_obj_order, organization=organization).exists():
            raise serializers.ValidationError({
                "from_obj_order": ["Heading with this order does not exist."]
            })

        if not Heading.objects.filter(order=to_obj_order, organization=organization).exists():
            raise serializers.ValidationError({
                "to_obj_order": ["Heading with this order does not exist."]
            })

        return attrs


class HeadingGetVariablesSerializer(DummySerializer):
    # CONDITIONAL_CHOICES = (
    #     ('True', 'True'),
    #     ('False', 'False')
    # )
    # is_conditional = serializers.ChoiceField(CONDITIONAL_CHOICES, default='True')

    order = serializers.IntegerField()
    current_duration_unit = serializers.ChoiceField(
        choices=DURATION_UNITS,
        required=False,
        allow_null=True
    )
    current_heading_type = serializers.ChoiceField(
        choices=HEADING_TYPES,
        required=False,
        allow_null=True
    )
    organization__slug = serializers.SlugRelatedField(
        queryset=Organization.objects.all(),
        slug_field='slug'
    )


class PackageHeadingGetVariablesSerializer(DummySerializer):
    # CONDITIONAL_CHOICES = (
    #     ('True', 'True'),
    #     ('False', 'False')
    # )
    # is_conditional = serializers.ChoiceField(CONDITIONAL_CHOICES, default='True')
    order = serializers.IntegerField()
    current_duration_unit = serializers.ChoiceField(
        choices=DURATION_UNITS,
        required=False,
        allow_null=True
    )
    current_heading_type = serializers.ChoiceField(
        choices=HEADING_TYPES,
        required=False,
        allow_null=True
    )
    package_id = serializers.PrimaryKeyRelatedField(
        queryset=Package.objects.all()
    )


class DragHeadingSerializer(DummySerializer):
    to_obj_order = serializers.IntegerField(
        min_value=0, max_value=32767, write_only=True)
    package_id = serializers.PrimaryKeyRelatedField(
        queryset=Package.objects.all(),
        write_only=True
    )
    heading_id = serializers.PrimaryKeyRelatedField(
        queryset=Heading.objects.all(),
        write_only=True
    )
    success = serializers.ReadOnlyField()
    new_orders = serializers.ReadOnlyField()

    def validate_package_id(self, package):
        if package.organization != self.context.get('organization'):
            raise serializers.ValidationError(
                "Package not found for this organization.")
        return package

    def validate_heading_id(self, heading):
        if heading.organization != self.context.get('organization'):
            raise serializers.ValidationError(
                "heading not found for this organization")
        return heading

    def get_new_package_heading(self, heading, package, to_obj_order):
        package_id = package.id
        heading_id = heading.id

        new_package_heading = PackageHeading(
            package_id=package_id,
            heading_id=heading_id,
            hourly_heading_source=heading.hourly_heading_source,
            order=to_obj_order,
            absent_days_impact=heading.absent_days_impact,
            type=heading.type,
            duration_unit=heading.duration_unit,
            taxable=heading.taxable,
            benefit_type=heading.benefit_type,
            rules=heading.rules
        )
        return new_package_heading

    def validate(self, attrs, auto_resolve=None):
        heading = attrs.get('heading_id')
        package = attrs.get('package_id')
        to_obj_order = attrs.get('to_obj_order')
        validate_if_package_heading_updated_after_payroll_generated_previously(package)

        if PackageHeading.objects.filter(heading=heading, package=package).exists():
            raise serializers.ValidationError(
                "Heading already exists in package.")

        if auto_resolve is None:
            attrs["auto_resolve"] = self.context.get("auto_resolve")
        else:
            attrs["auto_resolve"] = auto_resolve

        new_package_heading = self.get_new_package_heading(
            heading, package, to_obj_order)
        if not attrs.get('auto_resolve', False):
            is_valid, rule_validator = new_package_heading.rule_is_valid()

            if not is_valid:
                raise serializers.ValidationError(
                    {
                        'success': False,
                        'errors': rule_validator.error_messages,
                        'auto_resolve': True
                    }
                )
            attrs["new_package_heading"] = new_package_heading
            attrs["actual_dependent_headings"] = rule_validator.actual_dependent_headings
        else:
            # tax deduction order check missing if auto resolve is True
            validator = HeadingRuleValidator(heading=new_package_heading)
            error_msg, is_valid = validator.validate_tax_deduction_order(
                new_package_heading,
                latest_tax_deduction_heading_order=getattr(
                    validator.get_latest_tax_deduction(), 'order', None),
                oldest_taxable_addition_order=getattr(
                    validator.get_oldest_taxable_addition(), 'order', None),
                oldest_non_taxable_deduction_order=getattr(
                    validator.get_oldest_non_taxable_deduction(), 'order', None),
            )
            if not is_valid:
                raise serializers.ValidationError(error_msg)

        # if auto resolve is true, serializer will try to resolve on create
        return attrs

    def create(self, validated_data):

        package = validated_data.get('package_id')
        package_id = package.id
        to_obj_order = validated_data.get('to_obj_order')

        if validated_data.get('auto_resolve', False):
            # if auto_resolve is True, try auto resolve dependencies
            heading = validated_data.get('heading_id')
            return self.auto_resolve_dependencies(heading, package, to_obj_order)

        actual_dependent_headings = validated_data.get(
            'actual_dependent_headings')

        new_package_heading = validated_data.get("new_package_heading")

        with atomic():
            PackageHeading.objects.filter(
                package_id=package_id,
                order__gte=to_obj_order,
            ).update(
                order=F('order') + 1
            )
            new_package_heading.save()

            new_orders = PackageHeading.objects.filter(
                package_id=package_id
            ).order_by('order').values_list('order', flat=True)

            PackageHeadingDependency.objects.bulk_create(
                [
                    PackageHeadingDependency(
                        source=new_package_heading, target=target)
                    for target in actual_dependent_headings
                ]
            )

        return DummyObject(**{
            'success': True,
            'new_orders': new_orders
        })

    def auto_resolve_dependencies(self, heading, package, to_obj_order):
        dependencies = sorted(get_all_heading_dependencies(
            heading, package), key=lambda h: h.order)
        success_obj = None

        try:
            with atomic():
                for individual_heading in itertools.chain(dependencies, [heading]):
                    data = {
                        "heading_id": individual_heading,
                        "package_id": package,
                        "to_obj_order": to_obj_order,
                    }
                    attrs = self.validate(data, auto_resolve=False)
                    success_obj = self.create(attrs)
                    to_obj_order += 1
            return success_obj

        except serializers.ValidationError:
            raise serializers.ValidationError({
                'success': False,
                'auto_resolve': False,
                'message': 'Could not resolve dependencies automatically.'
            })


class UpdatePackageHeadingInputSerializer(serializers.Serializer):
    '''Takes the data from UI interface for assigning a heading to the
    latest package of the selected users and applying it from the date
    given.

    Attrs:
        users (serializer.PrimaryKeyRelatedField) : Holds the users for him
            new package is to be made and applied.

        filter_params (serializer.JSONField) : Holds the filclone_package_from_another_packageter params when
            the filterd users exceeds the pagination size and 'select all'
            has beed selected.

            When filter_params is present, the users for whom the new packages
            are to be generated are obtained by applying filter using `filter_params`
            to organization users.

        active_from_date (serializer.DateField) : Holds the date from which the
            new package generated is applied for selected users.

        backdated_calculation_from (serializer.DateField): Holds the date from
            which new package generated and applied needs a backdated calculation.

    Todo:
        Get users from filter params when filter_param is present. And continue
    '''

    filter_params = serializers.JSONField(required=False)

    active_from_date = serializers.DateField(
        required=True
    )

    backdated_calculation_from = serializers.DateField(
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.to_be_deleted_cloned_packages = list()

        self.to_be_saved_serializers = list()

        self.to_be_created_user_experience_package_slots = list()

        self.bulk_apply_errors = dict()
        self.active_from_date = ""

    def get_users_queryset(self, input):
        '''This method returns the selected users queryset

        Returns:
            queryset: users queryset to whom package update is
                to be applied
        '''
        filter_params = input.get('filter_params')

        users = input.get('users')

        user_queryset = self.fields['users'].child_relation.queryset

        if filter_params:
            try:
                return user_queryset.filter(**filter_params)
            except:
                raise ValidationError("Invalid filter parameters.")

        return user_queryset.filter(
            id__in=[user.id for user in users]
        )

    def validate(self, validated_input):

        active_from_date = validated_input.get('active_from_date')
        self.active_from_date = active_from_date

        validated_users = validated_input.get('users')
        # if user list is empty update users list with all users within organization
        if not validated_users:
            users = User.objects.filter(
                detail__organization=self.context.get('organization')
            ).current()
            if not users:
                raise ValidationError(
                    "No users found in the organization."
                )
            validated_input.update({
                "users": users
            })

        filter_params = validated_input.get('filter_params')

        if validated_users and filter_params:
            raise ValidationError(
                dict(
                    non_field_errors=f"Both users and filter_params are not valid at same time."
                )
            )

        users_queryset = self.get_users_queryset(validated_input)

        latest_user_experience_package_slot = UserExperiencePackageSlot.objects.filter(
            user_experience__user_id=OuterRef('pk'),
            active_from_date__lte=active_from_date
        ).order_by('-active_from_date')

        users = users_queryset.annotate(
            latest_user_experience_package_slot_id=Subquery(
                latest_user_experience_package_slot.values('id')[:1]
            )
        )

        self.apply_to_users(users)

        self.validate_user_experience_package_slot_creation(validated_input)

        if self.bulk_apply_errors.keys():
            for new_cloned_package in self.to_be_deleted_cloned_packages:
                new_cloned_package.delete()

            raise serializers.ValidationError(
                dict(
                    non_eligible_employee=self.bulk_apply_errors
                )
            )

        return validated_input

    def get_package_and_user_experience_to_be_applied(self, latest_user_experience_package_slot_id):

        user_experience_package_slot = UserExperiencePackageSlot.objects.get(
            id=latest_user_experience_package_slot_id
        )

        user_experience = user_experience_package_slot.user_experience

        current_package = user_experience_package_slot.package

        # clone new package even if package is not used.
        try:
            with transaction.atomic():
                request = self.context.get('request')
                user = request.user if request else None
                current_package = clone_package_from_another_package(
                    current_package,
                    f'{user_experience.user.full_name} '
                    f'{self.active_from_date.strftime("%Y-%m-%d")}',
                    actor=user
                )
            self.to_be_deleted_cloned_packages.append(current_package)
        except ValidationError:
            # if current package cannot be cloned, simply pass and use previous package
            pass

        return current_package, user_experience

    def apply_heading_to_package(self, user, heading, package, user_experience):

        new_order = PackageHeading.objects.filter(
            package=package,
            heading__in=heading.dependencies.all()
        ).aggregate(Max('order')).get('order__max', 0) or 0

        data = dict(
                heading=heading.id,
                deduct_amount_on_leave=heading.deduct_amount_on_leave,
                pay_when_present_holiday_offday=heading.pay_when_present_holiday_offday,
                deduct_amount_on_remote_work=heading.deduct_amount_on_remote_work,
                hourly_heading_source=heading.hourly_heading_source,
                package=package.id,
                payroll_setting_type=heading.payroll_setting_type,
                absent_days_impact=heading.absent_days_impact,
                type=heading.type,
                duration_unit=heading.duration_unit,
                taxable=heading.taxable,
                benefit_type=heading.benefit_type,
                order=new_order+1,
                rules=heading.rules,
                is_editable=heading.is_editable
            )
        package_heading_instance = PackageHeading.objects.filter(
            heading=heading.id,
            package=package.id
        ).first()

        if package_heading_instance:
            if package_heading_instance.order == new_order:
                data['order'] = new_order
                serializer = PackageHeadingSerializer(
                    package_heading_instance,
                    data=data,
                    partial=True
                )
            else:
                makes_dependency = list(package_heading_instance.makes_dependency.all())
                package_heading_instance.delete()
                serializer = PackageHeadingSerializer(
                    data=data,
                    context={
                        "makes_dependency": makes_dependency
                    }
                )

        else:
            serializer = PackageHeadingSerializer(
                data=data
            )
        if not serializer.is_valid():
            self.set_user_error(
                user,
                serializer.errors
            )

        else:
            self.to_be_created_user_experience_package_slots.append(
                dict(
                    user=user,
                    package=package,
                    user_experience=user_experience
                )
            )

            self.to_be_saved_serializers.append(serializer)

    def apply_to_user(self, user):

        heading = self.instance

        if not user.latest_user_experience_package_slot_id:

            self.set_user_error(
                user,
                'User has no user experience package slot to mutate its package.'
            )

            return

        package, user_experience = self.get_package_and_user_experience_to_be_applied(
            user.latest_user_experience_package_slot_id
        )

        self.apply_heading_to_package(user, heading, package, user_experience)

    def apply_to_users(self, users):
        for user in users:
            self.apply_to_user(user)

    def get_fields(self):
        fields = super().get_fields()

        organization_slug = self.context['request'].query_params.get(
            'organization__slug'
        )

        fields['users'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.filter(
                detail__organization__slug=organization_slug
            ),
            many=True,
            required=False
        )

        return fields

    def validate_user_experience_package_slot_creation(self, validated_data):

        for item in self.to_be_created_user_experience_package_slots:
            data = dict(
                user_experience=item.get('user_experience').id,
                active_from_date=validated_data.get('active_from_date'),
                package=item.get('package').id
            )
            package_slot_instance = UserExperiencePackageSlot.objects.filter(
                user_experience=item.get('user_experience').id,
                active_from_date=validated_data.get('active_from_date')
            ).first()
            if package_slot_instance:
                serializer = UserExperiencePackageSlotCreateAndUpdateSerializer(
                    package_slot_instance,
                    data=data,
                    context=self.context
                )

            else:
                serializer = UserExperiencePackageSlotCreateAndUpdateSerializer(
                    data=data,
                    context=self.context
                )

            if serializer.is_valid():
                self.to_be_saved_serializers.append(serializer)
            else:
                self.set_user_error(
                    item.get('user'),
                    serializer.errors
                )

    def update(self, instance, *args):
        for serializer in self.to_be_saved_serializers:
            serializer.save()

        return instance

    def set_user_error(self, user, error):
        if user.id in self.bulk_apply_errors:
            self.bulk_apply_errors[user.id]['errors'].append(
                error
            )
        else:
            self.bulk_apply_errors[user.id] = dict(
                user=UserThinSerializer(user, exclude_fields=('is_audit_user', )).data,
                errors=[error]
            )
