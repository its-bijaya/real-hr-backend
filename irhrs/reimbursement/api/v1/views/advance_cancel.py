from django.db.models import Exists, OuterRef, Q
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from irhrs.core.mixins.advance_salary_or_expense_mixin import \
    ActionOnExpenseCancelRequestWithMultipleApproverViewSetMixin
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, GetStatisticsMixin, \
    CommonApproverViewSetMixin, ListCreateRetrieveUpdateViewSetMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.core.constants.payroll import APPROVED, DENIED, CANCELED
from irhrs.permission.constants.permissions import ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION
from irhrs.reimbursement.api.v1.permissions import AdvanceExpenseRequestObjectPermission, \
    AdvanceExpenseRequestPermission
from irhrs.reimbursement.api.v1.serializers.reimbursement import \
    AdvanceExpenseCancelHistorySerializer
from irhrs.reimbursement.constants import OTHER, TRAVEL
from irhrs.reimbursement.models.reimbursement import AdvanceExpenseCancelHistory, \
    AdvanceExpenseRequestHistory


class AdvanceExpenseCancelRequestViewSet(
    OrganizationMixin, GetStatisticsMixin,
    ActionOnExpenseCancelRequestWithMultipleApproverViewSetMixin,
    CommonApproverViewSetMixin,
    ListCreateRetrieveUpdateViewSetMixin
):
    queryset = AdvanceExpenseCancelHistory.objects.all()
    serializer_class = AdvanceExpenseCancelHistorySerializer
    permission_classes = [AdvanceExpenseRequestObjectPermission, AdvanceExpenseRequestPermission]
    filter_backends = [FilterMapBackend, SearchFilter, OrderingFilterMap]
    filter_map = {
        'created_at': ('created_at', 'date'),
        'from_date': 'created_at__date__gte',
        'to_date': 'created_at__date__lte',
        'status': 'status',
        'type': 'advance_expense__type',
        'employee': 'advance_expense__employee'
    }
    ordering_fields_map = {
        'created_at': 'created_at',
        'total_amount': 'total_amount',
        'status': 'status',
    }
    search_fields = [
        'advance_expense__employee__first_name', 'advance_expense__employee__middle_name',
        'advance_expense__employee__last_name'
    ]
    statistics_field = 'status'
    history_model = AdvanceExpenseRequestHistory
    notification_for = 'advance expense'
    permission_for_hr = [ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION]

    def get_queryset(self):
        base_qs = self.queryset.filter(
            advance_expense__employee__detail__organization=self.organization
        )
        if self.mode == 'hr':
            queryset = base_qs
        elif self.mode == 'approver':
            queryset = self.queryset.filter(
                Q(recipient=self.request.user) |
                Q(approvals__user=self.request.user,
                  approvals__status__in=[APPROVED, DENIED])
            )
        else:
            queryset = base_qs.filter(advance_expense__employee=self.request.user)
        return queryset.select_related(
            'advance_expense__employee', 'advance_expense__employee__detail',
            'advance_expense__employee__detail__organization',
            'advance_expense__employee__detail__job_title',
        ).annotate(
            cancel_request_exists=Exists(
                AdvanceExpenseCancelHistory.objects.filter(
                    advance_expense=OuterRef('pk')
                ).exclude(
                    status__in=[DENIED, CANCELED]
                )
            )
        ).distinct()

    def get_serializer(self, *args, **kwargs):
        if self.action in ['list']:
            kwargs.update({
                'exclude_fields': [
                   'approvals'
                ]
            })
        return super().get_serializer(*args, **kwargs)

    def get_notification_url_for_organization(self, organization=None):
        return f'/admin/{organization.slug}/expense-management/cancel-request'

    def get_notification_url_for_user(self, user=None):
        return '/user/expense-management/cancel-request'

    def get_notification_url_for_approver(self, user=None):
        return '/user/expense-management/request/cancel-advance-request'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        expense_type = self.request.query_params.get('expense_type', OTHER)
        context['expense_type'] = expense_type.title()
        context['organization'] = self.organization
        return context

    def get_type(self, *args, **kwargs):
        text_type = {
            'Travel': f'Travel Authorization and Advance Request Cancel Form'
        }
        instance = self.get_object()
        return text_type.get(instance.advance_expense.type, 'advance expense cancel request')

    def get_organization_text(self, employee):
        return f"Approval for {self.get_type()} " \
               f"by {employee.full_name} has been completed."

    def retrieve(self, request, *args, **kwargs):
        cancel_expense = self.get_object()
        if self.request.query_params.get('expense_type',
                                         OTHER).title() != cancel_expense.advance_expense.type:
            return Response(
                {
                    'detail': 'Invalid query params supplied. '
                              f'\'expense_type\' must be \'{cancel_expense.advance_expense.type}\' '
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



