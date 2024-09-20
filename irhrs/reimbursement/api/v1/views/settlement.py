# Django imports
from django.db.models import Q
from django_q.tasks import async_task
#Rest_framework imports
from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

# Projects current app imports
from irhrs.core.constants.payroll import APPROVED, DENIED, REQUESTED, PENDING
from irhrs.core.mixins.advance_salary_or_expense_mixin import \
    ApproveDenyCancelWithMultipleApproverViewSetMixin
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, GetStatisticsMixin, \
    ListCreateRetrieveViewSetMixin, CommonApproverViewSetMixin, OrganizationCommonsMixin
from irhrs.core.mixins.serializers import create_dummy_serializer
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.utils.email import send_email_as_per_settings
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.notification.utils import add_notification
from irhrs.permission.constants.permissions import ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION
from irhrs.permission.constants.permissions.hrs_permissions import OVERALL_REIMBURSEMENT_PERMISSION, REIMBURSEMENT_READ_ONLY_PERMISSION
from irhrs.reimbursement.api.v1.permissions import ExpenseSettlementPermission, \
    AdvanceExpenseRequestObjectPermission, \
    ExpenseSettlementIsTaxableEditPermission
from irhrs.reimbursement.api.v1.serializers.settlement import \
    ExpenseSettlementSerializer, SettlementOptionSerializer
from irhrs.reimbursement.constants import OTHER, TRAVEL, BUSINESS
from irhrs.reimbursement.models.settlement import ExpenseSettlement, \
    SettlementHistory
from irhrs.core.constants.organization import (
    ADVANCE_EXPENSES_SETTLEMENT_APPROVE_OR_DENY,
    ADVANCE_EXPENSES_SETTLEMENT_BY_HR,
    ADVANCE_EXPENSES_REQUEST_CANCELLED_BY_HR
)


class ExpenseSettlementViewSet(
    OrganizationMixin,
    OrganizationCommonsMixin,
    GetStatisticsMixin,
    ApproveDenyCancelWithMultipleApproverViewSetMixin,
    CommonApproverViewSetMixin,
    ListCreateRetrieveViewSetMixin
):
    """
    list :
    list all the Settlement request from employees.
    "stats":{
      "Requested":2,
      "Approved":0,
      "Denied":0,
      "Canceled":0,
      "All":2
   }

    ## Available Filter
        * created_at
        * from_date
        * to_date
        * type
        * status
        * employee

    Create:
    ## Creates an instance of Settlement Request
    {
        "id":8,
        "reason":"travelling",
        "description":"",
        "type":"Travel",
        "remark":"fdgfdsgsfdg",
        "created_at":"2022-01-06T17:27:08.113061+05:45",
        "total_amount":100.0,
        "currency":"USD",
        "status":"Requested",
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
    }

    Retrive:
    ## Display an instance of Settlement request with all fields.
    {
    "count":2,
    "next":null,
    "previous":null,
    "results":[
        {
            "id":8,
            "reason":"travelling",
            "description":"",
            "type":"Travel",
            "remark":"fdgfdsgsfdg",
            "created_at":"2022-01-06T17:27:08.113061+05:45",
            "total_amount":100.0,
            "currency":"USD",
            "status":"Requested",
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
                "id":27,
                "full_name":"Pratima Dhungel",
                "profile_picture":"http://localhost:8000/media/cache/36/81/3681785b00432242e12fee385cc13eea.png",
                "cover_picture":"http://localhost:8000/media/cache/11/d3/11d3da262c5fb78610e7f4aab2e2e1e7.png",
                "job_title":"Senior Quality Assurance Engineer",
                "organization":{
                    "name":"Aayu Bank Pvt. Ltd.",
                    "abbreviation":"ABPL",
                    "slug":"aayu-bank-pvt-ltd"
                },
                "is_online":false
                }
            ],
            "has_advance_expense":false,
            "add_signature":true,
            "travel_report":"http://localhost:8000/media/uploads/expensesettlement/b84d489d26c343a094d3467f7fb2b69c.jpg",
            "is_taxable":false
        },
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
                "id":27,
                "full_name":"Pratima Dhungel",
                "profile_picture":"http://localhost:8000/media/cache/36/81/3681785b00432242e12fee385cc13eea.png",
                "cover_picture":"http://localhost:8000/media/cache/11/d3/11d3da262c5fb78610e7f4aab2e2e1e7.png",
                "job_title":"Senior Quality Assurance Engineer",
                "organization":{
                    "name":"Aayu Bank Pvt. Ltd.",
                    "abbreviation":"ABPL",
                    "slug":"aayu-bank-pvt-ltd"
                },
                "is_online":false
                }
            ],
            "has_advance_expense":true,
            "add_signature":true,
            "travel_report":"http://localhost:8000/media/uploads/expensesettlement/d0b1374432624e97908cb78b2c55c841.jpg",
            "is_taxable":false
        }
    ],
    "stats":{
        "Requested":2,
        "Approved":0,
        "Denied":0,
        "Canceled":0,
        "All":2
    }
    }
    """
    queryset = ExpenseSettlement.objects.all()
    serializer_class = ExpenseSettlementSerializer
    permission_classes = [ExpenseSettlementPermission, AdvanceExpenseRequestObjectPermission]
    filter_backends = [FilterMapBackend, SearchFilter, OrderingFilterMap]
    filter_map = {
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
        'title': 'reason',
        'status': 'status',
        'employee': ('employee__first_name', 'employee__middle_name', 'employee__last_name',)
    }
    search_fields = [
        'reason', 'employee__first_name', 'employee__middle_name',
        'employee__last_name'
    ]
    statistics_field = 'status'
    history_model = SettlementHistory
    notification_for = 'expense settlement'
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
        ).distinct()

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs.update({
                'exclude_fields': ['detail', 'documents', 'approvals', 'history',
                                   'option', 'advance_expense']
            })
        return super().get_serializer(*args, **kwargs)

    def get_type(self, *args, **kwargs):
        instance = self.get_object()
        return f'{instance.type} Expense Report' if instance else \
            super().get_type(*args, **kwargs)

    def get_notification_url_for_organization(self, organization=None):
        return f'/admin/{organization.slug}/expense-management/settle-request'

    def get_notification_url_for_user(self, user=None):
        return '/user/expense-management/settle-expense'

    def get_notification_url_for_approver(self, user=None):
        return '/user/expense-management/request/settlement'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        expense_type = self.request.query_params.get('expense_type', OTHER)
        context['expense_type'] = expense_type.title()
        return context

    def get_additional_validated_fields(self):
        return {
            "is_taxable": self.request.data.get("is_taxable")
        }
    def get_serializer_class(self):
        if self.action == 'approve':
            RemarksRequiredSerializer = create_dummy_serializer({
                'remarks': serializers.CharField(max_length=600, allow_blank=False),
                'is_taxable': serializers.BooleanField(required=False),
                'add_signature': serializers.BooleanField(required=False)
            })
            return RemarksRequiredSerializer
        return super().get_serializer_class()

    def post_approve(self, instance):
        created_by = instance.created_by
        if instance.status == REQUESTED:
            subject = f"{instance.created_by} has request for advance settlement"
            email_text=(
                f"{instance.modified_by} has forwarded expense settlement request by {instance.created_by}"
            )
            async_task(
                send_email_as_per_settings,
                instance.recipient.all(),
                subject,
                email_text,
                ADVANCE_EXPENSES_SETTLEMENT_APPROVE_OR_DENY
            )

        if instance.status == APPROVED:
            if instance.advance_expense and (instance.advance_expense.advance_amount < instance.total_amount):
                subject = f"Expense settlement requested by {instance.created_by} requires settlement confirmation"
                email_text=(
                    f"Expense settlement requested by {instance.created_by} has been approved and requires settlement confirmation."
                )
                permission_list = [ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION,OVERALL_REIMBURSEMENT_PERMISSION,REIMBURSEMENT_READ_ONLY_PERMISSION]
                user_list = get_users_list_from_permissions(permission_list,self.organization)
                async_task(
                    send_email_as_per_settings,
                    user_list,
                    subject,
                    email_text,
                    ADVANCE_EXPENSES_SETTLEMENT_APPROVE_OR_DENY
                )

        if not instance.approvals.filter(status=PENDING).exists():
            subject = f"Your request for expense settlement has been settled."
            email_text=(
                f"{instance.modified_by} has settled your expense settlement request"
            )
            async_task(
                send_email_as_per_settings,
                created_by,
                subject,
                email_text,
                ADVANCE_EXPENSES_SETTLEMENT_BY_HR
            )


    def post_deny(self, instance):
        subject = f"Your request for expense settlement is Denied"
        email_text=(
            f"{instance.modified_by} has declined your expense settlement request."
        )
        async_task(
            send_email_as_per_settings,
            instance.created_by,
            subject,
            email_text,
            ADVANCE_EXPENSES_SETTLEMENT_APPROVE_OR_DENY
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

    @action(
        detail=True,
        methods=['POST'],
        url_path='option',
        url_name='option',
        serializer_class=SettlementOptionSerializer
    )
    def settlement_option(self, request, *args, **kwargs):
        settlement = self.get_object()
        if hasattr(settlement, 'option'):
            return Response(
                {'detail': 'This settlement has already been settled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not settlement.advance_expense:
            return Response(
                {'detail': 'There is no any advance expense associated with this settlement .'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if settlement.status != APPROVED:
            return Response(
                {'detail': 'This settlement has not been approved by all approval levels.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.update({
            'settle': settlement
        })
        serializer.save()

        # notification for user about settlement
        add_notification(
            text=f"Your settlement request for advance expense has been settled "
                 f"by {request.user.full_name}",
            actor=request.user,
            action=settlement,
            recipient=settlement.employee,
            url=f"/user/expense-management/settle-expense"
        )
        subject = f"Your expense settlement request has been setttled."
        email_text=(
            f"{request.user.full_name} has settled your expense settlement request"
        )
        async_task(
            send_email_as_per_settings,
            settlement.created_by,
            subject,
            email_text,
            ADVANCE_EXPENSES_SETTLEMENT_APPROVE_OR_DENY
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        expense = self.get_object()
        if self.request.query_params.get('expense_type', OTHER).title() != expense.type:
            return Response(
                {
                    'detail': 'Invalid query params supplied. '
                              f'\'settle_type\' must be \'{expense.type}\' '
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().retrieve(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['POST'],
        url_path='is-taxable',
        url_name='is-taxable',
        permission_classes=[ExpenseSettlementIsTaxableEditPermission]
    )
    def is_taxable(self, request, *args, **kwargs):
        if not request.query_params.get('as') == 'hr':
            raise PermissionDenied
        self.check_permissions(request)
        expense_settlement = self.get_object()
        is_taxable_data = request.data.get('is_taxable')
        expense_settlement.is_taxable = is_taxable_data
        expense_settlement.save()
        return Response(request.data, status=status.HTTP_200_OK)

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

    def __get_pending_exists(self, instance):
        return self.get_queryset().exclude(id=instance.id).filter(
            employee=instance.employee,
            created_at__lte=instance.created_at,
            status=REQUESTED
        ).exists()

    def perform_pre_approval_validation(self, instance):
        is_taxable = instance.validated_data.get('is_taxable')
        if is_taxable and instance.type in [TRAVEL, BUSINESS]:
            raise serializers.ValidationError({
                'is_taxable': [
                    'Business and Travel expense type cannot be taxable.'
                ]
            })
        pending = self.__get_pending_exists(instance)
        if pending:
            raise serializers.ValidationError({
                'non_field_errors': [
                    'Can not approve this request.'
                    ' Other requests sent prior to this need to be acted first.'
                ]
            })

    def perform_pre_denial_validation(self, instance):
        pending = self.__get_pending_exists(instance)
        if pending:
            raise serializers.ValidationError({
                'non_field_errors': [
                    'Can not deny this request.'
                    ' Other requests sent prior to this need to be acted first.'
                ]
            })

    def _approve_action(self, approval, instance, remarks, user, signature,
                        additional_fields):
        approval.status = APPROVED
        approval.add_signature = signature
        approval.acted_by = user
        for key, val in additional_fields.items():
            if key == "is_taxable":
                if val is not None:
                    approval.settle.is_taxable = val
                    approval.settle.save()
            else:
                setattr(approval, key, val)
        approval.save()
        self.generate_history(instance, user=user, remarks=remarks, action=APPROVED)
        next_approval = instance.approvals.filter(status=PENDING).order_by('level').first()
        return next_approval
