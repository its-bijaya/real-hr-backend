from django.forms.models import model_to_dict
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from irhrs.attendance.constants import HOLIDAY, WORKDAY, OFFDAY
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.models import IndividualUserShift, TimeSheet
from irhrs.core.utils.common import combine_aware
import django
from dateutil.parser import parse
from dateutil.rrule import rrule, DAILY
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import override_settings

from irhrs.attendance.constants import DEVICE, WORKDAY, NO_LEAVE
from irhrs.attendance.models import TimeSheet
from irhrs.attendance.tasks.timesheets import populate_timesheets
from irhrs.organization.models import Organization


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
    print(
        time_sheet,
        'was modified as follows:',
        dict(diffs)
    )

organization_slug = 'evolve-pvt-ltd'

# FROM THE START TILL THE END ,WE DONT STOP NO!

date_begin = '2019-07-17'
date_until = '2019-12-31'
USER = get_user_model()
filtered_users = USER.objects.filter(
    detail__organization__slug=organization_slug,
).current()

date_iterator = list(
    map(
        lambda dt: dt.date(),
        rrule(
            freq=DAILY,
            dtstart=parse(date_begin),
            until=parse(date_until),
        )
    )
)

# Populate TimeSheet for All dates at first.
# for date_object in date_iterator:
#     results = populate_timesheets(
#         date_object.isoformat()
#     )
#     print(
#         date_object.isoformat(),
#         str(results.get('created')).rjust(5),
#         str(results.get('updated')).rjust(5),
#         str(results.get('failed')).rjust(5),
#         str(results.get('for')).rjust(5),
#         str(results.get('user')).rjust(5),
#     )

# For each, punch In.\
base_qs = TimeSheet.objects.filter(
    coefficient=WORKDAY,
    is_present=False,
    leave_coefficient=NO_LEAVE,
    timesheet_for__in=date_iterator,
    timesheet_user__in=filtered_users
).select_related(
    'timesheet_user'
).order_by(
    'timesheet_user__first_name',
    'timesheet_for',
)
final_id = base_qs.count()
with override_settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'):
    with transaction.atomic():
        for index, time_sheet in enumerate(base_qs):
            fix_time_sheet(time_sheet)
            time_sheet.refresh_from_db()
            if time_sheet.coefficient != WORKDAY:
                continue
            print(str(index+1).rjust(5)+'/'+str(final_id), time_sheet)
            for punch_it in (time_sheet.expected_punch_in, time_sheet.expected_punch_out):
                TimeSheet.objects.clock(
                    user=time_sheet.timesheet_user,
                    date_time=punch_it,
                    entry_method=DEVICE
                )


# It Shouldn't but if it did,
still_exists = base_qs.filter(
    is_present=False
)
if still_exists:
    print(still_exists.count(), 'duplicated')
    # still_exists.delete()
