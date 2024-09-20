# Django imports
from django.db.models import Q, Exists, OuterRef
from django_q.tasks import async_task
# RestFramework imports
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from irhrs.attendance.api.v1.serializers.travel_attendance import create_travel_attendance
from irhrs.attendance.constants import FULL_DAY
from irhrs.attendance.models.travel_attendance import(
    TravelAttendanceRequest, TravelAttendanceRequestHistory, TravelAttendanceSetting
)
from django.utils.functional import cached_property
from irhrs.attendance.utils.travel_attendance import calculate_balance

# Project current app imports
from irhrs.core.constants.payroll import (
    APPROVED, DENIED,
    CANCELED, REQUESTED
)
from irhrs.core.mixins.advance_salary_or_expense_mixin import \
    ApproveDenyCancelWithMultipleApproverViewSetMixin
from irhrs.core.mixins.viewset_mixins import ListCreateDestroyViewSetMixin, \
    AdvanceExpenseRequestMixin, OrganizationMixin, \
    GetStatisticsMixin, CommonApproverViewSetMixin, \
    ListCreateRetrieveUpdateViewSetMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.email import send_email_as_per_settings
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.permission.constants.permissions import ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION
from irhrs.reimbursement.api.v1.permissions import AdvanceExpenseRequestPermission, \
    AdvanceExpenseRequestObjectPermission
from irhrs.reimbursement.api.v1.serializers.reimbursement import \
    AdvanceExpenseRequestSerializer, AdvanceExpenseRequestDocumentsSerializer, \
    AdvanceAmountUpdateSerializer, AdvanceExpenseCancelHistorySerializer
from irhrs.reimbursement.constants import OTHER
from irhrs.reimbursement.models import ExpenseSettlement
from irhrs.reimbursement.models.reimbursement import AdvanceExpenseRequest, \
    AdvanceExpenseRequestDocuments, AdvanceExpenseRequestHistory, AdvanceExpenseCancelHistory
from irhrs.core.constants.payroll import PENDING
from irhrs.core.constants.organization import ADVANCE_EXPENSE_SETTING_APPROVE_OR_DENY, \
    ADVANCE_EXPENSES_REQUEST_CANCELLED_BY_HR


class AdvanceExpenseRequestViewSet(
    OrganizationMixin, GetStatisticsMixin,
    ApproveDenyCancelWithMultipleApproverViewSetMixin,
    CommonApproverViewSetMixin,
    ListCreateRetrieveUpdateViewSetMixin
):
    """
    ## Available Filters
    * reason
    * from_date
    * to_date
    * type
    * status
    * employee

    list:

    ## lists all the AdvanceExpenseRequest from the employees.

    {
        "count":1,
        "next":null,
        "previous":null,
        "results":[
            {
                "id":15,
                "reason":"travelling",
                "advance_code":1,
                "type":"Travel",
                "description":"",
                "remarks":"",
                "created_at":"2022-01-06T12:17:35.019083+05:45",
                "currency":"USD",
                "total_amount":289.0,
                "status":"Requested",
                "advance_amount":216.75,
                "employee":{
                    "id":1,
                    "full_name":"Rajesh Shrestha",
                    "profile_picture":"http://localhost:8000/media/cache/77/88/77881708789d9424a6705f4157f682e1.png",
                    "cover_picture":"http://localhost:8000/media/cache/df/6f/df6f4095dc5f1a22133855323a7683d0.png",
                    "organization":{
                    "name":"Aayu Bank Pvt. Ltd.",
                    "abbreviation":"ABPL",
                    "slug":"aayu-bank-pvt-ltd"
                    },
                    "job_title":"Executive Director",
                    "is_online":true,
                    "signature":"http://localhost:8000/media/uploads/changerequestdetails/c0c7e54aba654cbdb7ec7f4803edba2a.png"
                },
                "recipient":[
                    {
                    "id":1,
                    "full_name":"Rajesh Shrestha",
                    "profile_picture":"http://localhost:8000/media/cache/77/88/77881708789d9424a6705f4157f682e1.png",
                    "cover_picture":"http://localhost:8000/media/cache/df/6f/df6f4095dc5f1a22133855323a7683d0.png",
                    "job_title":"Executive Director",
                    "is_online":true
                    }
                ],
                "add_signature":true,
                "settlement_exists":false
            }
            ],
            "stats":{
                "Requested":1,
                "Approved":0,
                "Denied":0,
                "Canceled":1,
                "All":2
            }
        }

    create:
    Creates a new AdvanceExpenseRequest Instance.

    data

        {
            "id":16,
            "reason":"Client visit",
            "advance_code":2,
            "type":"Travel",
            "associates":[

            ],
            "description":"",
            "remarks":"",
            "created_at":"2022-01-06T14:24:46.373999+05:45",
            "currency":"USD",
            "total_amount":5000.0,
            "status":"Requested",
            "advance_amount":3750.0,
            "documents":[]
        }

    retrive:
    ## Displays an instance of AdvanceExpenseRequest with all fields.

        {
         "id":16,
         "reason":"Client visit",
         "advance_code":2,
         "type":"Travel",
         "description":"",
         "remarks":"",
         "created_at":"2022-01-06T14:24:46.373999+05:45",
         "currency":"USD",
         "total_amount":5000.0,
         "status":"Requested",
         "advance_amount":3750.0,
         "employee":{
            "id":1,
            "full_name":"Rajesh Shrestha",
            "profile_picture":"http://localhost:8000/media/cache/77/88/77881708789d9424a6705f4157f682e1.png",
            "cover_picture":"http://localhost:8000/media/cache/df/6f/df6f4095dc5f1a22133855323a7683d0.png",
            "organization":{
               "name":"Aayu Bank Pvt. Ltd.",
               "abbreviation":"ABPL",
               "slug":"aayu-bank-pvt-ltd"
            },
            "job_title":"Executive Director",
            "is_online":true,
            "signature":"http://localhost:8000/media/uploads/changerequestdetails/c0c7e54aba654cbdb7ec7f4803edba2a.png"
         },
         "recipient":[
            {
               "id":1,
               "full_name":"Rajesh Shrestha",
               "profile_picture":"http://localhost:8000/media/cache/77/88/77881708789d9424a6705f4157f682e1.png",
               "cover_picture":"http://localhost:8000/media/cache/df/6f/df6f4095dc5f1a22133855323a7683d0.png",
               "job_title":"Executive Director",
               "is_online":true
            }
         ],
         "add_signature":true,
         "settlement_exists":false
        }

    Update :
    Updating Advance Expenses amount:
    {
       "id":7,
        "reason":"Travelling",
        "description":"",
        "type":"Travel",
        "remark":"dgsdsfd",
        "created_at":"2022-01-06T17:04:46.325988+05:45",
        "total_amount":5000.0,
        "currency":"USD",
        "status":"Requested",
     }

    Delete:
    Deletes a Advance Expenses request instance from provided request ID.

    """
    queryset = AdvanceExpenseRequest.objects.all()
    serializer_class = AdvanceExpenseRequestSerializer
    permission_classes = [AdvanceExpenseRequestObjectPermission, AdvanceExpenseRequestPermission]
    filter_backends = [FilterMapBackend, SearchFilter, OrderingFilterMap]
    filter_map = {
        'reason': ('reason', 'icontains'),
        'created_at': ('created_at', 'date'),
        'from_date': 'created_at__date__gte',
        'to_date': 'created_at__date__lte',
        'type': 'type',
        'status': 'status',
        'employee': 'employee'
    }
    ordering_fields_map = {
        'type': 'type',
        'created_at': 'created_at',
        'total_amount': 'total_amount',
        'reason': 'reason',
        'status': 'status',
        'employee': ('employee__first_name', 'employee__middle_name', 'employee__last_name',)
    }
    search_fields = [
        'reason', 'employee__first_name', 'employee__middle_name',
        'employee__last_name'
    ]
    statistics_field = 'status'
    history_model = AdvanceExpenseRequestHistory
    notification_for = 'advance expense'
    permission_for_hr = [ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION]

    def get_queryset(self):
        base_qs = self.queryset.filter(employee__detail__organization=self.organization)
        if self.mode == 'hr':
            queryset = base_qs
        elif self.mode == 'approver':
            # filters request for current approver only
            queryset = self.queryset.filter(
                Q(recipient=self.request.user) |
                Q(approvals__user=self.request.user,
                  approvals__status__in=[APPROVED, DENIED])
            )
        else:
            queryset = base_qs.filter(employee=self.request.user)
        return queryset.select_related(
            'employee', 'employee__detail', 'employee__detail__organization',
            'employee__detail__job_title',
        ).annotate(
            settlement_exists=Exists(
                ExpenseSettlement.objects.filter(
                    advance_expense=OuterRef('pk')
                ).exclude(
                    status__in=[DENIED, CANCELED]
                )
            ),
            cancel_request_exists=Exists(
                AdvanceExpenseCancelHistory.objects.filter(
                    advance_expense=OuterRef('pk')
                ).exclude(
                    status__in=[DENIED, CANCELED]
                )
            )
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'cancel-approved':
            return AdvanceExpenseCancelHistorySerializer
        elif self.request.method.lower() in ['put', 'patch']:
            return AdvanceAmountUpdateSerializer
        return super().get_serializer_class()

    def get_serializer(self, *args, **kwargs):
        if self.action in ['list']:
            kwargs.update({
                'exclude_fields': [
                    'detail', 'documents', 'approvals', 'history',
                    'associates'
                ]
            })
        return super().get_serializer(*args, **kwargs)

    def get_notification_url_for_organization(self, organization=None):
        return f'/admin/{organization.slug}/expense-management/request'

    def get_notification_url_for_user(self, user=None):
        return '/user/expense-management/request-advance'

    def get_notification_url_for_approver(self, user=None):
        return '/user/expense-management/request/expense'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        expense_type = self.request.query_params.get('expense_type', OTHER)
        context['expense_type'] = expense_type.title()
        context['organization'] = self.organization
        context['travel_setting'] = self.travel_setting
        return context

    @cached_property
    def travel_setting(self):
        return TravelAttendanceSetting.objects.filter(
            organization = self.organization
        ).first()

    def get_type(self, *args, **kwargs):
        text_type = {
            'Travel': f'Travel Authorization and Advance Request Form'
        }
        instance = self.get_object()
        return text_type.get(instance.type, 'advance expense request')

    def get_organization_text(self, employee):
        return f"Approval for {self.get_type()} " \
               f"by {employee.full_name} has been completed."

    def retrieve(self, request, *args, **kwargs):
        expense = self.get_object()
        if self.request.query_params.get('expense_type', OTHER).title() != expense.type:
            return Response(
                {
                    'detail': 'Invalid query params supplied. '
                              f'\'expense_type\' must be \'{expense.type}\' '
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().retrieve(request, *args, **kwargs)

    def check_permissions(self, request):
        if self.request.user and self.request.user.is_authenticated:
            self.validate_hr_action(request)
        super().check_permissions(request)

    def validate_hr_action(self, request):
        if request.query_params.get('as') == 'hr':
            if not validate_permissions(
                request.user.get_hrs_permissions(self.get_organization()),
                *self.permission_for_hr
            ):
                raise PermissionDenied

    def post_approve(self, instance):
        remarks = self.request.data.get('remarks')
        if len(remarks) > 256:
            raise ValidationError({'error': "Remarks cannot be more than 255 characters."})

        travel_request=getattr(instance, 'travel_request_from_advance', None)
        employee = instance.employee if hasattr(instance, 'employee') else instance.created_by
        if instance.status == 'Approved' and travel_request:
            balance = calculate_balance(
                employee, travel_request.start, travel_request.end, self.travel_setting, part=FULL_DAY
            )
            _travel_request = TravelAttendanceRequest.objects.create(
                status=APPROVED,
                start=travel_request.start,
                end=travel_request.end,
                user=instance.employee,
                recipient=self.request.user,
                balance=balance,
                end_time=travel_request.end_time,
                start_time=travel_request.start_time
            )
            TravelAttendanceRequestHistory.objects.create(
                travel_attendance=_travel_request,
                status=APPROVED,
                action_performed_to=instance.employee,
                remarks=remarks
            )
            create_travel_attendance(_travel_request.id)

        if instance.status == REQUESTED:
            subject = f"{instance.created_by} has requested for advance expenses"
            email_text=(
                f"{instance.modified_by} has forwarded advance expense request requested by {instance.created_by}"
            )
            async_task(
                send_email_as_per_settings,
                instance.recipient.all(),
                subject,
                email_text,
                ADVANCE_EXPENSE_SETTING_APPROVE_OR_DENY
            )
        if not instance.approvals.filter(status=PENDING).exists():
            subject = f"Your requeste for advance expense has been approved"
            email_text=(
                f"{instance.modified_by} has approved your advance expense request"
            )
            async_task(
                send_email_as_per_settings,
                instance.created_by,
                subject,
                email_text,
                ADVANCE_EXPENSE_SETTING_APPROVE_OR_DENY
            )



    def post_deny(self, instance):
        subject = f"Your request for advance expenses has been Denied"
        email_text=(
            f"{instance.modified_by} has declined your advance expense request."
        )
        async_task(
            send_email_as_per_settings,
            instance.created_by,
            subject,
            email_text,
            ADVANCE_EXPENSE_SETTING_APPROVE_OR_DENY
        )

    def post_cancel(self, instance):
        if instance.created_by == instance.modified_by:
            return
        subject = f"Your request for advance expenses has been Canceled"
        email_text=(
            f"Your advance expense request has been canceled by {instance.modified_by}"
        )
        async_task(
            send_email_as_per_settings,
            instance.created_by,
            subject,
            email_text,
            ADVANCE_EXPENSES_REQUEST_CANCELLED_BY_HR
        )

    @action(detail=True, methods=["post"], url_path="cancel-approved")
    def cancel_approved(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != APPROVED:
            raise ValidationError({
                'detail': f"Only approved expense requests can be deleted."
            })
        ctx = self.get_serializer_context()

        ctx.update({
            'advance-expense-request': instance
        })
        if self.mode == 'approver':
            if not validate_permissions(
                self.request.user.get_hrs_permissions(
                    self.get_organization()
                ),
                ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION
            ):
                raise self.permission_denied(self.request)
            ctx.update({'mode': 'approver'})

        ser = AdvanceExpenseCancelHistorySerializer(
            context=ctx,
            data=request.data
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        instance.recipient.set(instance.approvals.first().user.all())
        return Response(
            status=status.HTTP_200_OK,
            data="Requested for delete"
        )


class AdvanceExpenseRequestDocumentsViewSet(
    OrganizationMixin,
    AdvanceExpenseRequestMixin,
    ListCreateDestroyViewSetMixin
):
    queryset = AdvanceExpenseRequestDocuments.objects.all()
    serializer_class = AdvanceExpenseRequestDocumentsSerializer
