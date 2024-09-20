from dateutil import rrule

from django.db import models
from django.db.models import Case, When, F, Subquery, OuterRef, Sum
from django.http import Http404
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from irhrs.attendance.api.v1.permissions import AttendanceReportPermission, TimeSheetReportPermission
from irhrs.attendance.constants import WORKDAY, NO_LEAVE, FULL_LEAVE, FIRST_HALF, HOLIDAY, OFFDAY
from irhrs.attendance.models import TimeSheet, TimeSheetRegistrationReportSettings
from irhrs.attendance.utils.timesheet_report import TimeSheetReport
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, UserMixin, OrganizationMixin
from irhrs.core.utils import get_system_admin
from irhrs.leave.constants.model_constants import SECOND_HALF, APPROVED
from irhrs.leave.models import LeaveType, LeaveAccount
from irhrs.leave.models.request import LeaveSheet
from irhrs.organization.models import FiscalYear, cached_property


class AttendanceActionableReport(OrganizationMixin, UserMixin, ListViewSetMixin):

    queryset = TimeSheet.objects.all()
    permission_classes = [TimeSheetReportPermission]
    default_leave_legend = {
        "legend": "Leave",
        "color": "#8B008B",
        "text": "Leave"
    }

    def get_user_queryset(self):
        return super().get_user_queryset().filter(detail__organization=self.organization)

    def get_queryset(self):
        return super().get_queryset().filter(timesheet_user=self.user)

    @cached_property
    def fiscal_year(self):
        fiscal_year_id = self.request.query_params.get('fiscal_year')
        if fiscal_year_id:
            fiscal_year = get_object_or_404(
                FiscalYear.objects.filter(organization=self.organization),
                id=fiscal_year_id
            )
        else:
            fiscal_year = FiscalYear.objects.active_for_date(
                organization=self.get_organization()
            )
        if not fiscal_year:
            raise ValidationError(
                {'non_field_errors': ["Active Fiscal Year not found"]}
            )
        return fiscal_year

    def list(self, request, *args, **kwargs):

        qs = self.filter_queryset(self.get_queryset())
        timesheet_report = TimeSheetReport(self.user, self.fiscal_year, qs)

        return Response(timesheet_report.get_report_data())

    @property
    def leave_type(self):
        return LeaveType.objects.filter(id=self.kwargs.get('leave_type_id')).first()

    @action(detail=False, methods=['GET'], url_path=r'leave-details/(?P<leave_type_id>\d+)')
    def extra_data(self, request, **kwargs):
        timesheet_report = TimeSheetReport(self.user, self.fiscal_year)
        timesheet_report.extra_data(self.leave_type)
        return Response(timesheet_report.extra_data(self.leave_type))
