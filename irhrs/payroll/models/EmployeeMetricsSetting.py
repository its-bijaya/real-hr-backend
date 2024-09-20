from django.db import models
from django.contrib.postgres.fields import ArrayField

from irhrs.organization.models import Organization

WORKING_DAYS, TOTAL_DAYS, WORKED_DAYS, ABSENT_DAYS, LEAVE_DAYS,\
LEAVE_DAYS_ON_WORKDAYS, UNPAID_LEAVE_DAYS,  PAID_DAYS, DAYS_DEDUCTION_FROM_PENALTY, HOLIDAY_COUNT,\
OFFDAY_COUNT, LEAVE_PAID_DAYS, WORKED_ON_OFFDAY_HOLIDAY, WORKED_HOUR, TOTAL_CLAIMED  = 'working_days', \
    'total_days',  'worked_days', 'absent_days', 'leave_days', \
    'leave_days_on_workdays', 'unpaid_leave_days', \
    'paid_days', 'days_deduction_from_penalty', \
    'holiday_count', 'offday_count', 'leave_paid_days', \
    'worked_on_offday_holiday', 'worked_hour', \
    'total_claimed'

EXTRA_HEADING_CHOICES = (
    (WORKING_DAYS, WORKING_DAYS),
    (TOTAL_DAYS, TOTAL_DAYS),
    (WORKED_DAYS, WORKED_DAYS),
    (OFFDAY_COUNT, OFFDAY_COUNT),
    (ABSENT_DAYS, ABSENT_DAYS),
    (LEAVE_DAYS, LEAVE_DAYS),
    (LEAVE_DAYS_ON_WORKDAYS, LEAVE_DAYS_ON_WORKDAYS),
    (UNPAID_LEAVE_DAYS, UNPAID_LEAVE_DAYS),
    (PAID_DAYS, PAID_DAYS),
    (DAYS_DEDUCTION_FROM_PENALTY, DAYS_DEDUCTION_FROM_PENALTY),
    (HOLIDAY_COUNT, HOLIDAY_COUNT),
    (LEAVE_PAID_DAYS, LEAVE_PAID_DAYS),
    (WORKED_ON_OFFDAY_HOLIDAY, WORKED_ON_OFFDAY_HOLIDAY),
    (WORKED_HOUR, WORKED_HOUR),
    (TOTAL_CLAIMED, TOTAL_CLAIMED)
)


class EmployeeMetricHeadingReportSetting(models.Model):
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE
    )
    headings = ArrayField(
        models.CharField(max_length=30, choices=EXTRA_HEADING_CHOICES),
    )
