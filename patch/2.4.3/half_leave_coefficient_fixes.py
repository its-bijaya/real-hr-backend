from datetime import timedelta

from django.db.models import F

from irhrs.attendance.constants import SECOND_HALF
from irhrs.attendance.models import TimeSheet

_timesheet_all = TimeSheet.objects.filter(leave_coefficient=SECOND_HALF,
                                          timesheet_for__gte='2019-10-03')
timesheets = _timesheet_all.annotate(
    expected_working_minute=F('expected_punch_out') - F('expected_punch_in')
)

for timesheet in timesheets:
    if timesheet.work_time:
        working_minutes = timesheet.work_time.working_minutes / 2
        if timesheet.expected_working_minute > timedelta(minutes=working_minutes):
            timesheet.expected_punch_out = timesheet.expected_punch_out - timedelta(minutes=working_minutes)
            timesheet.save()
            timesheet.fix_entries()
            print(timesheet.id, '\t', timesheet.timesheet_user, '\t', timesheet.timesheet_for)