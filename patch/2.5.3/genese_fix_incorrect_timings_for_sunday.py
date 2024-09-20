import json

from dateutil.parser import parse
from dateutil.rrule import rrule, WEEKLY, SU
from django.forms import model_to_dict
from django.utils import timezone

from irhrs.attendance.constants import WORKDAY, HOLIDAY, OFFDAY
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.models import TimeSheet
from irhrs.core.utils.common import combine_aware
from irhrs.organization.models import Organization

organization_slug = 'rojgari-services-pvt-ltd'
global_diff = dict()
organization = Organization.objects.get(slug=organization_slug)
date_start = '2019-10-14'
date_until = '2020-04-01'

dates = map(
    lambda dt: dt.date(),
    rrule(
        freq=WEEKLY,
        dtstart=parse(date_start),
        until=parse(date_until),
        # Iterate every Sunday.
        byweekday=SU
    )
)


def m2d(instance):
    return model_to_dict(
        instance,
        fields=[field.name for field in instance._meta.fields]
    )


def fix_time_sheet(time_sheet):
    """
    This method will be used to FIX time sheets,
    Apply leave and holidays

    Fix time sheets for every user on  daily basis
    If the user has requested leave we create time shift for that day
    """
    user = time_sheet.timesheet_user
    date_ = time_sheet.timesheet_for
    d1 = m2d(time_sheet)

    def get_coefficient():
        if user.is_holiday(date_):
            return HOLIDAY
        elif user.is_offday(date_):
            return OFFDAY
        else:
            return WORKDAY

    user.attendance_setting.force_prefetch_for_work_shift = True
    user.attendance_setting.force_work_shift_for_date = date_
    shift = user.attendance_setting.work_shift

    if not shift:
        return None
    try:
        day = shift.days[0]
    except IndexError:
        # This means, its off-day.
        day = None
    if day:
        for time in day.work_times:
            defaults = {
                'coefficient': get_coefficient(),
                'expected_punch_in': combine_aware(
                    date_,
                    time.start_time
                ),
                'work_time': time,
                'work_shift': shift,
                'expected_punch_out': combine_aware(
                    date_ + timezone.timedelta(days=1),
                    time.end_time
                ) if time.extends else combine_aware(
                    date_,
                    time.end_time
                )
            }
            for attribute, value in defaults.items():
                setattr(time_sheet, attribute, value)
            time_sheet.save()
    else:
        time_sheet.coefficient = get_coefficient()
        time_sheet.work_shift = shift
        time_sheet.save()
    fix_entries_on_commit(time_sheet, send_notification=False)
    d2 = m2d(time_sheet)
    diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
    if diffs:
        diffx = dict(diffs)
        global_diff[time_sheet] = diffx


queryset = TimeSheet.objects.filter(
    timesheet_for__in=dates,
    timesheet_user__detail__organization=organization,
    coefficient=WORKDAY
)

total_count = queryset.count()
print(total_count, 'will be affected')
for ind, ts in enumerate(queryset):
    fix_time_sheet(ts)
    print(round(ind/total_count*100, 2), '% Completed\r', end='')