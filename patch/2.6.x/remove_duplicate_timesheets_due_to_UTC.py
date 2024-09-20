"""
Generate all time-sheets for user for given dates.
"""

# ##################################################### #
# ################# CREATE FOR ALL DATES ############## #
# ##################################################### #

from datetime import date

from dateutil.rrule import rrule, DAILY
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from irhrs.attendance.constants import NO_LEAVE
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.models import TimeSheet

user = get_user_model().objects.get(pk=87)
date_start = date(2020, 6, 16)
date_until = timezone.now().astimezone().date()

# date_generator from start to end.
date_iterator = map(
    lambda datetime: datetime.date(),
    rrule(
        DAILY,
        dtstart=date_start,
        until=date_until
    )
)
max_len = 0


def stack_print(*args, clear=False):
    global max_len
    if clear:
        max_len = max(map(lambda g: len(str(g)), args)) + 5
    print(*map(lambda content: str(content).rjust(max_len), args))


stack_print(
    'date', 'user_count', 'created_count', 'updated_count', 'failed_count', clear=True
)

for date in date_iterator:
    print(*TimeSheet.objects._create_or_update_timesheet_for_profile(user, date))

# ##################################################### #
# ################# FIND TS COUNT > 1 ################# #
# ##################################################### #

from datetime import date

from dateutil.rrule import rrule, DAILY
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from irhrs.attendance.constants import NO_LEAVE
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.models import TimeSheet

more_than_one_per_day = TimeSheet.objects.order_by().values(
    'timesheet_user', 'timesheet_for',
).annotate(
    ts_count=Count(
        'id',
    )
).filter(
    ts_count__gt=1
).values_list('timesheet_user', 'timesheet_for')


def custom_fix_entries(self):
    fix_entries_on_commit(self, send_notification=False)


TimeSheet.fix_entries = custom_fix_entries

total_entries = more_than_one_per_day.count()
for index, meta in enumerate(more_than_one_per_day, start=1):
    print('\t', str(index).rjust(len(str(total_entries))), '/', total_entries, end='\r')
    timesheet_user, timesheet_for = meta
    equivalent_timesheets = TimeSheet.objects.filter(
        timesheet_user_id=timesheet_user,
        timesheet_for=timesheet_for
    )

    user = get_user_model().objects.get(pk=timesheet_user)

    user.attendance_setting.force_prefetch_for_work_shift = True
    user.attendance_setting.force_work_shift_for_date = timesheet_for
    shift = user.attendance_setting.work_shift
    if not shift:
        print('No SHIFT', user, timesheet_for)
        continue

    day = shift.days[0] if shift.days else None
    if day and len(day.work_times) > 1:
        continue
    adjustment_ts = equivalent_timesheets.filter(adjustment_requests__isnull=False).first()
    leave_ts = equivalent_timesheets.exclude(leave_coefficient=NO_LEAVE).first()
    hour_ts = equivalent_timesheets.exclude(hour_off_coefficient='').first()
    if adjustment_ts:
        parent = adjustment_ts
        others = equivalent_timesheets.exclude(id=adjustment_ts.id)
    elif leave_ts:
        parent = leave_ts
        others = equivalent_timesheets.exclude(id=leave_ts.id)
    elif hour_ts:
        parent = hour_ts
        others = equivalent_timesheets.exclude(id=hour_ts.id)
    else:
        parent = equivalent_timesheets.all().first()
        others = equivalent_timesheets.exclude(id=parent.id)

    for raw_timesheet in others:
        for (
                timestamp, entry_method, category, remark_category, remarks, entry_type
        ) in raw_timesheet.timesheet_entries.values_list(
                'timestamp',
                'entry_method',
                'category',
                'remark_category',
                'remarks',
                'entry_type',
        ):
            TimeSheet.objects.clock(
                user,
                timestamp,
                entry_method,
                entry_type=entry_type,
                remarks=remarks,
                timesheet=parent,
                remark_category=remark_category,
            )
    others.delete()
