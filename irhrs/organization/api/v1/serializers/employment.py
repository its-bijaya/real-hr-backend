from django.db.models import Max
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from django.conf import settings
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import get_patch_attr
from irhrs.organization.api.v1.serializers.branch import \
    OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.common_org_serializer import \
    OrganizationSerializerMixin
from irhrs.organization.api.v1.serializers.organization import \
    OrganizationSerializer
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer
from irhrs.users.models import UserExperience
from ....models import EmploymentStatus, EmploymentLevel, EmploymentJobTitle, \
    EmploymentStep


class EmploymentStatusSerializer(DynamicFieldsModelSerializer):
    slug = serializers.ReadOnlyField()

    class Meta:
        model = EmploymentStatus
        fields = ('id', 'title', 'description', 'is_contract', 'slug', 'created_at',
                  'modified_at', 'is_archived')

    def create(self, validated_data):
        validated_data.update({
            'organization': self.context.get('organization')
        })
        return super().create(validated_data)

    def validate_title(self, data):
        """
        Raise Validation Error if the provided title already exists for the org.
        """
        qs = EmploymentStatus.objects.filter(
            title__iexact=data,
            organization=self.context.get('organization'))
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Employment Status title already exists.")
        return data

    @staticmethod
    def validate_description(description):
        if description and len(description) > settings.TEXT_FIELD_MAX_LENGTH:
            raise ValidationError(
                f"The field length must be less than {settings.TEXT_FIELD_MAX_LENGTH}"
            )
        return description


class EmploymentLevelSerializer(DynamicFieldsModelSerializer):
    slug = serializers.ReadOnlyField()

    class Meta:
        model = EmploymentLevel
        fields = (
            'id', 'slug', 'title', 'code', 'description', 'order_field',
            'scale_max', 'auto_increment', 'auto_add_step',
            'is_archived', 'created_at', 'modified_at',
            'changes_on_fiscal', 'frequency', 'duration',
            'level'
        )

    def validate(self, attrs):
        (
            changes_on_fiscal, frequency, duration, auto_increment,
            auto_add_step
        ) = map(
            lambda x: get_patch_attr(x, attrs, self),
            (
                'changes_on_fiscal', 'frequency', 'duration', 'auto_increment',
                'auto_add_step'
            )
        )
        if auto_increment:
            errors = dict()
            if not auto_add_step:
                errors.update({
                    'auto_add_step': 'Please add the number of steps to add in '
                                     'auto increment'
                })
            if changes_on_fiscal not in [True, False]:
                errors.update({
                    'changes_on_fiscal': 'This must be selected if auto '
                                         'increment is enabled.'
                })
            if not frequency:
                errors.update({
                    'frequency': 'Please set frequency if auto increment '
                                 'is selected.'
                })
            if not duration:
                errors.update({
                    'duration': 'Please set duration if auto increment '
                                'is selected.'
                })

            if errors:
                raise ValidationError(errors)
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data.update({
            'organization': self.context.get('organization')
        })
        return super().create(validated_data)

    def validate_title(self, data):
        qs = EmploymentLevel.objects.filter(
            organization=self.context.get('organization'),
            title__iexact=data
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Employment level '{data}' already exists")
        return data

    def validate_code(self, data):
        if data == '':  # The code can be blank but can not be duplicated
            return data
        qs = EmploymentLevel.objects.filter(
            organization=self.context.get('organization'),
            code__iexact=data
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Employment Code '{data}' already exists")
        return data

    def validate_order_field(self, data):
        qs = EmploymentLevel.objects.filter(
            organization=self.context.get('organization'),
            order_field=data
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Employment Order Field '{data}' already "
                                  f"exists")
        return data

    def validate_scale_max(self, scale_max):
        if self.instance:
            max_step_used = UserExperience.objects.filter(
                employee_level=self.instance
            ).aggregate(
                max_step_used=Max('current_step')
            ).get(
                'max_step_used'
            )
            if max_step_used and max_step_used > scale_max:
                raise ValidationError(
                    f"Scaling below {max_step_used} is not possible, because "
                    f"it is assigned."
                )
        return scale_max


class EmploymentJobTitleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = EmploymentJobTitle
        fields = ('id', 'slug', 'title', 'description', 'created_at', 'modified_at')
        read_only_fields = ('slug',)

    def create(self, validated_data):
        validated_data.update({
            'organization': self.context.get('organization')
        })
        return super().create(validated_data)

    def validate_title(self, data):
        qs = EmploymentJobTitle.objects.filter(
            organization=self.context.get('organization'),
            title__iexact=data
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("The Job Title for the Organization exists.")
        return super().validate(data)

    @staticmethod
    def validate_description(description):
        if description and len(description) > settings.TEXT_FIELD_MAX_LENGTH:
            raise ValidationError(
                f"The field length must be less than {settings.TEXT_FIELD_MAX_LENGTH}"
            )
        return description


class EmploymentStepSerializer(OrganizationSerializerMixin):
    title = serializers.CharField(max_length=100,
                                  validators=[UniqueValidator(
                                      queryset=EmploymentStep.objects.all())])

    class Meta(OrganizationSerializerMixin.Meta):
        model = EmploymentStep
        fields = ('organization', 'title', 'description', 'slug',)
        read_only_fields = ('slug',)


class EmploymentStatusReportSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(read_only=True)
    organization = OrganizationSerializer(fields=['name', 'slug'],
                                          read_only=True)
    employee_level = EmploymentLevelSerializer(
        fields=['title', 'slug'],
        read_only=True)
    employment_status = EmploymentStatusSerializer(
        fields=['title', 'slug'],
        read_only=True)
    branch = OrganizationBranchSerializer(
        fields=['organization', 'name', 'slug'],
        read_only=True)
    supervisor = UserThinSerializer(
        source='user.first_level_supervisor'
    )
    date_of_birth = serializers.SerializerMethodField()

    class Meta:
        model = UserExperience
        fields = [
            'user', 'organization', 'employee_level', 'employment_status',
            'branch', 'change_type', 'supervisor', 'job_title', 'is_current',
            'start_date', 'end_date', 'date_of_birth'
        ]

    def get_fields(self):
        from irhrs.hris.api.v1.serializers.onboarding_offboarding import ChangeTypeSerializer
        fields = super().get_fields()
        fields['change_type'] = ChangeTypeSerializer(
            fields=['name', 'slug']
        )
        return fields

    @staticmethod
    def get_date_of_birth(obj):
        return obj.user.detail.date_of_birth
