import datetime
from django.db import transaction

from dateutil.parser import parse
from dateutil.rrule import rrule, DAILY
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

from django_q.tasks import async_task

from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.tasks.send_notifications import send_populate_timesheet_notifications
from irhrs.attendance.utils.shift_planner import get_shift_for_user
from irhrs.attendance.utils.travel_attendance import manage_travel_attendances_for_today
from irhrs.core.redix import get_a_lock
from irhrs.attendance.constants import DONT_SYNC, OFFDAY
from irhrs.attendance.models import TimeSheet, AttendanceSource
from irhrs.core.utils.common import get_today, combine_aware
from irhrs.leave.constants.model_constants import APPROVED
from irhrs.leave.models import LeaveRequest
from irhrs.leave.models.request import LeaveSheet
from irhrs.leave.utils.timesheet import create_leave_timesheet_for_user_per_day, get_in_out_times

from irhrs.attendance.constants import (
    FIRST_HALF, FULL_LEAVE,
    NO_LEAVE, SECOND_HALF
)
from irhrs.leave.constants.model_constants import (
    FIRST_HALF as FIRST,
    SECOND_HALF as SECOND,
    FULL_DAY as FULL
)
from irhrs.training.utils.util import manage_training_attendances_for_today

logger = logging.getLogger(__name__)
USER = get_user_model()


def populate_timesheets(date_=''):
    try:
        date_ = parse(date_).date()
    except (TypeError, ValueError):
        date_ = timezone.now().astimezone().date()
    user_count, created_count, updated_count, failed_count = TimeSheet.objects.create_timesheets(date_)
    logger.info(
        f'Populated timesheets for {user_count} users and created count is '
        f'{created_count} and '
        f'updated count is {updated_count}  '
        f'and failed count is {failed_count} '
        f'for {date_} ')
    async_task(manage_travel_attendances_for_today, date_)
    async_task(manage_training_attendances_for_today, date_)
    leave_requests_for_the_day = LeaveRequest.objects.filter(
        is_deleted=False,
        status=APPROVED,
        sheets__in=LeaveSheet.objects.filter(
            leave_for=date_
        )
    )
    for leave_request in leave_requests_for_the_day:
        create_leave_timesheet_for_user_per_day(
            leave_request, date_
        )
    return {
        'created': created_count,
        'updated': updated_count,
        'failed': failed_count,
        'for': date_,
        'user': user_count,
        'leave_timesheet_updated': leave_requests_for_the_day.count()
    }


def sync_attendance(*args, **kwargs):
    """
    Starts tasks to sync data from realhrsoft.attendance.devices.
    Excludes devices with sync_method set to DONT_SYNC.

    :return: Returns a number of devices sent for sync.
    """
    sent_for_sync = 0
    devices = AttendanceSource.objects.exclude(sync_method=DONT_SYNC)

    for device in devices:
        # separate tasks for each devices so that multiple django_q
        # workers can do them in parallel
        logger.info('passing device {} for sync'.format(device))
        sync_for_device(device, *args, **kwargs)
        sent_for_sync += 1
    return "Sent for Sync %s" % sent_for_sync


def sync_for_device(device, *args, **kwargs):
    total_synced = 0

    assert device.sync_method != DONT_SYNC

    if device.handler is None:
        logger.warning('No handler found for device {}'.format(device))
        return total_synced

    key = 'syncing_device_{}'.format(device.id)
    # Temp: timeout for 12 mins and schedular at 15 mins .
    lock = get_a_lock(key, timeout=720)
    if lock.acquire(blocking=False):
        logger.info('Acquired sync lock for {}'.format(device))
        try:
            synced = device.handler.sync()
            total_synced += synced
        except Exception as e:
            logger.error(e)
        finally:
            lock.release()
    else:
        logger.warning("Couldn't acquire lock for {}".format(device))

    return total_synced


def is_timesheet_deletable(timesheet):
    overtime_exists = hasattr(timesheet, 'overtime')
    credit_entries = timesheet.credit_entries.exists()
    return not (overtime_exists or credit_entries)


def parse_raw_date(date_raw):
    if isinstance(date_raw, datetime.datetime):
        return date_raw.astimezone().date()
    elif isinstance(date_raw, datetime.date):
        return date_raw
    try:
        return parse(date_raw).astimezone().date()
    except (TypeError, ValueError):
        return False


def populate_timesheet_for_user(
        user, start_date_raw, end_date_raw,
        notify='true', authority=0
):
    """
    can be exposed to dj-admin scheduling
    :param user: user or user id
    :param start_date_raw: start date in any format
    :param end_date_raw: end_date in any format
    :param notify: 'true' if notification is desired.
    :param authority: Override Value (for overtime/credit conflict)
    :return: task result.
    """
    failed_count = created_count = updated_count = 0
    terminal_errors = {}
    if isinstance(user, str) or isinstance(user, int):
        try:
            user = USER.objects.get(id=user)
        except (USER.DoesNotExist, TypeError, ValueError):
            terminal_errors['user'] = 'The user could not be recognized.'
    elif isinstance(user, USER):
        user = user
    else:
        terminal_errors['user'] = 'The user could not be recognized.'

    start_date = parse_raw_date(start_date_raw)
    end_date = user.detail.last_working_date or parse_raw_date(end_date_raw)
    if not start_date:
        terminal_errors['start_date'] = 'The start_date could not be recognized.'
    if not end_date:
        terminal_errors['end_date'] = 'The end_date could not be recognized.'
    if terminal_errors:
        return False, terminal_errors

    existing_timesheet = TimeSheet.objects.filter(
        timesheet_for__range=(start_date, end_date),
        timesheet_user=user
    )
    ignore_dates = tuple(existing_timesheet.values_list('timesheet_for', flat=True))
    date_generator = filter(
        lambda _dt: _dt <= get_today(),
        map(
            lambda _dt: _dt.date(),
            rrule(
                freq=DAILY,
                dtstart=start_date,
                until=end_date
            )
        )
    )
    for ts_date in date_generator:
        if ts_date in ignore_dates:
            continue
        _, created_cnt, updated_cnt, created = TimeSheet.objects._create_or_update_timesheet_for_profile(
            user=user,
            date_=ts_date
        )
        created_count += created_cnt
        updated_count += updated_cnt
        failed_count += 0 if created else 1
    processed_timesheets = dict()
    for timesheet in existing_timesheet:
        if timesheet.id in processed_timesheets:
            continue
        changes = []
        work_shift = get_shift_for_user(user, timesheet.timesheet_for)
        # user.attendance_setting.work_shift_for(timesheet.timesheet_for)
        if work_shift != timesheet.work_shift:
            changes.append('WS')
            timesheet.work_shift = work_shift
        work_day = user.attendance_setting.work_day_for(timesheet.timesheet_for)
        if not work_day:
            continue
        has_multiple_timings = work_day.timings.count() >= 2
        if has_multiple_timings:
            logger.warning("Unhandled multiple timings during time sheet regeneration")
            continue
        timing = work_day.timings.first()
        if timing != timesheet.work_time:
            changes.append('WT')
            timesheet.work_time = timing
        expected_punch_in, expected_punch_out, leave_coefficient, hour_off_coefficient = get_in_out_times(
            user=user, leave_for=timesheet.timesheet_for, timing=timing
        )
        if expected_punch_in != timesheet.expected_punch_in:
            timesheet.expected_punch_in = expected_punch_in
            changes.append('EPI')
        if expected_punch_out != timesheet.expected_punch_out:
            timesheet.expected_punch_out = expected_punch_out
            changes.append('EPO')
        if leave_coefficient != timesheet.leave_coefficient:
            timesheet.leave_coefficient = leave_coefficient
            changes.append('LC')
        if hour_off_coefficient != timesheet.hour_off_coefficient:
            timesheet.hour_off_coefficient = hour_off_coefficient
            changes.append('HOC')
        processed_timesheets[timesheet.id] = "|".join(changes)
        if changes:
            timesheet.save()
            if authority or not is_timesheet_deletable(timesheet):
                fix_entries_on_commit(timesheet, send_notification=(notify == 'true'))
    return True, {
        "created_count": created_count,
        "updated_count": updated_count,
        "failed_count": failed_count,
        'result': processed_timesheets,
        'user': user,
        'start_date': start_date,
        'end_date': end_date
    }


def timesheet_regenerate_broker(*args, **kwargs):
    success, result = populate_timesheet_for_user(
        *args, **kwargs
    )
    # Set False to deactivate
    if not kwargs.get('notify') == 'false':
        send_populate_timesheet_notifications(success, result)

# '2021-01-01', '2021-01-31', '1,2,3'


def populate_unique_time_sheets(date_from='', date_to='', user_list=''):
    date_start = parse_raw_date(date_from)
    if not date_start:
        date_start = get_today()

    date_until = parse_raw_date(date_to)
    if not date_until:
        date_until = get_today()

    user_ids = map(int, user_list.split(',')) if user_list else []
    date_iterator = list(
        map(
            lambda _dt: _dt.date(),
            rrule(
                freq=DAILY,
                dtstart=date_start,
                until=date_until
            )
        )
    )
    result_set = {}
    valid_users = USER.objects.filter(id__in=user_ids)
    for user in valid_users:
        user_result = {}
        for date in date_iterator:
            timesheet = TimeSheet.objects.filter(
                timesheet_for=date,
                timesheet_user=user
            ).first()
            if not timesheet:
                _, created_count, _, _ = (
                    TimeSheet.objects._create_or_update_timesheet_for_profile(user, date)
                )
                user_result[str(date)] = created_count
                continue
            shift = get_shift_for_user(user, date)
            update_values = {
                'work_shift': shift,
                'work_time': None,
                'coefficient': OFFDAY,
                'expected_punch_in': None,
                'expected_punch_out': None,
            }
            try:
                # if shift is None --> AttributeError | if days is empty -> IndexError
                day = shift.days[0]
            except (AttributeError, IndexError):
                day = None
            if day:
                for time in day.work_times:
                    update_values['coefficient'] = TimeSheet.objects._get_coefficient(
                        user, date
                    )
                    update_values.update({
                        'expected_punch_in': combine_aware(
                            date,
                            time.start_time
                        ),
                        'expected_punch_out': combine_aware(
                            date + timezone.timedelta(days=1),
                            time.end_time
                        ) if time.extends else combine_aware(
                            date,
                            time.end_time
                        )
                    })
            else:
                update_values['coefficient'] = TimeSheet.objects._get_coefficient(user, date)
            for attr, new_value in update_values.items():
                setattr(timesheet, attr, new_value)
            timesheet.save()
            user_result[str(date)] = update_values
        result_set[user.full_name] = user_result
    return result_set


@transaction.atomic()
def correct_leave_timesheets(for_date='')->None:
    """
    corrects timesheets of users whose leave has been approved for
    particular day (default is today), but their's timesheet coefficient
    has not been updated.

    The updated timesheet coefficient values is taken from that day's
    leave request's coefficient. When a particular day has both first
    half and second half leave request, leave coefficient is updated to
    FULL_LEAVE.
    """
    #get users whose leave is approved for today.
    try:
        for_date = parse(for_date).date()
    except (TypeError, ValueError):
        for_date = timezone.now().astimezone().date()

    users = LeaveSheet.objects.filter(
        leave_for=for_date,
        request__status=APPROVED
    ).values_list("request__user", flat=True)

    #get timesheet of those users whose leave coefficient is no_leave
    timesheets = TimeSheet.objects.filter(
        timesheet_user__in=users,
        timesheet_for=for_date,
        leave_coefficient=NO_LEAVE
    )
    if not timesheets:
        return

    #update the timesheet leave coefficient of those users from
    #leave_request's coefficient
    for timesheet in timesheets:
        leave_sheets = LeaveSheet.objects.filter(
            leave_for=for_date,
            request__user=timesheet.timesheet_user
        ).order_by("start")
        parts_of_day = list(
            leave_sheets.values_list("request__part_of_day", flat=True)
        )
        #part_of_day from leave_request is mapped to
        #corresponding value of timesheet leave_coefficient
        leave_coefficient_mapper = {
            FULL: FULL_LEAVE,
            FIRST: FIRST_HALF,
            SECOND: SECOND_HALF
        }
        if parts_of_day == [FIRST, SECOND]:
            leave_coefficient = FULL_LEAVE
        else:
            leave_coefficient = leave_coefficient_mapper.get(parts_of_day[0], NO_LEAVE)

        timesheet.leave_coefficient = leave_coefficient
        timesheet.save()
