from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.constants.payroll import EMPLOYEE, SUPERVISOR
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject
from irhrs.organization.api.v1.serializers.common_org_serializer import OrganizationSerializerMixin
from irhrs.forms.models import FormApprovalSettingLevel, Form


class FormApprovalSerializer(
    OrganizationSerializerMixin,
    DynamicFieldsModelSerializer
):
    class Meta:
        model = FormApprovalSettingLevel
        fields = [
            'id', 'approve_by', 'supervisor_level', 'employee',
            'approval_level', 'form'
        ]
        read_only_fields = ['approval_level', 'organization']
        extra_kwargs = {
            'employee': {'required': False, 'allow_null': True, 'allow_empty': True},
            'supervisor_level': {'required': False},
            'form': {'required': False},
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


class ReadFormApprovalSettingLevelSerializer(
    OrganizationSerializerMixin,
    serializers.ModelSerializer
):
    results = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = ("results",)

    def get_results(self, obj):
        approvals = obj.form_approval_setting.all()
        return FormApprovalSerializer(approvals, many=True).data


class FormApprovalSettingLevelSerializer(
    OrganizationSerializerMixin,
    serializers.ModelSerializer
):
    approvals = FormApprovalSerializer(many=True)

    class Meta:
        model = FormApprovalSettingLevel
        fields = ('approvals',)

    @staticmethod
    def validate_approvals(approvals):

        supervisor_list = [
            approve_by.get('supervisor_level') for approve_by in approvals
            if approve_by.get('approve_by') == SUPERVISOR
        ]

        if supervisor_list and len(supervisor_list) != len(set(supervisor_list)):
            raise ValidationError(
                "Approval Setting got similar supervisor level.")
        return approvals

    @staticmethod
    def _create_approval(organization, approvals, form):
        FormApprovalSettingLevel.objects.filter(form=form).delete()
        final_approvals = []
        for index, approval in enumerate(approvals, start=1):
            if approval.get('approve_by') == EMPLOYEE:
                approval.pop('supervisor_level', None)
            else:
                approval['employee'] = None
            employee = approval.pop('employee', None)
            approval['approval_level'] = index
            approval['form'] = form
            if approval['approve_by'] == EMPLOYEE:
                approval['employee'] = employee
                approval['supervisor_level'] = None
            instance = FormApprovalSettingLevel.objects.create(**approval)
            final_approvals.append(instance)
        return final_approvals

    def create(self, validated_data):
        instance = dict(validated_data)
        approvals = validated_data.pop('approvals', [])
        form_id = self.context.get('form')
        form = Form.objects.get(id=form_id)
        if form.is_anonymously_fillable:
            raise ValidationError({
                "error": "Cannot create approval levels for anonymous form."
            })
        organization = self.context.get('organization')
        approvals = self._create_approval(organization, approvals, form)
        return DummyObject(**instance)
