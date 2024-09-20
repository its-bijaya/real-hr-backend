
"""PATCH TO APPLY CURRENT SHIFT FROM JOINED DATE AND REGENERATE TIMESHEET"""
import datetime
import multiprocessing

from django.db import transaction
from dateutil.rrule import rrule, DAILY

from django.contrib.auth import get_user_model
from irhrs.attendance.models import IndividualUserShift, TimeSheet
from irhrs.attendance.models.attendance import TimeSheetEntry


User = get_user_model()

# leave as it is for all current users
user_filter = {
    'detail__organization__slug': 'twitter',
    # 'email': 'user1@email.com2'
}

start_date = datetime.date(2021, 7, 17)
end_date = datetime.date(2022, 3, 25)

DATE_LIST_PARSED = list(
    rrule(
        freq=DAILY,
        dtstart=start_date,
        until=end_date
    )
)


def fix_shift_applicable_dates(user):
    """Move shift, work day applicable date to joined date or start date
       which ever is latest
    """
    user_doj = user.detail.joined_date
    shift = IndividualUserShift.objects.filter(
        individual_setting__user_id=user.id,
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
    """Removes all time_sheet_entries, resets punch_in/punch_out/punch_in_delta/punch_out_delta
       but preserves coefficients.
    :param time_sheets: time_sheets queryset
    """
    time_sheets.delete()


def reapply_timesheet_entries(user):
    user_doj = user.detail.joined_date
    queryset = TimeSheet.objects.filter(
        timesheet_for__range=(user_doj, end_date),
        timesheet_user_id=user.id
    )

    # <-- Record all timestamps for the date.
    user_logs = list(
        TimeSheetEntry.objects.filter(
            timesheet__timesheet_user=user
        ).values_list(
            'timestamp', 'entry_method', 'timesheet__timesheet_for'
        )
    )

    # Record all timestamps for the date. -->

    empty_time_sheets(queryset)
    date_iterator = rrule(
        freq=DAILY,
        dtstart=user_doj,
        until=end_date,
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


def populate_time_sheet_for_given_dates(user):
    """
    Create time-sheet for individual user for given dates.
    :return:
    """
    for _date in DATE_LIST_PARSED:
        if _date.date() >= user.detail.joined_date:
            (
                timesheets, created_count, updated_count, status
            ) = TimeSheet.objects._create_or_update_timesheet_for_profile(
                user=user,
                date_=_date
            )
            print(user, 'Time Sheet creation for', _date, status)


@transaction.atomic
def apply_for_user(user):
    fix_shift_applicable_dates(user)
    reapply_timesheet_entries(user)
    populate_time_sheet_for_given_dates(user)


def main():
    """runs apply for user in parallel"""

    pool = multiprocessing.Pool(multiprocessing.cpu_count())

    for user in User.objects.filter(**user_filter).current().select_related('detail'):
        pool.apply_async(apply_for_user, args=(user,))

    pool.close()
    pool.join()


if __name__ == "__main__":
    main()
