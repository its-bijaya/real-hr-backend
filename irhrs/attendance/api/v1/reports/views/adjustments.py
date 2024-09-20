from django.contrib.auth import get_user_model
from django.db.models import Count, OuterRef, Subquery, F, fields as dj_fields
from django.db.models.functions import Coalesce
from rest_framework.filters import SearchFilter

from irhrs.attendance.api.v1.reports.serializers.adjustments import AdjustmentReportSerializer
from irhrs.attendance.api.v1.reports.views.mixins import AttendanceReportPermissionMixin
from irhrs.attendance.constants import ATT_ADJUSTMENT, PUNCH_IN, PUNCH_OUT
from irhrs.attendance.models import TimeSheetEntry
from irhrs.core.mixins.viewset_mixins import SupervisorQuerysetViewSetMixin, OrganizationMixin, ListViewSetMixin, \
    DateRangeParserMixin
from irhrs.core.utils.filters import NullsAlwaysLastOrderingFilter, FilterMapBackend
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.permission.constants.permissions import ATTENDANCE_REPORTS_PERMISSION

USER = get_user_model()


class AdjustmentReportViewSet(AttendanceReportPermissionMixin,
                              SupervisorQuerysetViewSetMixin,
                              OrganizationMixin,
                              DateRangeParserMixin,
                              BackgroundExcelExportMixin,
                              ListViewSetMixin):
    """
    Attendance Adjustment Views
    """
    serializer_class = AdjustmentReportSerializer
    user_field = ''
    queryset = USER.objects.all()
    filter_backends = [FilterMapBackend, SearchFilter, NullsAlwaysLastOrderingFilter]
    notification_permissions = [ATTENDANCE_REPORTS_PERMISSION]
    # ordering_fields_map =
    search_fields = (
        'first_name',
        'middle_name',
        'last_name',
        'username'
    )
    filter_map = {
        'division': 'detail__division__slug',
        'username': 'username',
    }
    allow_non_supervisor_user = True

    export_type = 'Attendance Adjustment Report'
    export_fields = {
        'Name': 'full_name',
        'Username': 'username',
        'Supervisor': 'first_level_supervisor.full_name',
        'punch_in_frequency': 'punch_in_frequency',
        'punch_out_frequency': 'punch_out_frequency',
        'total': 'total'
    }

    def get_ordering_fields_map(self):
        if self.action != 'export':
            return {
                'total': 'total',
                'punch_in_frequency': 'punch_in_frequency',
                'punch_out_frequency': 'punch_out_frequency',
                'full_name': ('first_name', 'middle_name', 'last_name')
            }
        return {
            'full_name': ('first_name', 'middle_name', 'last_name')
        }

    def get_extra_export_data(self):
        extra_data = super().get_extra_export_data()
        start, end = self.get_parsed_dates()

        extra_data.update({
            'start_date': start,
            'end_date': end,
            'ordering': self.request.query_params.get('ordering')
        })

        return extra_data

    def filter_queryset(self, queryset):
        start, end = self.get_parsed_dates()

        if not self.action == 'export':
            queryset = self.annotate_queryset(queryset, start, end)
        return super().filter_queryset(queryset)

    @staticmethod
    def annotate_queryset(queryset, start, end):
        return queryset.annotate(
            punch_in_frequency=Coalesce(
                Subquery(AdjustmentReportViewSet.get_subquery(PUNCH_IN, start, end),
                         output_field=dj_fields.IntegerField()), 0),
            punch_out_frequency=Coalesce(
                Subquery(AdjustmentReportViewSet.get_subquery(PUNCH_OUT, start, end),
                         output_field=dj_fields.IntegerField()), 0)
        ).annotate(total=F('punch_in_frequency') + F('punch_out_frequency'))

    @staticmethod
    def get_subquery(entry_type, start_date, end_date):
        return TimeSheetEntry.objects.filter(entry_method=ATT_ADJUSTMENT, entry_type=entry_type).filter(
            timesheet__timesheet_for__range=[start_date, end_date],
            timesheet__timesheet_user_id=OuterRef('pk')
        ).order_by().values('timesheet__timesheet_user_id').annotate(count=Count('id')).values('count')[:1]

    @classmethod
    def get_exported_file_content(cls, queryset, title, columns, extra_content, description=None, **kwargs):
        start = extra_content.get('start_date')
        end = extra_content.get('end_date')
        ordering = extra_content.get('ordering')

        queryset = cls.annotate_queryset(queryset, start, end)
        if ordering and ordering in ['punch_in_frequency', '-punch_in_frequency', 'punch_out_frequency',
                                     '-punch_out_frequency', 'total', '-total']:
            queryset = queryset.order_by(ordering)

        return super().get_exported_file_content(
            queryset, title, columns, extra_content, description=description, **kwargs
        )

    def get_frontend_redirect_url(self):
        return f'/admin/{self.organization.slug}/attendance/reports/adjustment'
