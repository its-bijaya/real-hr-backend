from django.db.models import Sum, Q

from irhrs.core.mixins.viewset_mixins import UserCommonsMixin, PastUserFilterMixin, \
    ListViewSetMixin, PastUserGenericFilterMixin
from irhrs.leave.api.v1.reports.serializers.employee_profile_report import \
    EmployeeProfileLeaveSerializer
from irhrs.leave.constants.model_constants import APPROVED
from irhrs.leave.models import LeaveAccount
from irhrs.leave.utils.balance import get_fiscal_year_for_leave

from irhrs.organization.models import FiscalYear


class EmployeeProfileLeaveDetails(
    PastUserGenericFilterMixin,
    UserCommonsMixin,
    ListViewSetMixin
):
    queryset = LeaveAccount.objects.all()
    user_definition = 'user'
    serializer_class = EmployeeProfileLeaveSerializer

    def get_queryset(self):
        fiscal_year = get_fiscal_year_for_leave(organization=self.user.detail.organization)
        if fiscal_year:
            return super().get_queryset().annotate(
                consumed_balance=Sum('leave_requests__balance', filter=Q(
                    leave_requests__start__date__gte=fiscal_year.applicable_from,
                    leave_requests__end__date__lte=fiscal_year.applicable_to,
                    leave_requests__status=APPROVED))
            ).filter(
                consumed_balance__isnull=False)

        return self.queryset.none()
