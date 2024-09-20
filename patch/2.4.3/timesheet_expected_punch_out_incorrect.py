from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from irhrs.attendance.models import TimeSheet
from irhrs.core.utils.common import combine_aware

_timesheets_all = TimeSheet.objects.filter(timesheet_for__gte='2019-10-03')
timesheets = _timesheets_all.annotate(
    expected_work_hours=F('expected_punch_out') - F('expected_punch_in')
)
for timesheet in timesheets:
    if timesheet.expected_work_hours and timesheet.expected_work_hours > timedelta(days=1):
        shift = timesheet.work_shift
        if not shift:
            continue
        timing = timesheet.work_time
        expected_punch_out = combine_aware(
            timesheet.timesheet_for + timezone.timedelta(
                #int(True) = 1
                days=int(bool(timing.extends))
            ),
            timing.end_time
        )
        timesheet.expected_punch_out = expected_punch_out
        timesheet.save()
        timesheet.fix_entries()
        print(timesheet.timesheet_user, timesheet.timesheet_for)