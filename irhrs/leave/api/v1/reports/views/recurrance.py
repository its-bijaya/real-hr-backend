from django.contrib.auth import get_user_model
from rest_framework.filters import SearchFilter, OrderingFilter

from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, \
    OrganizationMixin, DateRangeParserMixin, PastUserFilterMixin
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.leave.api.v1.permissions import AdminOnlyLeaveReportPermission
from irhrs.leave.api.v1.reports.serializers.recurrence import \
    UserRecurrenceSerializer
from irhrs.leave.models import LeaveAccount
from irhrs.leave.tasks import get_active_master_setting
from irhrs.leave.utils.balance import \
    get_applicable_leave_types_for_organization

User = get_user_model()


class RecurrenceLeaveReport(DateRangeParserMixin,
                            PastUserFilterMixin,
                            OrganizationMixin,
                            ListViewSetMixin):
    """
    list:
    filters = "branch", "division", "employment_level", "start_date", "end_date"
    """
    serializer_class = UserRecurrenceSerializer
    filter_backends = (SearchFilter, OrderingFilter, FilterMapBackend,)
    queryset = User.objects.all()
    search_fields = (
        'first_name',
        'middle_name',
        'last_name'
    )

    ordering_fields = (
        'first_name',
        'middle_name',
        'last_name'
    )

    filter_map = {
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'employee_level': 'detail__employment_level__slug',
    }
    permission_classes = [AdminOnlyLeaveReportPermission]

    def get_queryset(self):
        return super().get_queryset().filter(
            detail__organization=self.get_organization()
        ).distinct()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        start_date_parsed, end_date_parsed = self.get_parsed_dates()
        ctx.update({
            'filters': {
                'start': start_date_parsed,
                'end': end_date_parsed
            },
            'active_leave_accounts': LeaveAccount.objects.filter(
                rule__leave_type__master_setting=get_active_master_setting(
                    self.get_organization()
                )
            )
        })

        return ctx

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        start_date_parsed, end_date_parsed = self.get_parsed_dates()

        if start_date_parsed and end_date_parsed:
            queryset = queryset.filter(
                leave_requests__start__date__lte=end_date_parsed,
                leave_requests__end__date__gte=start_date_parsed
            )

        return queryset

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        ret.data.update({
            'applicable_leaves': get_applicable_leave_types_for_organization(
                self.get_organization()
            )
        })
        return ret
