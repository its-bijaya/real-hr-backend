import calendar

from dateutil.rrule import rrule, DAILY
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField

from irhrs.attendance.api.v1.permissions import AttendanceReportPermission
from irhrs.attendance.api.v1.reports.serializers.monthly_attendance import MonthlyAttendanceReportSerializer,\
    MonthlyAttendanceExportSerializer

from irhrs.attendance.constants import WORKDAY, OFFDAY, HOLIDAY
from irhrs.attendance.models import TimeSheet
from irhrs.core.mixins.serializers import add_fields_to_serializer_class
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, \
    OrganizationMixin, PastUserFilterMixin, DateRangeParserMixin
from irhrs.core.utils.common import get_today, validate_permissions
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.export.mixins.export import BackgroundTableExportMixin
from irhrs.permission.constants.permissions import ATTENDANCE_PERMISSION, \
    ATTENDANCE_REPORTS_PERMISSION

USER = get_user_model()


class MonthlyAttendanceReport(
    PastUserFilterMixin, BackgroundTableExportMixin,
    DateRangeParserMixin, OrganizationMixin, ListViewSetMixin
):
    serializer_class = MonthlyAttendanceReportSerializer
    filter_backends = FilterMapBackend,
    permission_classes = [AttendanceReportPermission]
    filter_map = {
        'division': 'detail__division__slug',
        'user': 'id',
        'username': 'username',
    }
    queryset = USER.objects.all()
    export_type = 'Monthly Attendance'
    notification_permissions = [ATTENDANCE_REPORTS_PERMISSION]

    def get_export_description(self):
        lines = [
            "Day wise Monthly report"
        ]
        start_date, end_date = self.get_parsed_dates()
        no_of_days = (end_date - start_date).days + 1
        lines.append(
            f"Date Range: {start_date} - {end_date}, Total Days: {no_of_days}"
        )
        return lines

    @staticmethod
    def get_default_start_date():
        return get_today() - timezone.timedelta(days=30)

    @staticmethod
    def get_default_end_date():
        return get_today()

    def get_export_fields(self):
        fields = [
            {
                "name": "user",
                "title": "User Details",
                "fields": (
                    {"name": "id", "title": "Id"},
                    {"name": "full_name", "title": "Full Name"},
                    {"name": "username", "title": "Username"},
                )
            },
            {
                "name": "total_holiday",
                "title": "Total Holidays",
            },
            {
                "name": "total_workday",
                "title": "Total Work Days"
            },

        ]
        for day, value in self._get_report_days(*self.get_parsed_dates()).items():
            fields.append({
                    "name": day,
                    "title": day,
                    "fields": ({"name": "title", "title": value['day']},)
            })

        return fields

    def get_extra_export_data(self):
        extra = super().get_extra_export_data()
        extra["serializer_context"] = {
            'report_days': self._get_report_days(*self.get_parsed_dates())
        }
        extra["organization"] = self.get_organization()
        return extra

    def get_serializer_class_params(self):
        return {
            "args": self.get_parsed_dates(),
            "kwargs": dict()
        }

    @classmethod
    def get_serializer_class_for_export(cls, start_date, end_date):
        serializer_fields = dict()

        for date in cls._get_report_days(start_date, end_date):
            serializer_fields.update({
                date: SerializerMethodField(),
                f"get_{date}": lambda s, o, date_c=date: s.day_breakdown(o).get(date_c)
            })

        return add_fields_to_serializer_class(MonthlyAttendanceExportSerializer, fields=serializer_fields)

    def get_queryset(self):
        qs = super().get_queryset().filter(
            detail__organization=self.get_organization(),
        )
        if not validate_permissions(
            self.request.user.get_hrs_permissions(self.get_organization()),
            ATTENDANCE_PERMISSION,
            ATTENDANCE_REPORTS_PERMISSION,
        ):
            qs = qs.filter(
                id=self.request.user
            )
        return qs

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        start, end = self.get_parsed_dates()

        if not self.validate_start_end(start, end):
            raise ValidationError({'detail': 'Date range exceeds a month'})

        return queryset.filter(
            timesheets__timesheet_for__gte=start,
            timesheets__timesheet_for__lte=end,
        ).select_related(
            'detail', 'detail__organization', 'detail__division',
            'detail__job_title', 'detail__employment_level'
        ).prefetch_related(
            Prefetch('timesheets',
                     queryset=TimeSheet.objects.filter(
                         timesheet_user__detail__organization=self.get_organization()
                     ).select_related('work_time', 'work_shift').order_by('timesheet_for', 'expected_punch_in'),
                     to_attr='_timesheets'
                     )

        ).annotate(
            total_workday=Count('timesheets__timesheet_for',
                                filter=Q(timesheets__coefficient=WORKDAY),
                                distinct=True),
            total_holiday=Count('timesheets__timesheet_for',
                                filter=Q(timesheets__coefficient=HOLIDAY),
                                distinct=True),
            total_offday=Count('timesheets__timesheet_for',
                               filter=Q(timesheets__coefficient=OFFDAY),
                               distinct=True)
        )

    @staticmethod
    def validate_start_end(start, end):
        return not (end - start).days > 33

    @staticmethod
    def _get_report_days(start, end):
        _day_list = {}
        date_list = list(rrule(freq=DAILY, dtstart=start, until=end))
        for date in date_list:
            _day_list[date.date().__str__()] = {
                'label': calendar.month_abbr[
                             date.month] + ' ' + date.day.__str__(),
                'var': calendar.month_abbr[date.month] + date.day.__str__(),
                'day': calendar.day_name[date.weekday()],
                'results': []
            }
        return _day_list

    @method_decorator(cache_page(60 * 60 * 2))
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        start, end = self.get_parsed_dates()

        context = self.get_serializer_context()
        context['report_days'] = self._get_report_days(start, end)
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True,
                                           context=context)
        resp = self.get_paginated_response(serializer.data)

        resp.data['start_date'], resp.data['end_date'] = start, end
        resp.data['total_days'] = (end - start).days + 1
        return resp

    @staticmethod
    def has_user_permission():
        return False

    def get_frontend_redirect_url(self):
        return f'/admin/{self.organization.slug}/attendance/reports/monthly-report'
