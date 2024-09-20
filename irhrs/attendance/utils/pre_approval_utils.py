from datetime import timedelta

from irhrs.attendance.models import PreApprovalOvertime
from irhrs.attendance.constants import (
    REQUESTED, FORWARDED, APPROVED, DECLINED, CANCELLED,
)
ZERO = timedelta(0)


def hold_credit_if_overtime_undecided(timesheet):
    """
    Returns Hold, Reserved duration
    :param timesheet: Timesheet for any day
    :returns:
        If does not exist for the day: (False, ZERO)
        If exists in REQUESTED/FORWARDED: (True, ZERO)
        If exists in APPROVED: (False, requested_duration)
    """
    user = timesheet.timesheet_user
    date = timesheet.timesheet_for

    pre_approval_for_the_day = PreApprovalOvertime.objects.filter(
        sender=user,
        overtime_date=date,
    ).exclude(
        status__in=(DECLINED, CANCELLED)
    ).first()
    if not pre_approval_for_the_day:
        return False, ZERO
    if pre_approval_for_the_day.status in (REQUESTED, FORWARDED):
        return True, ZERO
    if pre_approval_for_the_day.status == APPROVED:
        return False, pre_approval_for_the_day.overtime_duration
