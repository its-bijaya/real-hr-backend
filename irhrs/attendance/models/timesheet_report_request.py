from django.contrib.auth import get_user_model
from django.db.models import JSONField
from django.db import models

from irhrs.attendance.constants import TIMESHEET_REPORT_REQUEST_CHOICES
from irhrs.common.models import BaseModel
from irhrs.core.utils.common import get_upload_path
from irhrs.organization.models import FiscalYearMonth

USER = get_user_model()


class TimeSheetReportRequest(BaseModel):
    """
    Model to keep timesheet report approval request
    """
    user = models.ForeignKey(
        USER,
        related_name='timesheet_reports',
        on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        USER,
        related_name='timesheet_report_requests',
        on_delete=models.SET_NULL,
        null=True
    )
    status = models.CharField(
        choices=TIMESHEET_REPORT_REQUEST_CHOICES,
        max_length=50,
        db_index=True
    )

    # report data will have all the data needed to be consumed by FE
    report_data = JSONField()

    # this is to keep backup of settings if they are changed after generation
    settings_data = JSONField()

    fiscal_month = models.ForeignKey(FiscalYearMonth, on_delete=models.SET_NULL, null=True)

    # if fiscal month is deleted
    month_name = models.CharField(max_length=50)
    month_from_date = models.DateField()
    month_to_date = models.DateField()
    year_name = models.CharField(max_length=100)
    year_from_date = models.DateField()
    year_to_date = models.DateField()

    def __str__(self):
        return f"Name:{self.user.full_name}, Year Name: {self.year_name}," \
               f" Month Name: {self.month_name}"


class TimeSheetReportRequestHistory(BaseModel):
    request = models.ForeignKey(
        TimeSheetReportRequest,
        on_delete=models.CASCADE,
        related_name='histories'
    )
    actor = models.ForeignKey(
        to=USER,
        on_delete=models.SET_NULL,
        null=True,
        related_name='acted_timesheet_report_request_history'
    )
    action = models.CharField(
        choices=TIMESHEET_REPORT_REQUEST_CHOICES,
        max_length=50,
        db_index=True
    )
    action_to = models.ForeignKey(
        to=USER,
        on_delete=models.SET_NULL,
        null=True,
        related_name='action_to_timesheet_report_request_history'
    )
    attached_signature = models.FileField(upload_to=get_upload_path, null=True)
    remarks = models.TextField(max_length=600, blank=True)
