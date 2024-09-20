from django_q.tasks import async_task
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.utils import email
from irhrs.core.utils.common import get_today
from irhrs.core.constants.payroll import EMPLOYEE, PENDING, SUPERVISOR, FIRST, SECOND, THIRD, \
    REQUESTED, APPROVED
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.constants.organization import RESIGNATION_REQUEST_EMAIL, RESIGNATION_REQUEST_ACTION_EMAIL
from irhrs.core.constants.user import RESIGNED
from irhrs.core.mixins.serializers import ApprovalSettingValidationMixin, \
    DynamicFieldsModelSerializer
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import DummyObject
from irhrs.core.utils.email import send_notification_email
from irhrs.hris.api.v1.serializers.onboarding_offboarding import EmployeeSeparationTypeSerializer
from irhrs.hris.models import EmployeeSeparationType
from irhrs.hris.models.resignation import ResignationApprovalSetting, UserResignation, \
    UserResignationApproval, UserResignationHistory, HRApprovalUserResignation
from irhrs.hris.constants import resignation_email_permissions
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.organization.api.v1.serializers.common_org_serializer import OrganizationSerializerMixin
from irhrs.permission.constants.permissions import RESIGNATION_PERMISSION
from irhrs.reimbursement.utils.exceptions import AdvanceExpenseNotConfigured
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class ResignationApprovalSettingValidationSerializer(
    OrganizationSerializerMixin, DynamicFieldsModelSerializer
):
    class Meta:
        model = ResignationApprovalSetting
        fields = [
            'id', 'approve_by', 'supervisor_level', 'employee',
            'approval_level', 'organization'
        ]
        read_only_fields = ['approval_level', 'organization']
        extra_kwargs = {
            'employee': {'required': False},
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


class ResignationApprovalSettingSerializer(DynamicFieldsModelSerializer):
    approvals = serializers.SerializerMethodField()

    class Meta:
        model = ResignationApprovalSetting
        fields = ('approvals', )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'post':
            fields['approvals'] = ResignationApprovalSettingValidationSerializer(many=True)
        return fields

    @staticmethod
    def get_approvals(obj):
        organization = obj.organization
        return ResignationApprovalSettingValidationSerializer(
           organization.resignation_setting.all(),
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

        if supervisor_list and len(supervisor_list) != len(set(supervisor_list)):
            raise ValidationError("Approval Setting got similar supervisor level.")
        return approvals

    def create(self, validated_data):
        instance = dict(validated_data)
        approvals = validated_data.pop('approvals', [])
        organization = self.context.get('organization')
        ResignationApprovalSetting.objects.filter(organization=organization).delete()
        for index, approval in enumerate(approvals, start=1):
            if approval.get('approve_by') == EMPLOYEE:
                _ = approval.pop('supervisor_level', None)
            else:
                approval['employee'] = None
            approval['organization'] = organization
            approval['approval_level'] = index
            ResignationApprovalSetting.objects.create(**approval)
            if approval['approve_by'] == EMPLOYEE:
                approval['supervisor'] = None
            approval['employee'] = approval.pop('employee', None)

        return DummyObject(**instance)


class UserResignationApprovalSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(
        fields=[
            'id', 'full_name', 'job_title', 'profile_picture', 'cover_picture',
            'organization', 'is_online', 'is_current',
        ]
    )

    class Meta:
        model = UserResignationApproval
        fields = 'id', 'user', 'status', 'role', 'level', 'remarks'


class UserResignationHistorySerializer(DynamicFieldsModelSerializer):
    actor = UserThinSerializer(fields=['id', 'full_name', 'profile_picture', 'cover_picture', 'organization', 'is_current',])

    class Meta:
        model = UserResignationHistory
        fields = ['actor', 'action', 'target', 'remarks', 'created_at']


class HRApprovalUserResignationSerializer(DynamicFieldsModelSerializer):
    separation_type = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeSeparationType.objects.filter(category=RESIGNED),
    )
    user = UserThinSerializer(
        source='created_by',
        fields=[
            'id', 'full_name', 'profile_picture', 'cover_picture',
            'organization', 'is_current','job_title', 'is_online', 'last_online'
        ],
        read_only=True
    )

    class Meta:
        model = HRApprovalUserResignation
        fields = ['separation_type', 'remarks', 'user', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        validated_data['resignation'] = self.context.get('resignation')
        return super().create(validated_data)

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['separation_type'] = EmployeeSeparationTypeSerializer(
                fields=["id", "title", "slug", "category"]
            )

        return fields


class UserResignationSerializer(DynamicFieldsModelSerializer):
    hr_approval = HRApprovalUserResignationSerializer(
        read_only=True
    )

    class Meta:
        model = UserResignation
        fields = [
            'id', 'employee', 'release_date', 'reason', 'remarks', 'status',
            'created_at', 'hr_approval'
        ]
        read_only_fields = ['employee', 'status', 'created_at']

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['employee'] = UserThinSerializer(
                fields=[
                    'id', 'full_name', 'profile_picture', 'cover_picture',
                    'organization', 'is_current', 'job_title', 'is_online', 'last_online'
                ]
            )
            fields['recipient'] = UserThinSerializer(
                fields=[
                    'id', 'full_name', 'profile_picture', 'cover_picture',
                    'organization', 'is_current', 'job_title', 'is_online', 'last_online'
                ]
            )
            fields['approvals'] = UserResignationApprovalSerializer(
                many=True,
                read_only=True
            )
            fields['history'] = UserResignationHistorySerializer(
                source='histories',
                many=True,
                read_only=True
            )
        return fields

    @cached_property
    def approvals(self):
        approvals = []
        approval_settings = ResignationApprovalSetting.objects.filter(
            organization=self.context['organization']
        ).order_by('approval_level')

        if not approval_settings:
            raise AdvanceExpenseNotConfigured(detail=_("Approval Levels not set."))

        for index, approval_setting in enumerate(approval_settings, start=1):
            if approval_setting.approve_by == EMPLOYEE:
                approvals.append({
                    "user": approval_setting.employee,
                    "status": PENDING,
                    "role": EMPLOYEE,
                    "level": index
                })
            elif approval_setting.approve_by == SUPERVISOR:
                supervisor_level = [0, FIRST, SECOND, THIRD].index(
                    approval_setting.supervisor_level)
                supervisor_authority = self.request.user.supervisors.filter(
                    authority_order=supervisor_level).first()

                if not supervisor_authority or supervisor_authority.supervisor == get_system_admin():
                    continue

                approvals.append({
                    "user": supervisor_authority.supervisor,
                    "status": PENDING,
                    "role": SUPERVISOR,
                    "level": index
                })

        return approvals

    @property
    def recipient(self):
        return self.approvals[0]['user'] if self.approvals else None

    def validate(self, attrs):
        attrs['approvals'] = self.approvals
        attrs['recipient'] = self.recipient
        employee = self.context.get('employee')
        organization = self.context.get('organization')
        attrs['employee'] = employee
        if organization and organization != employee.detail.organization:
            raise ValidationError({
                'detail': ['Invalid organization.']
            })

        if employee.resignation.filter(status__in=[REQUESTED, APPROVED]).exists():
            raise ValidationError({
                'detail': ['You have already submitted your resignation.']
            })
        return super().validate(attrs)

    def create(self, validated_data):
        approvals = validated_data.pop('approvals')
        instance = super().create(validated_data)

        organization = instance.employee.detail.organization
        text = f"{instance.employee.full_name} sent resignation request."

        if approvals:
            approvals_level = []
            for approval in approvals:
                approvals_level.append(
                    UserResignationApproval(resignation=instance, **approval)
                )

            if approvals_level:
                UserResignationApproval.objects.bulk_create(approvals_level)
        else:
            instance.status = APPROVED
            instance.save()
            text = f"Approval for resignation by {instance.employee.full_name} " \
                   f" awaits for the confirmation."
        if instance.recipient:
            # send mail

            recipient_objects = [
                user for user in
                get_users_list_from_permissions(
                    permission_list=resignation_email_permissions,
                    organization=self.context["organization"]
                )
            ]
            settings_enabled_recipients = list(
                filter(
                    lambda user: email.can_send_email(user, RESIGNATION_REQUEST_EMAIL),
                    recipient_objects
                ),
            )
            recipients = [user.email for user in settings_enabled_recipients]
            subject = "New resignation request."
            notification_text = f"{instance.employee.full_name} has sent resignation request."
            can_send_email = email.can_send_email(instance.recipient, RESIGNATION_REQUEST_EMAIL)
            if can_send_email:
                recipients.append(instance.recipient.email)
            if recipients:
                async_task(
                    send_notification_email,
                    recipients=list(set(recipients)),
                    subject=subject,
                    notification_text=text
                )

            add_notification(
                text=notification_text,
                recipient=instance.recipient,
                action=instance,
                actor=instance.employee,
                url='/user/resignation-request'
            )
        notify_organization(
            text=text,
            organization=organization,
            action=instance,
            actor=instance.employee,
            permissions=[RESIGNATION_PERMISSION],
            url=f'/admin/{organization.slug}/hris/resignation/request/?status={instance.status}'
        )
        UserResignationHistory.objects.create(
            request=instance,
            actor=instance.employee,
            remarks=instance.reason,
            action=REQUESTED
        )
        return instance
