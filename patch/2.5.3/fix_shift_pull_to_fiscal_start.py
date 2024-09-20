import json

from dateutil.rrule import rrule, DAILY
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.utils import timezone

from irhrs.attendance.constants import HOLIDAY, WORKDAY, OFFDAY
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.models import IndividualUserShift, TimeSheet
from irhrs.core.utils.common import combine_aware
from irhrs.organization.models import FiscalYear, Organization

organization_slug = 'evolve-pvt-ltd'

USER = get_user_model()
organization = Organization.objects.get(slug=organization_slug)

shift_users = USER.objects.filter(
    detail__organization=organization
).current()  # Current Users Only.

fiscal = FiscalYear.objects.current(
    organization=organization
)

start = fiscal.applicable_from

processed_user = list()

# Fix Shifts for all users (starting from Fiscal Year or DOJ)

for individual_shift in IndividualUserShift.objects.filter(
        individual_setting__user__in=shift_users,
        applicable_from__gt=start
).order_by('applicable_from'):
    usr = individual_shift.individual_setting.user
    if usr in processed_user:
        continue
    processed_user.append(usr)
    print(
        individual_shift.individual_setting.user,
        individual_shift.applicable_from
    )
    individual_shift.applicable_from = max((
        usr.detail.joined_date,
        start
    ))
    individual_shift.save()

until = timezone.now().date()

print(
    'Date'.rjust(10),
    'User'.rjust(10),
    'Created'.rjust(10),
    'Updated'.rjust(10),
    'Failed'.rjust(10)
)
for _date in rrule(
        freq=DAILY,
        dtstart=start,
        until=until
):
    user_count, created_count, updated_count, failed_count = TimeSheet.objects.create_timesheets(
        _date
    )
    print(
        str(_date.date()).rjust(10),
        str(user_count).rjust(10),
        str(created_count).rjust(10),
        str(updated_count).rjust(10),
        str(failed_count).rjust(10),
    )


# EVOLVE DATA FIX #####
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
    diffx = json.dumps(
        dict(diffs),
        default=str,
        indent=2
    )
    print(
        time_sheet,
        'was modified as follows:',
        diffx
    )


for ts in TimeSheet.objects.filter(
        work_shift__isnull=True
):
    base = TimeSheet.objects.filter(
        timesheet_for=ts.timesheet_for,
        timesheet_user=ts.timesheet_user
    ).exclude(
        id=ts.id
    )
    if base.count() == 0:
        continue
    print(
        ts.timesheet_user, ts.timesheet_for, base.count()
    )
    alternate_time_sheet = base.first()
    if alternate_time_sheet:
        alternate_time_sheet.delete()
        fix_time_sheet(ts)
