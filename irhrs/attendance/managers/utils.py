import functools
from datetime import timedelta

from django.db import connection

from irhrs.attendance.constants import (
    UNCATEGORIZED, LATE_IN, EARLY_IN, TIMELY_IN, PUNCH_IN, EARLY_OUT, LATE_OUT,
    TIMELY_OUT, PUNCH_OUT, BREAK_IN, BREAK_OUT,
    FULL_LEAVE, ATT_ADJUSTMENT, METHOD_IMPORT)
from irhrs.core.utils import grouper
from irhrs.core.utils.common import get_today
from django.conf import settings



def tuple_to_str(tup):
    '''Remove the last , in tuple representation for passing tuples to SQL'''
    if len(tup) == 1:
        return f'({repr(tup[0])})'
    return tup


def trim_timestamps(timestamps, min_diff=1, keep_latest=True):
    assert min_diff > 0

    timestamps = [d.replace(microsecond=0) for d in timestamps]
    timestamps = list(sorted(timestamps, reverse=keep_latest))

    new_timestamps = []

    for i, timestamp in enumerate(timestamps):
        if i != 0:
            prev = timestamps[i - 1]
            diff = (prev - timestamp).total_seconds()

            if diff > min_diff:
                new_timestamps.append(timestamp)
        else:
            new_timestamps.append(timestamp)
    return sorted(new_timestamps)


def get_total_unpaid_break_time(timesheet):
    base_qs = timesheet.timesheet_entries.filter(is_deleted=False).order_by('timestamp')
    outs = list(base_qs.filter(entry_type=BREAK_OUT))
    ins = list(base_qs.filter(entry_type=BREAK_IN))
    pairs = zip(outs, ins)
    unpaid_breaks = 0
    try:
        unpaid_break_types = settings.UNPAID_BREAK_TYPES
    except AttributeError:
        unpaid_break_types = ('',)
    for _out, _in in pairs:
        if _out.remark_category in unpaid_break_types:
            unpaid_breaks = unpaid_breaks + abs((_out.timestamp - _in.timestamp).total_seconds())
    return timedelta(seconds=unpaid_breaks)


def reduce_unpaid_breaks_from_work_hours(timesheet):
    res = get_total_unpaid_break_time(timesheet)
    # handles first punch in of the day
    timesheet.unpaid_break_hours = timedelta(0)
    if timesheet.punch_out:
        timesheet.worked_hours = (timesheet.punch_out - timesheet.punch_in)
    if res:
        timesheet.unpaid_break_hours = res
        timesheet.worked_hours -= timesheet.unpaid_break_hours
    timesheet.save()


def is_valid_for_late_in_notification(punch_in_entry):
    # Rule1: Do not send notification for past dates.
    if punch_in_entry.timestamp.astimezone().date() < get_today():
        return False
    # Rule2: Do not send notification for import or adjustments
    if punch_in_entry.entry_method in (ATT_ADJUSTMENT, METHOD_IMPORT):
        return False
    return True


def fix_entries_on_commit(instance, send_notification=True):
    entries = list(instance.timesheet_entries.filter(is_deleted=False).order_by('timestamp'))
    if not entries:
        return False
    punch_in_entry = entries.pop(0)
    punch_in_entry_old_category = punch_in_entry.category

    # value that determines whether timesheet entry can be categorized or not
    # if the day is OFFDAY or HOLIDAY or On FULL_LEAVE this value will be true
    uncategorized = False

    if instance.timesheet_user.is_offday(
            instance.timesheet_for
    ) or instance.timesheet_user.is_holiday(
        instance.timesheet_for
    ):
        uncategorized = True
        category = UNCATEGORIZED

        # compensatory leaves counts are incremented by tasks
    else:
        work_time = instance.work_time
        work_shift = instance.work_shift
        if work_time and work_shift:
            start_time_grace = work_shift.start_time_grace
            punch_in_dt = punch_in_entry.timestamp
            start_time_dt = instance.expected_punch_in
            if punch_in_dt > (start_time_dt + start_time_grace):
                category = LATE_IN
            elif punch_in_dt < start_time_dt:
                category = EARLY_IN
            else:
                category = TIMELY_IN
            instance.punch_in_delta = punch_in_dt - start_time_dt
        else:
            category = UNCATEGORIZED
        punctuality = {
            EARLY_IN: 100.0,
            TIMELY_IN: 100.0,
            LATE_IN: get_punctuality(instance.expected_punch_in, punch_in_entry.timestamp),
            UNCATEGORIZED: None
        }.get(category)
        instance.punctuality = punctuality
    punch_in_entry.category = category
    punch_in_entry.entry_type = PUNCH_IN
    punch_in_entry.save()

    instance.punch_in = punch_in_entry.timestamp
    if category == UNCATEGORIZED:
        instance.punch_in_delta = None
        instance.save(update_fields=['punch_in', 'punch_in_delta'])
    else:
        instance.save(update_fields=[
            'punch_in', 'punch_in_delta', 'punctuality'
        ])

    if (
            punch_in_entry_old_category != punch_in_entry.category
            and punch_in_entry.category == LATE_IN
            and send_notification
    ):
        # check the old category with new one so the notification is not sent
        # every time, the category is re-calculated.
        if is_valid_for_late_in_notification(punch_in_entry):
            from irhrs.attendance.tasks.send_notifications import \
                send_late_in_notification_email
            send_late_in_notification_email(instance)
    try:
        punch_out_entry = entries.pop(-1)
    except IndexError:
        pass
    else:  # if no exceptions
        work_time = instance.work_time
        work_shift = instance.work_shift
        if work_time and work_shift and not uncategorized:
            end_time_grace = work_shift.end_time_grace
            punch_out_dt = punch_out_entry.timestamp
            end_time_dt = instance.expected_punch_out

            if punch_out_dt < (end_time_dt - end_time_grace):
                category = EARLY_OUT
            elif punch_out_dt > end_time_dt:
                category = LATE_OUT
            else:
                category = TIMELY_OUT
            instance.punch_out_delta = punch_out_dt - end_time_dt
        else:
            category = UNCATEGORIZED
        punch_out_entry.category = category
        punch_out_entry.entry_type = PUNCH_OUT
        punch_out_entry.save()

        instance.punch_out = punch_out_entry.timestamp
        if category == UNCATEGORIZED:
            instance.punch_out_delta = None
            instance.save(update_fields=['punch_out', 'punch_out_delta'])
        else:
            instance.save(update_fields=['punch_out', 'punch_out_delta'])
        for pair in grouper(entries, 2):
            break_out, break_in = pair
            break_out.entry_type = BREAK_OUT
            break_out.category = UNCATEGORIZED
            break_out.save(update_fields=['entry_type', 'category'])
            if break_in:
                break_in.entry_type = BREAK_IN
                break_in.category = UNCATEGORIZED
                break_in.save(update_fields=['entry_type', 'category'])
    reduce_unpaid_breaks_from_work_hours(instance)


def get_punctuality(expected_in, actual_in):
    initial_punctuality = 100.0
    decrement_by = 100 / 60  # Reduce 100 percent for every 60 minutes
    if not all([expected_in, actual_in]):
        return None
    if expected_in >= actual_in:
        return initial_punctuality  # should not occur. Just in case.
    deviation = (actual_in - expected_in).total_seconds()
    reduce_by = deviation / 60 * decrement_by
    return 0 if reduce_by >= 100.0 else round((
            initial_punctuality - reduce_by
    ), 2)
