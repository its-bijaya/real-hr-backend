from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.mixins.viewset_mixins import DisallowPatchMixin
from irhrs.core.utils.common import get_today, DummyObject
from irhrs.leave.constants.model_constants import GENERAL, CATEGORY_FIELD_MAP, \
    IDLE, ACTIVE, APPLICABLE_GENDER_CHOICES, APPLICABLE_MARITAL_STATUS_CHOICES
from irhrs.leave.constants.validation_error_messages import \
    NAME_ORGANIZATION_NOT_UNIQUE, PAID_OR_UNPAID_REQUIRED, \
    ONE_WAY_TO_APPLY_REQUIRED, MUST_SET_ACTION_FOR_REMAINING_BALANCE, \
    THERE_IDLE_IDLE_SETTING, ALREADY_ONE_ACTIVE_SETTING, \
    SELECTED_CATEGORY_NOT_IN_MASTER_SETTING, CAN_NOT_ASSOCIATE_TO_MASTER_SETTING
from irhrs.leave.models import MasterSetting, LeaveType
from irhrs.leave.models.settings import LeaveApproval
from irhrs.leave.utils.master_settings_validator import \
    MasterSettingUpdateValidator
from irhrs.leave.utils.setting import check_in_setting
from irhrs.organization.api.v1.serializers.common_org_serializer import \
    OrganizationSerializerMixin
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

USER = get_user_model()


class MasterSettingSerializer(DisallowPatchMixin,
                              OrganizationSerializerMixin,
                              DynamicFieldsModelSerializer):
    class Meta:
        model = MasterSetting
        fields = (
            "cloned_from",
            "id",
            "name",
            "description",
            "status",

            "effective_from",
            "effective_till",

            "accumulation",
            "renewal",
            "deductible",

            "paid",
            "unpaid",

            "half_shift_leave",
            "occurrences",
            "beyond_balance",
            "proportionate_leave",
            "depletion_required",

            "require_experience",
            "require_time_period",
            "require_prior_approval",
            "require_document",

            "leave_limitations",
            "leave_irregularities",
            "employees_can_apply",
            "admin_can_assign",

            "continuous",
            "holiday_inclusive",

            "encashment",
            "carry_forward",
            "collapsible",

            "years_of_service",
            "time_off",
            "compensatory",
            "credit_hour",
        )
        read_only_fields = (
            "id", "effective_till", "status"
        )
        extra_kwargs = {
            "accumulation": {"required": True},
            "renewal": {"required": True},
            "deductible": {"required": True},

            "paid": {"required": True},
            "unpaid": {"required": True},

            "half_shift_leave": {"required": True},
            "occurrences": {"required": True},
            "beyond_balance": {"required": True},
            "proportionate_leave": {"required": True},
            "depletion_required": {"required": True},

            "require_experience": {"required": True},
            "require_time_period": {"required": True},
            "require_prior_approval": {"required": True},
            "require_document": {"required": True},

            "leave_limitations": {"required": True},
            "leave_irregularities": {"required": True},
            "employees_can_apply": {"required": True},
            "admin_can_assign": {"required": True},

            "continuous": {"required": True},
            "holiday_inclusive": {"required": True},

            "encashment": {"required": True},
            "carry_forward": {"required": True},
            "collapsible": {"required": True},

            "years_of_service": {"required": True},
            "time_off": {"required": True},
            "compensatory": {"required": True}
        }
        create_only_fields = 'cloned_from',

    def validate_name(self, name):
        organization = self.context.get('organization')
        qs = organization.leave_master_settings.all()
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.filter(name=name).exists():
            raise ValidationError(NAME_ORGANIZATION_NOT_UNIQUE)

        return name

    def validate_effective_from(self, effective_from):
        today = get_today()
        organization = self.context.get('organization')
        # Effective From can be null (IDLE status). There won't be multiple IDLE.

        # The issue becomes date conflicts.

        if (not self.instance and effective_from == today and
            MasterSetting.objects.all().active().filter(
                organization=organization).exists()):
            # if effective from is today and there is
            #  already a setting active
            raise ValidationError(ALREADY_ONE_ACTIVE_SETTING)
        return effective_from

    def validate(self, attrs):
        organization = self.context.get('organization')
        if not self.instance and MasterSetting.objects.all().idle().filter(
            organization=organization).exists():
            raise ValidationError(THERE_IDLE_IDLE_SETTING)

        paid = attrs.get('paid')
        unpaid = attrs.get('unpaid')

        employees_can_apply = attrs.get('employees_can_apply')
        admin_can_assign = attrs.get('admin_can_assign')

        encashment = attrs.get('encashment')
        carry_forward = attrs.get('carry_forward')
        collapsible = attrs.get('collapsible')

        if not (paid or unpaid):
            raise ValidationError(PAID_OR_UNPAID_REQUIRED)

        if not (employees_can_apply or admin_can_assign):
            raise ValidationError(ONE_WAY_TO_APPLY_REQUIRED)

        if not (encashment or carry_forward or collapsible):
            raise ValidationError(MUST_SET_ACTION_FOR_REMAINING_BALANCE)

        if self.instance:
            is_valid, errors = MasterSettingUpdateValidator.validate(
                self.instance, attrs)
            if not is_valid:
                raise ValidationError(errors)
        return attrs

    @transaction.atomic()
    def save(self, **kwargs):
        instance = super().save(**kwargs)

        organization = self.context.get('organization')

        # if there is effective from, set effective till for currently active setting.
        if instance.effective_from:
            active_setting_end_date = (
                instance.effective_from - timezone.timedelta(days=1)
            )
            # add effective till to currently active setting
            MasterSetting.objects.all().active().filter(
                organization=organization
            ).exclude(id=instance.id).update(effective_till=active_setting_end_date)

        return instance


class LeaveTypeSerializer(DynamicFieldsModelSerializer):
    applicable_for_gender = serializers.ChoiceField(
        choices=APPLICABLE_GENDER_CHOICES,
    )

    applicable_for_marital_status = serializers.ChoiceField(
        choices=APPLICABLE_MARITAL_STATUS_CHOICES
    )

    class Meta:
        model = LeaveType
        fields = (
            "cloned_from",
            "id",
            "master_setting",
            "name",
            "description",
            "applicable_for_gender",
            "applicable_for_marital_status",
            "category",
            "email_notification",
            "sms_notification",
            "is_archived",
            "visible_on_default",
            "multi_level_approval"
        )
        read_only_fields = ("id", "is_archived",)
        create_only_fields = 'cloned_from',

    def get_unique_together_validators(self):
        validators = []
        vs = super().get_unique_together_validators()
        for v in vs:
            if v.fields == ('name', 'master_setting'):
                v.message = "The name already exists for the master setting."
            validators.append(v)
        return validators

    def validate(self, attrs):
        master_setting = attrs.get('master_setting')

        category = attrs.get('category')
        if category != GENERAL and not (check_in_setting(
            master_setting, CATEGORY_FIELD_MAP.get(category))):
            raise ValidationError({
                "category": [SELECTED_CATEGORY_NOT_IN_MASTER_SETTING]
            })

        return attrs

    def validate_master_setting(self, master_setting):
        if self.instance:
            return self.instance.master_setting
        if master_setting.status not in [IDLE, ACTIVE]:
            raise ValidationError(CAN_NOT_ASSOCIATE_TO_MASTER_SETTING)
        return master_setting

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['name'] = SerializerMethodField()
        return fields

    def get_name(self, instance):
        if self.context.get('merge_master_setting_name'):
            return instance.master_setting.name + '--' + instance.name
        return instance.name


class LeaveApprovalSerializer(OrganizationSerializerMixin, DynamicFieldsModelSerializer):
    approvals = serializers.PrimaryKeyRelatedField(
        queryset=USER.objects.all().current(),
        many=True,
        write_only=True
    )
    user = UserThinSerializer(
        source='employee',
        fields=['id', 'full_name', 'profile_picture', 'cover_picture', 'organization', 'is_current',],
        read_only=True
    )
    approval_level = serializers.IntegerField(
        source='authority_order',
        read_only=True
    )

    class Meta:
        model = LeaveApproval
        fields = ['id', 'user', 'approval_level', 'organization', 'approvals']
        read_only_fields = ['organization', ]

    @staticmethod
    def validate_approvals(employee):
        if len(employee) != len(set(employee)):
            raise ValidationError('User can\'t be repeated in approval level.')
        if len(employee) > 5:
            raise ValidationError('Only 5 employee can be accepted as approvals in leave.')
        return employee

    def create(self, validated_data):
        employees = validated_data.get('approvals')
        organization = self.context.get('organization')
        approvals = []
        for index, employee in enumerate(employees, start=1):
            approvals.append(
                LeaveApproval(
                    organization=organization,
                    authority_order=index,
                    employee=employee
                )
            )

        if approvals:
            LeaveApproval.objects.bulk_create(approvals)

        return DummyObject(**validated_data)
