"""
Create travel Attendance Utils.
"""
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY

from irhrs.attendance.constants import APPROVED, TRAVEL_ATTENDANCE, WORKDAY, FIRST_HALF, \
    SECOND_HALF, FULL_DAY
from irhrs.attendance.models import TimeSheet
from irhrs.attendance.models.travel_attendance import TravelAttendanceDays, TravelAttendanceRequest
from irhrs.attendance.utils.shift_planner import get_shift_details
from irhrs.core.utils.common import combine_aware, get_today


def create_travel_attendance_for_past_dates(travel_request) -> None:
    """
    Create Travel Attendance and Clock respective days for days that are in past.
    :param travel_request: Approved Travel Request
    """
    if travel_request.status != APPROVED:
        return
    user = travel_request.user
    clocks = list()
    for travel_day in travel_request.travel_attendances.filter(
        day__lte=get_today(),
        is_archived=False,
        processed=False
    ):
        timesheets = TimeSheet.objects.filter(
            timesheet_user=user,
            timesheet_for=travel_day.day
        ).select_related(
            'work_time'
        )
        # There is no timesheet for shiftless employee.
        if not timesheets:
            clocks += get_no_timesheet_clocks(travel_day, travel_request)
        # There is Timesheets for Shift Employee.
        for ts in timesheets:
            if ts.expected_punch_in and ts.expected_punch_out:
                clocks.append(get_punch_in(ts, travel_day))
                clocks.append(get_punch_out(ts, travel_day))
            else:
                clocks += get_no_timesheet_clocks(travel_day, travel_request)
        travel_day.processed = True
        travel_day.save(update_fields=['processed'])
        for clock in clocks:
            ts = TimeSheet.objects.clock(
                user,
                clock,
                entry_method=TRAVEL_ATTENDANCE
            )
            travel_day.timesheets.add(ts)


def get_no_timesheet_clocks(travel_day, travel_request):
    clocks = list()
    ed = combine_aware(
        travel_day.day,
        travel_request.end_time
    )
    st = combine_aware(
        travel_day.day,
        travel_request.start_time
    )
    if travel_request.working_time in [FIRST_HALF, SECOND_HALF]:
        delta = (ed - st).total_seconds() // 2
        if travel_request.working_time == FIRST_HALF:
            clocks.append(st + timezone.timedelta(seconds=delta))
            clocks.append(st)
        if travel_request.working_time == SECOND_HALF:
            clocks.append(ed - timezone.timedelta(seconds=delta))
            clocks.append(ed)
    else:
        clocks.append(st)
        clocks.append(ed)
    return clocks


def manage_travel_attendances_for_today(date=None):
    """
    Manages timesheet clock for timesheets created today.
    """
    # List of tuples, user vs. timestamps
    date = get_today() if date is None else date
    base_qs = TravelAttendanceDays.objects.filter(
        is_archived=False,
        processed=False,
        day=date
    ).select_related(
        'travel_attendance'
    )
    missed_travel_attendances = TravelAttendanceDays.objects.filter(
        is_archived=False,
        processed=False,
        day__lt=date
    ).select_related(
        'travel_attendance'
    )
    for missed_request in TravelAttendanceRequest.objects.filter(
            travel_attendances__in=missed_travel_attendances
    ):
        create_travel_attendance_for_past_dates(missed_request)

    for travel_day in base_qs:
        clocks = list()
        travel_request = travel_day.travel_attendance
        # get the related timesheets for this user, for this day.
        timesheets = TimeSheet.objects.filter(
            timesheet_for=date,
            timesheet_user=travel_day.user
        )
        if not timesheets:
            clocks.append(
                combine_aware(
                    travel_day.day,
                    travel_day.travel_attendance.start_time
                )
            )
            clocks.append(
                combine_aware(
                    travel_day.day,
                    travel_day.travel_attendance.end_time
                )
            )
        for ts in timesheets:
            if ts.expected_punch_in and ts.expected_punch_out:
                clocks.append(get_punch_out(ts, travel_day))
                clocks.append(get_punch_in(ts, travel_day))
            else:
                clocks += get_no_timesheet_clocks(travel_day, travel_request)
        for timestamp in clocks:
            ts = TimeSheet.objects.clock(
                user=travel_request.user,
                date_time=timestamp,
                entry_method=TRAVEL_ATTENDANCE
            )
            travel_day.timesheets.add(ts)
        travel_day.processed = True
        travel_day.save(update_fields=['processed'])


def get_punch_out(timesheet, travel_day):
    timestamp = {
        FIRST_HALF: timesheet.expected_punch_out - timezone.timedelta(
            minutes=timesheet.work_time.working_minutes // 2
        ),
        SECOND_HALF: timesheet.expected_punch_out,
        FULL_DAY: timesheet.expected_punch_out,
    }.get(
        travel_day.travel_attendance.working_time
    )
    return timestamp


def get_punch_in(timesheet, travel_day):
    timestamp = {
        FIRST_HALF: timesheet.expected_punch_in,
        SECOND_HALF: timesheet.expected_punch_in + timezone.timedelta(
            minutes=timesheet.work_time.working_minutes // 2
        ),
        FULL_DAY: timesheet.expected_punch_in,
    }.get(
        travel_day.travel_attendance.working_time
    )
    return timestamp


def calculate_balance(user, start, end, travel_setting, part=FULL_DAY):
    attendance_setting = user.attendance_setting
    balance = 0
    # Test for if user has no shift
    shift_exists = all(get_shift_details(user, start, end))
    if not shift_exists:
        return relativedelta(
            dt1=end,
            dt2=start
        ).days + 1  # Because the date is start-date exclusive.
    offday_applicable = travel_setting.can_apply_in_offday
    holiday_applicable = travel_setting.can_apply_in_holiday
    for date in rrule(freq=DAILY, dtstart=start, until=end):
        # check for holiday,
        # if no holiday check for workday
        # if no workday (i.e. workday) check for if settings count off-days too.
        if not holiday_applicable:
            is_holiday = user.is_holiday(date)
            if is_holiday:
                continue
        wd = attendance_setting.work_day_for(date)
        if wd:
            balance += 1
        elif offday_applicable:
            balance += 1
    return balance
