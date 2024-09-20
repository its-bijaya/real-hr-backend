"""@irhrs_docs
Util for manipulating timesheets and overtimes.
"""
import logging
from datetime import timedelta

from dateutil.rrule import rrule, DAILY
from django.db.models import QuerySet, Q, Sum
from django.utils import timezone

from irhrs.attendance.constants import FIRST_HALF, SECOND_HALF, FULL_LEAVE, \
    NO_LEAVE, CREDIT_HOUR, TIME_OFF, CREDIT_TIME_OFF
from irhrs.attendance.models import TimeSheet
from irhrs.core.utils.common import get_today, combine_aware
from irhrs.leave.constants.model_constants import APPROVED
from irhrs.leave.constants.model_constants import (
    FIRST_HALF as FIRST_HALF_LEAVE,
    SECOND_HALF as SECOND_HALF_LEAVE,
    FULL_DAY as FULL_DAY_LEAVE
)
from irhrs.leave.models.request import LeaveRequest, LeaveSheet
from irhrs.leave.utils.leave_request import is_hourly_account

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_shift_timings(user, date_):
    has_attendance = hasattr(user, 'attendance_setting')
    if has_attendance:
        attendance_setting = user.attendance_setting
    else:
        logger.warning("Timesheet generation failed as no attendance setting.")
        return None, None

    shift = attendance_setting.work_shift_for(date_)
    if not shift:
        return None, None
    workday = attendance_setting.work_day_for(date_)
    if not workday:
        return shift, None
    timings = workday.timings.all()
    return shift, timings


def create_leave_timesheet_for_user_per_day(leave_request, date_):
    if leave_request.status != APPROVED:
        return
    user = leave_request.user
    shift, timings = get_shift_timings(user, date_)

    if not shift:
        return

    leave_request.refresh_from_db()
    if not timings:
        # Assume Leave and Create into offday.
        obj, created = TimeSheet.objects.update_or_create(
            timesheet_for=date_,
            timesheet_user=user,
            work_shift=shift,
        )
        logger.debug(
            f"{'Created' if created else 'Updated'} "
            f"Leave timesheet for {user} on {date_}"
        )
        obj.leave_coefficient = FULL_LEAVE
        obj.save()
        obj.fix_entries()
        return

    for timing in timings:
        neo_punch_in, neo_punch_out, leave_coefficient, hour_off_coefficient = get_in_out_times(
            user,
            date_,
            timing
        )
        in_out_times = {
            'expected_punch_in': neo_punch_in,
            'expected_punch_out': neo_punch_out
        }
        try:
            obj, created = TimeSheet.objects.update_or_create(
                timesheet_for=date_,
                timesheet_user=user,
                work_time=timing,
                work_shift=shift,
                defaults={
                    **in_out_times,
                    'hour_off_coefficient': hour_off_coefficient
                }
            )
            logger.debug(
                f"{'Created' if created else 'Updated'} "
                f"Leave timesheet for {user} on {date_}"
            )
            obj.leave_coefficient = leave_coefficient
            obj.hour_off_coefficient = hour_off_coefficient
            obj.save()
            obj.fix_entries()

        except TimeSheet.MultipleObjectsReturned:
            logger.warning(
                f"Multiple timesheets found for {date_}"
            )
            count, _ = TimeSheet.objects.filter(
                timesheet_for=date_).delete()
            logger.warning(
                f"Deleted {count} timesheets for {date_} for {user}"
            )
            logger.warning(
                f"Creating timesheets for {user} on {date_}"
            )
            TimeSheet.objects.create(
                timesheet_for=date_,
                timesheet_user=user,
                work_time=timing,
                work_shift=shift,
                leave_coefficient=leave_coefficient,
                **in_out_times
            )
            logger.warning(
                f"Created on Leave timesheet for {user} on {date_}"
            )


def get_in_out_times(user, leave_for, timing):
    """
    :param user: Timesheet User
    :param leave_for: Date to calculate timings for
    :param timing: Shift timing
    :return: expected_in, expected_out, leave_coefficient, hour_off_coefficient
    """
    if not timing:
        return None, None, NO_LEAVE, ""
    actual_in = combine_aware(
        leave_for,
        timing.start_time
    )
    actual_out = combine_aware(
        leave_for,
        timing.end_time
    )
    base_qs = LeaveSheet.objects.filter(
        Q(
            request__user=user
        ) & Q(
            leave_for=leave_for
        ) & Q(
            request__status=APPROVED
        ) & ~Q(
            request__is_deleted=True
        )
    ).order_by(
        'start'
    )
    leave_coefficient, re_actual_in, re_actual_out = get_leave_coefficient(actual_in, actual_out,
                                                                           base_qs, timing)

    # Hour off coefficient is CREDIT_HOUR if any of the leave_accounts is credit type.
    if base_qs.filter(
        request__leave_rule__leave_type__category__in=(TIME_OFF, CREDIT_HOUR)
    ):
        hour_off_coefficient = CREDIT_HOUR
    else:
        hour_off_coefficient = ''
    return re_actual_in, re_actual_out, leave_coefficient, hour_off_coefficient


def get_leave_coefficient(actual_in, actual_out, base_qs, timing):
    if timing.extends:
        # for night shift where extends=True, add 1 day so that there's no second half issue while
        # assigning shift from admin side.
        actual_out = actual_out + timedelta(days=1)
    re_actual_in, re_actual_out = actual_in, actual_out
    # if shift start timing is start or shift end timing is end, then process
    leave_coefficient = NO_LEAVE
    for start, end, request_id in base_qs.values_list(
        'start', 'end','request'
    ).order_by('start'):
        if timing.extends:
            end = end + timedelta(days=1)
        if re_actual_in == start:
            re_actual_in = end
        if re_actual_out == end:
            re_actual_out = start

        #leave coefficient form leave request
        leave_request = LeaveRequest.objects.get(id=request_id)
        if leave_request.part_of_day == "full":
            leave_coefficient = FULL_LEAVE
        elif leave_request.part_of_day == "first":
            leave_coefficient = FIRST_HALF
        elif leave_request.part_of_day == "second":
            leave_coefficient = SECOND_HALF

    if set(base_qs.values_list("request__part_of_day", flat=True)) == {"first", "second"}:
        leave_coefficient = FULL_LEAVE
        
    re_actual_out = max(re_actual_out, re_actual_in)
    # check leave coefficient for hourly leave request
    if leave_coefficient == NO_LEAVE:
        leave_coefficient = get_hourly_coefficient(
            base_qs,
            timing
        )
    return leave_coefficient, re_actual_in, re_actual_out

def get_hourly_coefficient(base_qs, timing):
    if not base_qs:
        return NO_LEAVE

    from datetime import datetime

    # converting datetime.time to datetime.datetime
    leave_for = base_qs.first().start.date()
    start_time = datetime.combine(leave_for, timing.start_time)
    end_time = datetime.combine(leave_for, timing.end_time)

    half_time = start_time + (end_time - start_time)/2

    current_tz = timezone.get_current_timezone()
    half_time = timezone.make_aware(half_time, current_tz)
    start_time = timezone.make_aware(start_time, current_tz)

    leave_days = base_qs.aggregate(
        days=Sum("balance"),
    ).get("days") or 0

    leave_start = base_qs.order_by("-start").first().start
    leave_end = base_qs.order_by("-end").first().end
    first_half = leave_start <= start_time and leave_end >= half_time
    if leave_days >= 1:
        return FULL_LEAVE
    elif leave_days == 0.5:
        return FIRST_HALF if first_half else SECOND_HALF
    return NO_LEAVE

def create_leave_timesheet_for_user(leave_request):
    if leave_request.status != APPROVED:
        return

    leave_request.refresh_from_db()
    date_range = map(
        lambda d: d.date(),
        rrule(
            freq=DAILY,
            dtstart=leave_request.start.date(),
            until=leave_request.end.date()
        )
    )

    for date_ in filter(
            lambda d: d <= get_today(),
            date_range
    ):
        create_leave_timesheet_for_user_per_day(leave_request, date_)


def revert_hour_off_for(leave_request):
    if not is_hourly_account(leave_request.leave_account):
        return
    user = leave_request.user
    leave_request.refresh_from_db()
    date_range = rrule(
        freq=DAILY,
        dtstart=leave_request.start.date(),
        until=leave_request.end.date()
    )
    leave_begin, leave_end = leave_request.start.astimezone().time(), leave_request.end.astimezone().time()
    for timesheet in TimeSheet.objects.filter(
        timesheet_for__in=date_range,
        timesheet_user=user,
    ).exclude(
        hour_off_coefficient=''
    ):
        timing = timesheet.work_time
        date_ = timesheet.timesheet_for
        timing_start, timing_end = timing.start_time, timing.end_time
        if timing_start == leave_begin:
            timesheet.expected_punch_in = combine_aware(
                timesheet.timesheet_for, timing_start
            )
        elif timing_end == leave_end:
            timesheet.expected_punch_out = combine_aware(
                timesheet.timesheet_for, timing_end
            )
        if timesheet.hour_off_coefficient == CREDIT_HOUR:
            timesheet.hour_off_coefficient = ''
        if timesheet.leave_coefficient == FULL_LEAVE:
            timesheet.leave_coefficient = NO_LEAVE
        timesheet.save()


def revert_timesheet_for_leave(leave_request):
    """
    Util for reverting timesheets created by
    `create_leave_timesheet_for_user` after the deletion of approved leave
    requests.
    :caution: To be used with care, as this is performed just before the leave
    request is deleted and not otherwise.
    :param leave_request: Leave Request to be deleted
    :return: None
    """
    if leave_request.status != APPROVED:
        return
    # safely keep the leave_request's part e.g first half or second half.
    part = leave_request.part_of_day
    user = leave_request.user
    date_range = rrule(
        freq=DAILY,
        dtstart=leave_request.start.date(),
        until=leave_request.end.date()
    )
    for date_ in date_range:
        timesheets = user.timesheets.filter(
            timesheet_for=date_,
        )
        updated_count = 0
        for timesheet in timesheets.filter(
            timesheet_for__lte=get_today()
        ):

            # The expected_punch_in and expected_punch_out was not reverted.
            # Hence, the issue was not seen in FULL LEAVE, rather only `first`
            # and `second` half leaves.
            re_actual_in, re_actual_out, leave_coefficient, hour_off_coefficient = get_in_out_times(
                user=timesheet.timesheet_user,
                leave_for=timesheet.timesheet_for,
                timing=timesheet.work_time
            )
            timesheet.expected_punch_in = re_actual_in
            timesheet.expected_punch_out = re_actual_out
            timesheet.leave_coefficient = leave_coefficient
            timesheet.hour_off_coefficient = hour_off_coefficient
            timesheet.save(update_fields=[
                'expected_punch_in', 'expected_punch_out',
                'leave_coefficient', 'hour_off_coefficient',
            ])
            updated_count += 1

        timesheets.filter(
            timesheet_for__gt=get_today()
        ).delete()

        logger.info(f"Reverted {updated_count} timesheets to `No Leave` for "
                    f"the following ids:"
                    f"{timesheets.values_list('id', flat=True)}")


def empty_timesheets(timesheets: QuerySet) -> None:
    """
    Removes all timesheet_entries, resets punch_in/punch_out/punch_in_delta/punch_out_delta
    but preserves coefficients.
    :param timesheets: timesheets queryset
    """
    timesheets.update(
        punch_in=None,
        punch_out=None,
        punch_in_delta=None,
        punch_out_delta=None,
        punctuality=None,
        is_present=False,
        worked_hours=None,
        unpaid_break_hours=None,
    )
    from irhrs.attendance.models import TimeSheetEntry, OvertimeEntry
    TimeSheetEntry.objects.filter(
        timesheet__in=timesheets
    ).delete()
    OvertimeEntry.objects.filter(
        timesheet__in=timesheets
    ).delete()
