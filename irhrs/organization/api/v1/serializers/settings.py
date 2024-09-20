from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from irhrs.core.constants.organization import (
    ACTION_ON_CREDIT_HOUR_EMAIL, ACTION_ON_PAYROLL_APPROVAL_BY_APPROVAL_LEVELS, ADVANCE_EXPENSE_REQUEST_EMAIL,
    ADVANCE_EXPENSE_SETTING_APPROVE_OR_DENY, ADVANCE_EXPENSES_REQUEST_CANCELLED_BY_HR, 
    ADVANCE_EXPENSES_SETTLEMENT_APPROVE_OR_DENY, ADVANCE_EXPENSES_SETTLEMENT_BY_HR,
    ADVANCE_EXPENSES_SETTLEMENT_EMAIL,ADVANCE_SALARY_IS_REQUESTED_BY_USER,ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL,ANNIVERSARY_EMAIL, 
    ASSESSMENT_ASSIGNED_UNASSIGNED_TO_USER_EMAIL, ASSESSMENT_COMPLETED_BY_USER_EMAIL,
    BIRTHDAY_EMAIL, CONTRACT_EXPIRY_ALERT_EMAIL,
    CREDIT_HOUR_APPROVAL_REQUESTED_FORWARDED_EMAIL, 
    CREDIT_HOUR_DELETE_REQUEST_IS_REQUESTED_FORWARDED_EMAIL,
    CREDIT_HOUR_DELETE_REQUEST_IS_APPROVED_DECLINED_EMAIL,
    CREDIT_HOUR_REQUEST_ON_BEHALF, EVENT_CANCELED_DELETED_EMAIL,
    EVENT_UPDATED_EMAIL, GENERATE_ADVANCE_SALARY_BY_HR,HOLIDAY_EMAIL, INVITED_TO_EVENT_EMAIL,
    PAYROLL_ACKNOWLEDGED_BY_USER, PAYROLL_APPROVAL_NEEDED_EMAIL, PAYROLL_CONFIRMATION_BY_HR, 
    EVENT_UPDATED_EMAIL, HOLIDAY_EMAIL, INVITED_TO_EVENT_EMAIL, REBATE_IS_APPROVED_DECLINED, REBATE_IS_REQUESTED_BY_USER, REBATE_IS_REQUESTED_ON_BEHALF_USER_BY_HR, 
    RESIGNATION_REMINDER_EMAIL, RESIGNATION_REQUEST_ACTION_EMAIL,
    RESIGNATION_REQUEST_EMAIL, TRAINING_ASSIGNED_UNASSIGNED_EMAIL, 
    TRAINING_CANCELLED_EMAIL, TRAINING_REQUESTED_ACTION_EMAIL, 
    TRAINING_REQUESTED_EMAIL, TRAINING_UPDATED_EMAIL,
    ATTENDANCE_ADJUSTMENT_REQUEST_EMAIL,
    ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_BY_SUPERVISOR_EMAIL,
    ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_DELETED_BY_HR_EMAIL,
    OVERTIME_CLAIM_APPROVED_DENIED_CONFIRMED, OVERTIME_CLAIM_REQUEST,
    OVERTIME_GENERATED_EMAIL, OVERTIME_RECALIBRATE_EMAIL,
    OVERTIME_UNCLAIMED_EXPIRED,
    TRAVEL_ATTENDANCE_IS_APPROVED_DECLINED,
    TRAVEL_ATTENDANCE_REQUEST_EMAIL, LEAVE_DEDUCTION_ON_PENALTY,
)

from irhrs.core.utils.common import DummyObject
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.organization.api.v1.serializers.common_org_serializer import \
    OrganizationSerializerMixin

from irhrs.organization.models.settings import ContractSettings, \
    ApplicationSettings, EmailNotificationSetting


class ContractSettingsSerializer(OrganizationSerializerMixin):
    class Meta:
        model = ContractSettings
        fields = ["safe_days", "critical_days"]

    def validate(self, attrs):
        if attrs.get('safe_days') <= attrs.get('critical_days'):
            raise ValidationError(
                "`Safe Days` must be greater than `Critical Days`")
        return attrs


class ApplicationSettingsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ApplicationSettings
        fields = ('id',
                  'application',
                  'enabled')

    def validate(self, attrs):
        organization = self.context.get('organization')
        attrs['organization'] = organization
        application = attrs.get('application')

        if ApplicationSettings.objects.filter(
            organization=organization,
            application=application
        ).exists():
            raise ValidationError("Application Settings already exists.")
        return attrs


# Each email notification serializer will look up email category map to 
# get the category of the given email type
EMAIL_CATEGORY_MAP = {
    **dict.fromkeys(
        [
            TRAVEL_ATTENDANCE_IS_APPROVED_DECLINED,
            TRAVEL_ATTENDANCE_REQUEST_EMAIL
        ], "travel"
    ),
    **dict.fromkeys(
        [
            ATTENDANCE_ADJUSTMENT_REQUEST_EMAIL,
            ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_BY_SUPERVISOR_EMAIL,
            ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_DELETED_BY_HR_EMAIL
        ], "adjustment"
    ),
    **dict.fromkeys(
        [
            OVERTIME_GENERATED_EMAIL,
            OVERTIME_RECALIBRATE_EMAIL,
            OVERTIME_CLAIM_REQUEST,
            OVERTIME_UNCLAIMED_EXPIRED,
            OVERTIME_CLAIM_APPROVED_DENIED_CONFIRMED
        ], "overtime"
    ),
    **dict.fromkeys(
        [
            LEAVE_DEDUCTION_ON_PENALTY
        ], "penalty"
    ),
    **dict.fromkeys(
        [
            CREDIT_HOUR_APPROVAL_REQUESTED_FORWARDED_EMAIL,
            ACTION_ON_CREDIT_HOUR_EMAIL,
            CREDIT_HOUR_DELETE_REQUEST_IS_REQUESTED_FORWARDED_EMAIL,
            CREDIT_HOUR_DELETE_REQUEST_IS_APPROVED_DECLINED_EMAIL,
            CREDIT_HOUR_REQUEST_ON_BEHALF
        ], "credit_hour"
    ),
     **dict.fromkeys(
        [
            PAYROLL_APPROVAL_NEEDED_EMAIL,
            ACTION_ON_PAYROLL_APPROVAL_BY_APPROVAL_LEVELS,
            PAYROLL_CONFIRMATION_BY_HR,
            PAYROLL_ACKNOWLEDGED_BY_USER,
        ], "payroll_generate"
    ),
     **dict.fromkeys(
        [
            REBATE_IS_REQUESTED_BY_USER,
            REBATE_IS_APPROVED_DECLINED,
            REBATE_IS_REQUESTED_ON_BEHALF_USER_BY_HR,
        ], "payroll_rebate"
    ),
    **dict.fromkeys(
        [
            ADVANCE_SALARY_IS_REQUESTED_BY_USER,
            ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL,
            GENERATE_ADVANCE_SALARY_BY_HR,
        ], "advance_salary"
    ),
}

class EmailNotificationSettingSerializer(OrganizationSerializerMixin):
    email_type_display = serializers.ReadOnlyField(source='get_email_type_display')
    category = serializers.SerializerMethodField()

    class Meta:
        model = EmailNotificationSetting
        read_only_field = ('organization',)
        exclude = ('created_by', 'modified_by')

    @staticmethod
    def get_category(obj):
        return EMAIL_CATEGORY_MAP.get(obj.email_type, "")


# add other module-wise email_type respectively
MODULE_WISE_EMAIL_TYPE = {
    "hris": [
        BIRTHDAY_EMAIL, ANNIVERSARY_EMAIL, HOLIDAY_EMAIL,
        CONTRACT_EXPIRY_ALERT_EMAIL, RESIGNATION_REQUEST_EMAIL,
        RESIGNATION_REQUEST_ACTION_EMAIL, RESIGNATION_REMINDER_EMAIL
    ],
    "event": [INVITED_TO_EVENT_EMAIL, EVENT_UPDATED_EMAIL, EVENT_CANCELED_DELETED_EMAIL],
    "training": [
        TRAINING_ASSIGNED_UNASSIGNED_EMAIL, TRAINING_CANCELLED_EMAIL,
        TRAINING_REQUESTED_EMAIL, TRAINING_UPDATED_EMAIL, TRAINING_REQUESTED_ACTION_EMAIL
    ],
    "assessment": [
        ASSESSMENT_ASSIGNED_UNASSIGNED_TO_USER_EMAIL,
        ASSESSMENT_COMPLETED_BY_USER_EMAIL
    ],
    "expense_management": [
        ADVANCE_EXPENSE_REQUEST_EMAIL, ADVANCE_EXPENSES_SETTLEMENT_EMAIL, 
        ADVANCE_EXPENSE_SETTING_APPROVE_OR_DENY, ADVANCE_EXPENSES_SETTLEMENT_APPROVE_OR_DENY,
        ADVANCE_EXPENSES_SETTLEMENT_BY_HR, ADVANCE_EXPENSES_REQUEST_CANCELLED_BY_HR
    ],
    "attendance": [
        ATTENDANCE_ADJUSTMENT_REQUEST_EMAIL,
        ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_BY_SUPERVISOR_EMAIL,
        ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_DELETED_BY_HR_EMAIL,

        LEAVE_DEDUCTION_ON_PENALTY,
        
        OVERTIME_GENERATED_EMAIL,
        OVERTIME_RECALIBRATE_EMAIL,
        OVERTIME_CLAIM_REQUEST,
        OVERTIME_UNCLAIMED_EXPIRED,
        OVERTIME_CLAIM_APPROVED_DENIED_CONFIRMED,

        CREDIT_HOUR_APPROVAL_REQUESTED_FORWARDED_EMAIL,
        ACTION_ON_CREDIT_HOUR_EMAIL,
        CREDIT_HOUR_DELETE_REQUEST_IS_REQUESTED_FORWARDED_EMAIL,
        CREDIT_HOUR_DELETE_REQUEST_IS_APPROVED_DECLINED_EMAIL,
        CREDIT_HOUR_REQUEST_ON_BEHALF,

        TRAVEL_ATTENDANCE_IS_APPROVED_DECLINED,
        TRAVEL_ATTENDANCE_REQUEST_EMAIL,
    ],

    "payroll": [
        PAYROLL_APPROVAL_NEEDED_EMAIL,
        ACTION_ON_PAYROLL_APPROVAL_BY_APPROVAL_LEVELS,
        PAYROLL_CONFIRMATION_BY_HR,
        PAYROLL_ACKNOWLEDGED_BY_USER,

        REBATE_IS_REQUESTED_BY_USER,
        REBATE_IS_APPROVED_DECLINED,
        REBATE_IS_REQUESTED_ON_BEHALF_USER_BY_HR,

        ADVANCE_SALARY_IS_REQUESTED_BY_USER,
        ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL,
        GENERATE_ADVANCE_SALARY_BY_HR,
    ],
}

class EmailGroupNotificationSettingSerializer(serializers.Serializer):
    results = serializers.SerializerMethodField()

    class Meta:
        fields = ('results', )

    @staticmethod
    def get_results(obj):
        out = dict()
        for key, items in MODULE_WISE_EMAIL_TYPE.items():
            out[key] = EmailNotificationSettingSerializer(
                obj.filter(email_type__in=MODULE_WISE_EMAIL_TYPE.get(key)),
                many=True
            ).data
        return out


class EmailNotificationSettingBulkUpdateSerializer(DummySerializer):
    email_settings = EmailNotificationSettingSerializer(
        fields=['email_type', 'send_email', 'allow_unsubscribe'],
        many=True
    )

    @transaction.atomic()
    def create(self, validated_data):
        created_instances = []
        for email_setting_data in validated_data.get('email_settings', []):
            email_type = email_setting_data.pop('email_type')
            instance, created = EmailNotificationSetting.objects.update_or_create(
                organization=self.context.get('organization'),
                email_type=email_type,
                defaults=email_setting_data
            )
            created_instances.append(instance)
        return DummyObject(email_settings=created_instances)
