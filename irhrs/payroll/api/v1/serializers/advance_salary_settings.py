from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from irhrs.core.constants.payroll import EMPLOYEE, SUPERVISOR
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    ApprovalSettingValidationMixin
from irhrs.core.utils.common import DummyObject
from irhrs.organization.api.v1.serializers.common_org_serializer import OrganizationSerializerMixin
from irhrs.organization.api.v1.serializers.employment import EmploymentStatusSerializer
from irhrs.organization.models import EmploymentStatus
from irhrs.payroll.api.v1.serializers import HeadingOrderSerializer
from irhrs.payroll.models import Heading
from irhrs.payroll.models.advance_salary_settings import (
    AmountSetting, AdvanceSalarySetting,
    ApprovalSetting)


class EligibilitySettingSerializer(OrganizationSerializerMixin, DynamicFieldsModelSerializer):
    class Meta:
        model = AdvanceSalarySetting
        fields = [
            'id', 'organization', 'time_of_service_completion', 'request_limit',
            'request_interval', 'complete_previous_request', 'excluded_employment_type',
        ]
        read_only_fields = ['organization']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context['request']
        if request and request.method.lower() == 'get' and 'excluded_employment_type' in fields:
            fields['excluded_employment_type'] = EmploymentStatusSerializer(
                many=True,
                fields=["title", "description", "is_contract", "slug"]
            )

        if request and request.method.lower() == 'post' and 'excluded_employment_type' in fields:
            fields['excluded_employment_type'] = serializers.SlugRelatedField(
                many=True,
                slug_field='slug',
                queryset=EmploymentStatus.objects.filter(organization=self.context['organization'])
            )
        return fields

    def create(self, validated_data):
        organization = self.context.get('organization')
        employment_types = None
        if 'excluded_employment_type' in validated_data:
            employment_types = validated_data.pop('excluded_employment_type')

        eligibility_setting, created = AdvanceSalarySetting.objects.update_or_create(
            organization=organization,
            defaults=validated_data
        )
        if isinstance(employment_types, list):
            _new_employment_type = set(map(lambda x: x.slug, employment_types))
            _old_employment_type = set(
                eligibility_setting.excluded_employment_type.all().values_list(
                    'slug', flat=True
                )
            )
            if _new_employment_type != _old_employment_type:
                _del_employment_type = _old_employment_type.difference(_new_employment_type)
                eligibility_setting.excluded_employment_type.remove(
                    *eligibility_setting.excluded_employment_type.filter(
                        slug__in=_del_employment_type
                    ))

                for employment_type in employment_types:
                    eligibility_setting.excluded_employment_type.add(employment_type)

        return eligibility_setting


class LimitUpToSettingSerializer(EligibilitySettingSerializer):
    class Meta(EligibilitySettingSerializer.Meta):
        model = EligibilitySettingSerializer.Meta.model
        fields = ['limit_upto']


class DisbursementSettingSerializer(EligibilitySettingSerializer):
    class Meta(EligibilitySettingSerializer.Meta):
        model = EligibilitySettingSerializer.Meta.model
        fields = ['disbursement_limit_for_repayment', 'deduction_heading']

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'post':
            fields['deduction_heading'] = serializers.PrimaryKeyRelatedField(
                queryset=Heading.objects.filter(organization=self.context['organization'])
            )
        elif self.request and self.request.method.lower() == 'get':
            fields['deduction_heading'] = HeadingOrderSerializer()

        return fields


class AmountHeadingSettingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = AmountSetting
        fields = [
            'payroll_heading', 'multiple',
        ]
        read_only_fields = ['organization']

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'post':
            fields['payroll_heading'] = serializers.PrimaryKeyRelatedField(
                queryset=Heading.objects.filter(organization=self.context['organization'])
            )
        return fields


class AmountSettingSerializer(serializers.Serializer):
    payroll_heading = AmountHeadingSettingSerializer(many=True)
    limit_upto = LimitUpToSettingSerializer()

    def create(self, validated_data):
        payroll_heading = validated_data.pop('payroll_heading')
        limit_upto = validated_data.pop('limit_upto')
        response_data = {
            'payroll_heading': self._save_payroll_heading(payroll_heading),
            'limit_upto': self._save_limit_upto(limit_upto)
        }
        return response_data

    def validate(self, attrs):
        payroll_heading = attrs.get('payroll_heading')
        limit_upto = attrs.get('limit_upto').get('limit_upto')
        if not payroll_heading and not limit_upto:
            raise ValidationError({
                'non_field_error': 'Must provide at least one of the configuration value.'
            })
        return super().validate(attrs)

    def validate_payroll_heading(self, payroll_heading):
        _new_heading = []
        if isinstance(payroll_heading, list):
            _new_heading = list(
                filter(
                    None,
                    map(
                        lambda heading: heading.get(
                            'payroll_heading'
                        ).id if 'payroll_heading' in heading else None,
                        payroll_heading
                    )
                )
            )
            if len(_new_heading) != len(set(_new_heading)):
                raise ValidationError({
                    'non_field_error': 'Amount Setting got similar payroll heading'
                })

        advance_salary_setting = self.context['advance_salary_setting']
        _old_heading = advance_salary_setting.amount_setting.all().values_list(
            'payroll_heading', flat=True
        )
        _deleted_heading = set(_old_heading).difference(set(_new_heading))
        if _deleted_heading:
            advance_salary_setting.amount_setting.filter(
                payroll_heading__id__in=_deleted_heading
            ).delete()
        return payroll_heading

    def _save_payroll_heading(self, account_data):
        advance_salary_setting = self.context['advance_salary_setting']
        bulk_create_amount_setting = []
        for payroll_heading in account_data:
            heading_amount_setting = AmountSetting.objects.filter(
                advance_salary_setting=advance_salary_setting,
                payroll_heading=payroll_heading.get('payroll_heading')
            )
            if heading_amount_setting.exists():
                heading_amount_setting.update(
                    multiple=payroll_heading.get('multiple')
                )
            else:
                bulk_create_amount_setting.append(
                    AmountSetting(
                        advance_salary_setting=advance_salary_setting,
                        **payroll_heading
                    )
                )

        if bulk_create_amount_setting:
            AmountSetting.objects.bulk_create(bulk_create_amount_setting)
        return account_data

    def _save_limit_upto(self, limit_upto):
        advance_salary_setting = self.context['advance_salary_setting']
        advance_salary_setting.limit_upto = limit_upto.get('limit_upto')
        advance_salary_setting.save()
        return limit_upto


class ApprovalSettingSerializer(ApprovalSettingValidationMixin, DynamicFieldsModelSerializer):
    class Meta:
        model = ApprovalSetting
        fields = ['id', 'approve_by', 'supervisor_level', 'employee', 'approval_level']
        read_only_fields = ['approval_level']


class ApprovalSettingBulkSerializer(DynamicFieldsModelSerializer):
    approvals = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalSetting
        fields = ('approvals', )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'post':
            fields['approvals'] = ApprovalSettingSerializer(many=True)
        return fields

    def get_advance_salary_setting(self):
        return self.context.get('advance_salary_setting')

    def get_approvals(self, obj):
        setting = self.get_advance_salary_setting()
        return ApprovalSettingSerializer(
            setting.approval_setting.all(),
            many=True
        ).data

    @staticmethod
    def validate_approvals(approvals):
        if len(approvals) < 1 or len(approvals) > 5:
            raise ValidationError('Approval Hierarchy can\'t be less than 1 or more than 5.')

        supervisor_list = [
            approve_by.get('supervisor_level') for approve_by in approvals
            if approve_by.get('approve_by') == SUPERVISOR
        ]
        employee_list = [
            emp.get('employee') for emp in approvals
            if emp.get('approve_by') == EMPLOYEE
        ]
        if supervisor_list and len(supervisor_list) != len(set(supervisor_list)):
            raise ValidationError("Approval Setting got similar supervisor level.")

        if employee_list and len(employee_list) != len(set(employee_list)):
            raise ValidationError("Approval Setting got similar employee.")
        return approvals

    def create(self, validated_data):
        instance = dict(validated_data)
        approvals = validated_data.pop('approvals', [])
        ApprovalSetting.objects.filter(
            advance_salary_setting=self.get_advance_salary_setting()
        ).delete()
        for index, approval in enumerate(approvals, start=1):
            if approval.get('approve_by') == EMPLOYEE:
                approval.pop('supervisor_level', None)
            else:
                approval['employee'] = None
            approval['approval_level'] = index
            approval['advance_salary_setting'] = self.get_advance_salary_setting()
            ApprovalSetting.objects.create(**approval)
            if approval['approve_by'] == EMPLOYEE:
                approval['supervisor'] = None
            approval['employee'] = approval.pop('employee', None)

        return DummyObject(**instance)
