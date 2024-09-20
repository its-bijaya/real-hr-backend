from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.constants.payroll import EMPLOYEE, SUPERVISOR
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject
from irhrs.organization.api.v1.serializers.common_org_serializer import OrganizationSerializerMixin
from irhrs.reimbursement.constants import SETTLEMENT_OPTION
from irhrs.reimbursement.models import ExpenseApprovalSetting
from irhrs.reimbursement.models.setting import (
    ReimbursementSetting,
    SettlementApprovalSetting,
    SettlementOptionSetting
)


class ExpenseApprovalSettingSerializer(
    OrganizationSerializerMixin,
    DynamicFieldsModelSerializer
):
    class Meta:
        model = ExpenseApprovalSetting
        fields = [
            'id', 'approve_by', 'supervisor_level', 'employee',
            'approval_level', 'organization', 'select_employee'
        ]
        read_only_fields = ['approval_level', 'organization']
        extra_kwargs = {
            'employee': {'required': False, 'allow_null': True, 'allow_empty': True},
            'supervisor_level': {'required': False},
        }

    def validate(self, attrs):
        approve_by = attrs.get('approve_by')
        supervisor_level = attrs.get('supervisor_level', None)
        employee = attrs.get('employee', [])
        if not approve_by:
            raise ValidationError({
                'approved_by': ['This field is required.']
            })

        if approve_by == SUPERVISOR and not supervisor_level:
            raise ValidationError({
                'supervisor_level': 'This field is required if approve_by is set to supervisor.'
            })

        if approve_by == EMPLOYEE and not employee:
            raise ValidationError({
                'employee': 'This field is required if approve_by is set to employee.'
            })
        return attrs

class SettlementApprovalSettingSerializer(ExpenseApprovalSettingSerializer):
    class Meta(ExpenseApprovalSettingSerializer.Meta):
        model = SettlementApprovalSetting

class ReimbursementSettingSerializer(
    DynamicFieldsModelSerializer
):
    options = serializers.SerializerMethodField()

    class Meta:
        model = ReimbursementSetting
        fields = ['options', 'advance_code', 'approve_multiple_times', 'travel_report_mandatory']

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'post':
            fields['options'] = serializers.MultipleChoiceField(
                choices=dict(SETTLEMENT_OPTION).values(),
                allow_blank=True
            )
        return fields

    @staticmethod
    def get_options(obj):
        return obj.options.values_list('option', flat=True)


class OverallReimbursementSetting(
    OrganizationSerializerMixin,
    DynamicFieldsModelSerializer
):
    options = serializers.SerializerMethodField()
    approvals = serializers.SerializerMethodField()
    settlement_approvals = serializers.SerializerMethodField()

    class Meta:
        model = ReimbursementSetting
        fields = [
            'advance_code', 'approve_multiple_times', 'options', 'approvals',
            'per_diem_rate', 'lodging_rate', 'others_rate', 'settlement_approvals',
            'travel_report_mandatory'
        ]

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'post':
            fields['approvals'] = ExpenseApprovalSettingSerializer(many=True)
            fields['settlement_approvals'] = SettlementApprovalSettingSerializer(many=True)
            fields['options'] = serializers.MultipleChoiceField(
                choices=dict(SETTLEMENT_OPTION).values(),
                allow_blank=True
            )
        return fields

    @staticmethod
    def get_options(obj):
        return obj.options.values_list('option', flat=True)

    @staticmethod
    def get_approvals(obj):
        organization = obj.organization
        return ExpenseApprovalSettingSerializer(
            organization.expense_setting.all(),
            many=True
        ).data

    @staticmethod
    def get_settlement_approvals(obj):
        organization = obj.organization
        return SettlementApprovalSettingSerializer(
            organization.settlement_setting.all(),
            many=True
        ).data

    @staticmethod
    def _validate_approvals(approvals):
        if len(approvals) < 1 or len(approvals) > 5:
            raise ValidationError('Approval Hierarchy can\'t be less than 1 or more than 5.')

        supervisor_list = [
            approve_by.get('supervisor_level') for approve_by in approvals
            if approve_by.get('approve_by') == SUPERVISOR
        ]

        if supervisor_list and len(supervisor_list) != len(set(supervisor_list)):
            raise ValidationError("Approval Setting got similar supervisor level.")
        return approvals

    def validate_approvals(self, approvals):
        return self._validate_approvals(approvals)

    def validate_settlement_approvals(self, approvals):
        return self._validate_approvals(approvals)

    @staticmethod
    def _create_setting(data, organization, options):
        setting, created = ReimbursementSetting.objects.update_or_create(
            organization=organization,
            defaults={
                **data
            }
        )

        settlement_options = []
        old_options = setting.options.values_list('option', flat=True)
        deleted_options = set(old_options) - set(options)
        new_options = set(options) - set(old_options)

        if deleted_options:
            setting.options.filter(
                option__in=deleted_options
            ).delete()

        if new_options:
            for option in new_options:
                settlement_options.append(
                    SettlementOptionSetting(
                        setting=setting,
                        option=option
                    )
                )
            if settlement_options:
                SettlementOptionSetting.objects.bulk_create(settlement_options)
        return setting

    @staticmethod
    def _create_approval(klass, organization, approvals):
        """
        This method is called to create either SettlementApprovalSetting
        or ExpenseApprovalSetting
        """
        klass.objects.filter(organization=organization).delete()
        for index, approval in enumerate(approvals, start=1):
            if approval.get('approve_by') == EMPLOYEE:
                __ = approval.pop('supervisor_level', None)
            else:
                approval['employee'] = []
                approval['select_employee'] = False

            employee = approval.pop('employee', [])
            approval['organization'] = organization
            approval['approval_level'] = index
            instance =klass.objects.create(**approval)
            if approval['approve_by'] == EMPLOYEE:
                instance.employee.set(employee)
                approval['supervisor'] = None
            approval['employee'] = employee

    def create(self, validated_data):
        instance = dict(validated_data)
        approvals = validated_data.pop('approvals', [])
        settlement_approvals = validated_data.pop('settlement_approvals', [])
        options = validated_data.pop('options', [])
        organization = self.context.get('organization')
        self._create_setting(validated_data, organization, options)
        self._create_approval(ExpenseApprovalSetting, organization, approvals)
        self._create_approval(SettlementApprovalSetting,organization,settlement_approvals)
        return DummyObject(**instance)
