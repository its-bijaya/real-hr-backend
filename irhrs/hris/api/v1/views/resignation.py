from django_q.tasks import async_task
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from irhrs.core.utils import email
from irhrs.core.constants.payroll import APPROVED, REQUESTED, PENDING
from irhrs.core.constants.organization import RESIGNATION_REQUEST_ACTION_EMAIL
from irhrs.core.utils.email import send_notification_email
from irhrs.core.mixins.advance_salary_or_expense_mixin import ApproveDenyCancelViewSetMixin
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, OrganizationCommonsMixin, \
    CreateListModelMixin, ApprovalSettingViewSetMixin, ListCreateViewSetMixin, GetStatisticsMixin, \
    ListCreateRetrieveViewSetMixin, CommonApproverViewSetMixin
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.hris.api.v1.permissions import UserResignationObjectPermission
from irhrs.hris.api.v1.serializers.onboarding_offboarding import EmployeeSeparationSerializer
from irhrs.hris.constants import resignation_email_permissions
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.hris.api.v1.serializers.resignation import ResignationApprovalSettingSerializer, \
    UserResignationSerializer, HRApprovalUserResignationSerializer, \
    ResignationApprovalSettingValidationSerializer
from irhrs.hris.models import EmployeeSeparation
from irhrs.hris.models.resignation import ResignationApprovalSetting, UserResignation, \
    UserResignationHistory
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.permission.constants.permissions import RESIGNATION_PERMISSION, \
    HAS_PERMISSION_FROM_METHOD
from irhrs.permission.permission_classes import permission_factory


class ResignationApprovalSettingViewSet(
    OrganizationMixin,
    OrganizationCommonsMixin,
    CreateListModelMixin,
    ListCreateViewSetMixin
):
    serializer_class = ResignationApprovalSettingSerializer
    permission_classes = [
        permission_factory.build_permission(
            'ResignationPermission',
            allowed_to=[RESIGNATION_PERMISSION]
        )
    ]
    queryset = ResignationApprovalSetting.objects.all()

    def get_queryset(self):
        return super().get_queryset().order_by('approval_level')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(organization=self.get_organization())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ResignationApprovalSettingValidationSerializer(
                            queryset,
                            many=True
                        )
            return self.get_paginated_response(serializer.data)

        serializer = ResignationApprovalSettingValidationSerializer(
            queryset,
            many=True
        )
        return Response(serializer.data)


class UserResignationViewSet(
    OrganizationMixin, GetStatisticsMixin, ApproveDenyCancelViewSetMixin,
    CommonApproverViewSetMixin, ListCreateRetrieveViewSetMixin
):
    """
    User Resignation Flow :

    1. To create resignation:

    url: /api/v1/hris/{org_slug}/resignation/

    method: post

    data:

        {
            "release_date": "2020-01-01",
            "reason": "String",
            "remarks": "String"
        }

    2. To list resignation:

    url: /api/v1/hris/{org_slug}/resignation/

    method: get

    data:

        {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "employee": {user thin serializer},
                    "release_date": "2020-01-01",
                    "reason": "kks",
                    "remarks": "ksljkdas",
                    "status": "Requested",
                    "recipient": {user thin serializer}
                }
            ],
            "stats": {
                "Requested": 1,
                "Approved": 0,
                "Denied": 0,
                "Canceled": 0,
                "All": 1
            }
        }

    3. To retrieve resignation:

    Url: /api/v1/hris/{org_slug}/resignation/{resignation_id}

    Method: get

    Data:

        {
            "id": 1,
            "employee": {user thin serializer},
            "release_date": "2020-01-01",
            "reason": "kks",
            "remarks": "ksljkdas",
            "status": "Approved",
            "recipient": {user thin serializer},
            "approvals": [
                {
                    "id": 1,
                    "user": {user thin serizlier},
                        "is_online": true
                    },
                    "status": "Approved",
                    "role": "Supervisor",
                    "level": 1,
                    "remarks": ""
                }
            ],
            "history": [
                {
                    "actor": {user thin serializer},
                    "action": "Approved",
                    "target": "",
                    "remarks": "asdasd",
                    "created_at": "2020-05-27T11:20:04.353432+05:45"
                }
            ],
            "hr_approval": {
                "separation_type": {
                    "title": "Resigned",
                    "slug": "resigned",
                    "category": "Resigned",
                    "id": 74
                },
                "remark": "nsdinasdsadsd",
                "user": {user thin serializer},
                "created_at": "2020-05-27T05:39:50.360220Z"
            }
        }

    """
    queryset = UserResignation.objects.all()
    serializer_class = UserResignationSerializer
    permission_classes = [
        permission_factory.build_permission(
            'UserResignationPermission',
            allowed_to=[HAS_PERMISSION_FROM_METHOD],
            actions={
                'approve_by_hr': [RESIGNATION_PERMISSION]
            }
        ),
        UserResignationObjectPermission,
    ]
    filter_backends = [FilterMapBackend, SearchFilter, OrderingFilterMap]
    filter_map = {
        'release_date': 'release_date',
        'status': 'status',
    }
    search_fields = ['employee__first_name', 'employee__middle_name', 'employee__last_name']
    ordering_fields_map = {
        'created_at': 'created_at',
        'released_date': 'released_date',
        'employee': ('employee__first_name', 'employee__middle_name', 'employee__last_name')
    }
    statistics_field = 'status'
    history_model = UserResignationHistory
    notification_for = 'resignation'
    permission_for_hr = [RESIGNATION_PERMISSION]
    send_hr_notification = True

    def get_queryset(self):
        return super().get_queryset().select_related(
            'employee', 'employee__detail', 'employee__detail__organization',
            'employee__detail__job_title', 'hr_approval', 'recipient', 'recipient__detail',
            'recipient__detail__organization', 'recipient__detail__job_title',
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        context['employee'] = self.request.user
        return context

    def get_notification_url_for_organization(self, organization=None):
        return f'/admin/{organization.slug}/hris/resignation/request'

    def get_notification_url_for_user(self, user=None):
        return f'/user/resignation/{user.id}'

    def get_notification_url_for_approver(self, user=None):
        return f'/user/resignation-request'

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs.update({
                'exclude_fields': ['history', 'approvals']
            })
        return super().get_serializer(*args, **kwargs)

    def post_approve(self, instance):
        recipients = []
        subject = "Resignation approved."
        email_body=f"{instance.recipient.full_name} has approved your resignation request."
        can_send_email = email.can_send_email(instance.employee, RESIGNATION_REQUEST_ACTION_EMAIL)
        if can_send_email:
            recipients.append(instance.employee.email)

        recipients = list(set(recipients) - set([instance.recipient.email]))

        if recipients:
            async_task(
                send_notification_email,
                recipients=recipients,
                subject=subject,
                notification_text=email_body
            )

        # email to HR and other approvers
        next_approval = instance.approvals.filter(status=PENDING).order_by('level').first()
        approvers = [next_approval.user.email] if next_approval else []
        recipient_objects = [
            user for user in
            get_users_list_from_permissions(
                permission_list=resignation_email_permissions,
                organization=self.organization
            )
        ]
        settings_enabled_recipients = list(
            filter(
                lambda user: email.can_send_email(user, RESIGNATION_REQUEST_ACTION_EMAIL),
                recipient_objects
            ),
        )
        recipients = [user.email for user in settings_enabled_recipients] + approvers
        subject = "Resignation request was approved."
        email_body=f"{instance.recipient.full_name} has approved resignation request for {instance.employee.full_name}."
        recipients = list(set(recipients) - set([instance.recipient.email]))
        if recipients:
            async_task(
                send_notification_email,
                recipients=recipients,
                subject=subject,
                notification_text=email_body
            )

    def post_deny(self, instance):
        # email to user
        recipients = []
        subject = "Resignation request denied."
        email_body=f"{instance.recipient.full_name} has denied your resignation request."
        can_send_email = email.can_send_email(instance.employee, RESIGNATION_REQUEST_ACTION_EMAIL)
        if can_send_email:
            recipients.append(instance.employee.email)
        recipients = list(set(recipients) - set([instance.recipient.email]))
        if recipients:
            async_task(
                send_notification_email,
                recipients=recipients,
                subject=subject,
                notification_text=email_body
            )

        # email to HR
        approvers = [
            approver.user.email for approver in
            instance.approvals.filter(status=APPROVED)
        ]
        recipient_objects = [
            user for user in
            get_users_list_from_permissions(
                permission_list=resignation_email_permissions,
                organization=self.organization
            )
        ]
        settings_enabled_recipients = list(
            filter(
                lambda user: email.can_send_email(user, RESIGNATION_REQUEST_ACTION_EMAIL),
                recipient_objects
            ),
        )
        recipients = [user.email for user in settings_enabled_recipients] + approvers
        # to all recipient except the one who denied the request
        recipients = list(set(recipients) - set([instance.recipient.email]))
        subject = "Resignation request denied."
        email_body=f"{instance.recipient.full_name} has denied resignation request for {instance.employee.full_name}."
        if recipients:
            async_task(
                send_notification_email,
                recipients=recipients,
                subject=subject,
                notification_text=email_body
            )

    @action(
        detail=True,
        methods=['POST'],
        serializer_class=HRApprovalUserResignationSerializer,
        url_path='approve/final'
    )
    def approve_by_hr(self, request, *args, **kwargs):
        resignation = self.get_object()
        context = self.get_serializer_context()
        context['resignation'] = resignation
        if not resignation:
            return Response({
                'detail': 'User Resignation not found.'
            })
        if resignation and hasattr(resignation, 'hr_approval'):
            return Response({
                'detail': 'User Resignation has already been approved by hr.'
            })
        if resignation.status != APPROVED:
            return Response({
                'detail': ['This resignation has not been approved by all the approval levels.']
            })
        serializer = self.serializer_class(
            data=request.data,
            context=context
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        employee_separation = EmployeeSeparation(
            employee=resignation.employee,
            separation_type=instance.separation_type,
            parted_date=resignation.created_at.date(),
            release_date=resignation.release_date,
            effective_date=instance.created_at.date(),
            remarks=instance.remarks
        )
        employee_separation.save()
        offboarding = EmployeeSeparationSerializer(
            employee_separation,
            fields=[
                'id', 'employee', 'separation_type', 'parted_date',
                'release_date', 'effective_date', 'remarks'
            ],
            context=context
        ).data
        add_notification(
            text="Your resignation request is carried to employee separation process.",
            recipient=resignation.employee,
            action=resignation,
            actor=request.user,
            url=f'/user/resignation/{resignation.employee.id}'
        )

        organization = resignation.employee.detail.organization
        notify_organization(
            text=f"Resignation request for {resignation.employee.full_name}"
                 f" has been carried to employee separation process.",
            organization=organization,
            action=instance,
            actor=request.user,
            permissions=[RESIGNATION_PERMISSION],
            url=self.get_notification_url_for_organization(organization=organization)
        )
        UserResignationHistory.objects.create(
            request=resignation,
            actor=instance.created_by,
            remarks=instance.remarks,
            action=APPROVED
        )
        return Response(offboarding)

    def options(self, request, *args, **kwargs):
        options_response = super().options(request, *args, **kwargs)
        can_resign = False
        organization = self.get_organization()
        if organization:
            can_resign = ResignationApprovalSetting.exists_for_organization(organization)
        options_response.data.update({'can_resign': can_resign})
        return options_response
