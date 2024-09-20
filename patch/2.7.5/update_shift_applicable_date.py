import json
import os

from dateutil.parser import parse
from dateutil.rrule import rrule, DAILY
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from irhrs.attendance.models import IndividualUserShift, TimeSheetEntry, TimeSheet

User = get_user_model()
hard_start_date = '2020-07-16'
hard_end_date = '2020-11-19'


def fix_shift_applicable_dates(user_id):
    user_doj = User.objects.get(id=user_id).detail.joined_date
    shift = IndividualUserShift.objects.filter(
        individual_setting__user_id=user_id,
    ).order_by(
        'applicable_from'
    ).first()
    if not shift:
        print('No Shift')
        return
    shift.applicable_from = user_doj
    shift.save()

    # if this was a dedicated shift, the work days need to be updated as well.
    # because, there could be multiple work days defined: proceed this way.
    for d in range(1, 8):
        day = shift.shift.work_days.filter(day=d).order_by('applicable_from').first()
        if day:
            day.applicable_from = min(day.applicable_from, user_doj)
            day.save()


def empty_time_sheets(time_sheets):
    """
    Removes all time_sheet_entries, resets punch_in/punch_out/punch_in_delta/punch_out_delta
    but preserves coefficients.
    :param time_sheets: time_sheets queryset
    """
    time_sheets.update(
        punch_in=None,
        punch_out=None,
        punch_in_delta=None,
        punch_out_delta=None,
        punctuality=None,
        is_present=False
    )
    TimeSheetEntry.objects.filter(
        timesheet__in=time_sheets
    ).delete()


def back_up_time_sheet_entries(user_id):
    user_doj = User.objects.get(id=user_id).detail.joined_date
    queryset = TimeSheet.objects.filter(
        timesheet_for__range=(user_doj, hard_end_date),
        timesheet_user_id=user_id
    )

    # <-- Record all timestamps for the date.
    user = User.objects.get(id=user_id)
    user_logs = list(
        TimeSheetEntry.objects.filter(
            timesheet__timesheet_user=user
        ).values_list(
            'timestamp', 'entry_method', 'timesheet__timesheet_for'
        )
    )

    JSON_LOGS = {
        user.id: user_logs
    }
    print('Begin JSON Dump')
    base_path = os.path.abspath(
        os.path.join(
            settings.ROOT_DIR,
            'backups'
        )
    )
    file_path = os.path.join(
        base_path,
        f"{user.full_name}-all-entries.json"
    )
    with open(file_path, 'w') as f:
        json.dump(JSON_LOGS, f, default=str)
    print('Attendance Dump stored in ', file_path)

    # Record all timestamps for the date. -->

    empty_time_sheets(queryset)
    date_iterator = rrule(
        freq=DAILY,
        dtstart=user_doj,
        until=parse(hard_end_date).date(),
    )
    for date_ in date_iterator:
        res = TimeSheet.objects._create_or_update_timesheet_for_profile(
            user, date_.date()
        )
        print(date_.date(), res, end='\r')
    print()
    for timestamp, entry_method, timesheet_for in user_logs:
        TimeSheet.objects.clock(
            user=user,
            date_time=timestamp,
            entry_method=entry_method
        )


with transaction.atomic():
    fix_shift_applicable_dates(90)
    back_up_time_sheet_entries(90)


"""

def fix_shift_applicable_dates(user_id):
    user_doj = User.objects.get(id=user_id).detail.joined_date
    shift = IndividualUserShift.objects.filter(
        individual_setting__user_id=user_id,
    ).order_by(
        'applicable_from'
    ).first()
    if not shift:
        print('No Shift')
        return
    shift.applicable_from = user_doj
    shift.save()

    # if this was a dedicated shift, the work days need to be updated as well.
    # because, there could be multiple work days defined: proceed this way.
    for d in range(1, 8):
        day = shift.shift.work_days.filter(day=d).order_by('applicable_from').first()
        if day:
            day.applicable_from = min(day.applicable_from, user_doj)
            day.save()

id_list = [
    (8, 211),
    (7, 212),
    (79, 213),
    (89, 214),
    (82, 215),
    (80, 233),
    (3, 210),
    (85, 208),
    (22, 234),
]
for _, new_id in id_list:
    fix_shift_applicable_dates(new_id)

"""