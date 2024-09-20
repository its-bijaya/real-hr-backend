"""@irhrs_docs"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Case, When, Value, F
from django.template.defaultfilters import pluralize
from django.utils import timezone

from irhrs.attendance.models import WorkDay
from irhrs.attendance.models.workshift import WorkTiming
from irhrs.attendance.utils.helpers import get_weekday, get_week_range
from irhrs.core.utils.common import combine_aware, get_today

USER = get_user_model()


def calculate_time_difference(work_timing):
    """
    Return minutes difference between two times.
    work_timing: work day whose time difference is to be calculated
    :return: minutes between start time and end time
    """
    today = timezone.now().date()
    tomorrow = timezone.now().date() + timezone.timedelta(days=1)

    # calculate work shift minutes
    delta = (timezone.datetime.combine(
        tomorrow,
        work_timing.end_time
    ) - timezone.datetime.combine(
        today,
        work_timing.start_time
    )) if work_timing.extends else (timezone.datetime.combine(
        today,
        work_timing.end_time
    ) - timezone.datetime.combine(
        today,
        work_timing.start_time
    ))
    return delta.total_seconds() // 60


def has_work_day_changed(work_day, work_day_data):
    # check whether workday has changed or not
    has_changed = False
    old_timings = work_day.timings.all()
    new_timings = work_day_data.get('timings')
    if old_timings.count() != len(new_timings):
        return True
    for timing in new_timings:
        if not old_timings.filter(**timing).exists():
            has_changed = True
            break
    return has_changed


def create_work_day(data, work_shift):
    timings_data = data.pop('timings')
    day = WorkDay.objects.create(
        shift=work_shift,
        **data
    )
    timings = []

    for timing in timings_data:
        work_timing = WorkTiming(
            work_day=day,
            **timing
        )
        work_timing.working_minutes = calculate_time_difference(work_timing)
        timings.append(work_timing)

    WorkTiming.objects.bulk_create(timings)
    return day


def create_work_days(days, work_shift):
    for day in days:
        create_work_day(day, work_shift)


def find_conflicting_work_days(work_days):
    # find whether work days are conflicting
    def make_datetimes(days):
        shifts = []
        start_datetime = timezone.now().min
        for w_day in days:
            this_day = start_datetime + timezone.timedelta(
                days=w_day.get('day'))
            next_day = this_day + timezone.timedelta(days=1)

            start = timezone.datetime.combine(
                this_day,
                w_day.get('start_time')
            )
            end = timezone.datetime.combine(
                this_day if not w_day.get('extends', False) else next_day,
                w_day.get('end_time')
            )
            shifts.append((start, end))
        return shifts

    def check_conflicts(datetime_list):
        """
            :param datetime_list: List of sorted datetime(s) to check conflict
            :return: True/False
            Syntax:
            [
                (<start_timestamp>, <end_timestamp>),
                (<start_timestamp>, <end_timestamp>),
                ...
            ]
        """
        previous_end = None
        for entry in datetime_list:
            if not previous_end:
                previous_end = entry[1]
            elif entry[0] < previous_end:
                return True
            else:
                previous_end = entry[1]
        return False

    w_days = []
    for work_day in work_days:
        for timing in work_day.get('timings'):
            w_days.append({
                "day": work_day.get("day"),
                "start_time": timing.get("start_time"),
                "end_time": timing.get("end_time"),
                "extends": timing.get("extends")
            })
    datetime_list = sorted(make_datetimes(w_days), key=lambda x: x[0])

    if len(datetime_list) != len(set(datetime_list)):
        # for same start and end time pairs raise from here
        return True

    return check_conflicts(datetime_list)


def get_next_supervisor(user, recipient):
    current_authority = user.supervisors.filter(
        supervisor=recipient
    ).first()
    if getattr(current_authority, 'forward', None):
        next_order = current_authority.authority_order + 1
        return user.supervisors.filter(
            authority_order=next_order
        ).first()
    return None


def get_adjustment_request_forwarded_to(adjustment_request):
    return get_next_supervisor(
        adjustment_request.sender,
        adjustment_request.receiver
    )


def get_adjustment_request_receiver(user):
    """
    :param user: user whose adjustment request receiver is to be returned
    :return: userdetail who is adjustment request receiver
    """
    sup_obj = user.user_supervisors.filter(authority_order=1).first()
    return sup_obj.supervisor if sup_obj else None


def get_week(today):
    return get_week_range(dt=today)


def get_present_employees(date, filters=None):
    """
    Return present employees on any date
    """
    filters = filters or {}
    return USER.objects.filter(**filters).filter(
        timesheets__timesheet_for=date,
        timesheets__is_present=True,
    ).distinct()


def stringify_seconds(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '{:02d}:{:02d}:{:02d}'.format(h, m, s)


def signed_stringify_seconds(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    ret_string = '{:02d}:{:02d}:{:02d}'.format(abs(h), m, s)
    return f'-{ret_string}' if h < 0 else f'+{ret_string}'


def humanize_interval(interval, absolute=True):
    if not interval:
        return "00:00:00"
    elif isinstance(interval, timedelta):
        total_seconds = interval.total_seconds()
        value = abs(total_seconds) if absolute else total_seconds
        return stringify_seconds(int(value))
    elif isinstance(interval, float):
        return stringify_seconds(int(interval))
    elif isinstance(interval, int):
        return stringify_seconds(interval)
    return interval


def signed_humanize_interval(interval):
    if not interval:
        return "00:00:00"
    elif isinstance(interval, timedelta):
        total_seconds = interval.total_seconds()
    elif isinstance(interval, float):
        total_seconds = int(interval)
    else:
        total_seconds = int(interval)
    prefix = '+' if total_seconds >= 0 else '-'
    return prefix + humanize_interval(abs(total_seconds))


def chunk_interval(interval_string='00:00:00'):
    """
    Returns two adjacent intervals: Eg: 1 hour, 1 minute OR 15 minutes,
    2 seconds
    :param interval_string: output from humanize interval
    :return:
    """

    hh, mm, ss = map(int, interval_string.split(':'))
    chunks = list()
    if hh:
        chunks.append(f"{hh} hour{pluralize(hh)}")
    if mm:
        chunks.append(f'{mm} minute{pluralize(mm)}')
    if ss:
        chunks.append(f'{ss} second{pluralize(ss)}')
    return ', '.join(chunks)


def get_waiting_datetime(shift_end_time):
    """
    For given shift_end_time returns datetime till when we wait before
    taking attendance entry as punch_in of another day
    """
    return shift_end_time + timezone.timedelta(hours=settings.OFFDAY_PUNCHOUT_WAITING_TIME)


def get_timing_info(dt, shift):
    """
    Return work timing and timesheet_for for given datetime and given shift

    :return { 'date': 'timesheet_for', 'timing': WorkTime Instance }
    """

    if shift is None:
        return {
            "date": dt.date(),
            "timing": None
        }

    dt = dt.astimezone()
    dt_weekday = get_weekday(dt)
    weekday_date_map = {
        dt_weekday: dt.date(),
        dt_weekday - 1: (dt - timezone.timedelta(days=1)).date()
    }

    timing_date_map = dict()
    timing_for_given_day_exists = False

    for day in shift.days:
        for timing in day.work_times:
            date_ = weekday_date_map.get(day.day)
            if not date_:
                # if date is out of required range ignore that timing
                continue

            # if date_ == dt.date():
            timing_for_given_day_exists = True

            start = combine_aware(date_, timing.start_time)
            end = combine_aware(date_ + timezone.timedelta(days=1), timing.end_time) \
                if timing.extends else combine_aware(date_, timing.end_time)

            timing_date_map.update({
                start: {'date': date_, 'timing': timing},
                end: {'date': date_, 'timing': timing}
            })

    # OFF DAY
    if not timing_for_given_day_exists:

        if timing_date_map:
            last_shift_end_time = max(timing_date_map)
            # wait until this time before declaring missing punch out
            waiting_time = get_waiting_datetime(last_shift_end_time)
        else:
            waiting_time = None

        if waiting_time and dt <= waiting_time:
            # Punch is for previous timing
            return timing_date_map[last_shift_end_time]
        else:
            # Punch is for off day
            return {'date': dt.date(), 'timing': None}

    # WORKING DAYS
    probable_timing = min(timing_date_map.keys(), key=lambda t: abs(t - dt))

    return timing_date_map[probable_timing]


def double_date_conflict_checker(queryset, new_from, new_to):
    # conflict against undefined applicable to

    queryset = queryset.annotate(
        new_applicable_to=Case(
            When(applicable_to__isnull=True, then=Value(get_today())),
            default=F('applicable_to'),
        )
    )
    if new_to:
        return queryset.filter(
            applicable_from__lt=Value(new_to),
            new_applicable_to__gt=Value(new_from)
        ).exists()
    # this is possible for new indefinite entry only.
    currently_active = queryset.order_by(
        '-new_applicable_to'
    ).first()
    return currently_active and (
        new_from <= currently_active.new_applicable_to
    )

def get_row_data(row):
    email = str(row[0]).strip()
    bio_id = row[1]
    device = str(row[2]).strip()
    return email, bio_id, device