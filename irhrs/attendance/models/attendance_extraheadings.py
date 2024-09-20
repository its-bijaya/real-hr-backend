from django.contrib.postgres.fields import ArrayField
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.organization.models.organization import Organization

DAY, LEAVE_REMARKS, LOGS, \
EXPECTED_PUNCH_IN, EXPECTED_PUNCH_OUT, \
PUNCH_IN_CATEGORY, PUNCH_OUT_CATEGORY, \
TOTAL_LOST_HOUR, BREAK_IN_OUT_LOST_TIME, \
OVERTIME, APPROVED_OVERTIME, CONFIRMED_OVERTIME, \
WORK_DURATION, EXPECTED_WORK_HOURS, REMARKS, = (
    "day", "leave_coefficient", "logs",
    "expected_punch_in", "expected_punch_out",
    "punch_in_category", "punch_out_category",
    "total_lost_hours", "break_in_out_lost_hours",
    "overtime", "approved_overtime", "confirmed_overtime",
    "worked_hours", "expected_work_hours", "coefficient"
)

EXTRA_HEADING_CHOICES = (
    (DAY, DAY),
    (LEAVE_REMARKS, LEAVE_REMARKS),
    (LOGS, LOGS),
    (EXPECTED_PUNCH_IN, EXPECTED_PUNCH_IN),
    (EXPECTED_PUNCH_OUT, EXPECTED_PUNCH_OUT),
    (PUNCH_IN_CATEGORY, PUNCH_IN_CATEGORY),
    (PUNCH_OUT_CATEGORY, PUNCH_OUT_CATEGORY),
    (TOTAL_LOST_HOUR, TOTAL_LOST_HOUR),
    (BREAK_IN_OUT_LOST_TIME, BREAK_IN_OUT_LOST_TIME),
    (OVERTIME, OVERTIME),
    (APPROVED_OVERTIME, APPROVED_OVERTIME),
    (CONFIRMED_OVERTIME, CONFIRMED_OVERTIME),
    (WORK_DURATION, WORK_DURATION),
    (EXPECTED_WORK_HOURS, EXPECTED_WORK_HOURS),
    (REMARKS, REMARKS),
)


class AttendanceHeadingReportSetting(BaseModel):
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='organization'
    )
    headings = ArrayField(
        models.CharField(max_length=30, choices=EXTRA_HEADING_CHOICES),
    )
