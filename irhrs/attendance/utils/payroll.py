"""@irhrs_docs"""
from config import settings
from irhrs.attendance.models.breakout_penalty import TimeSheetPenaltyToPayroll
import typing
import itertools
from datetime import date, timedelta, datetime

from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Exists, OuterRef, Sum, F, Q, Case, When, IntegerField, Value, FilteredRelation, \
    FloatField, Prefetch
from django.db.models.functions import Coalesce
from django.utils import timezone

from irhrs.attendance.constants import (
    WORKDAY, CONFIRMED, REQUESTED, FORWARDED, APPROVED,
    FULL_LEAVE, NO_LEAVE,
    FIRST_HALF, SECOND_HALF, OFFDAY, HOLIDAY, DECLINED, CREDIT_HOUR)
from irhrs.attendance.models import TimeSheet, OvertimeClaim, AttendanceAdjustment, \
    TimeSheetApproval
from irhrs.attendance.utils.timesheet import simulate_timesheets
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import get_today
from irhrs.leave.models.request import LeaveSheet
from irhrs.leave.utils.payroll import get_half_credit_leave_sum
from irhrs.users.models import UserDetail

USER = get_user_model()

# Normalized time is total time multiplied by the OT rates
# If user has OT of 2 hrs, and rate for first hour is 1 and second hour is 2
# normalized_hours = 1*1 + 1*2 = 3


def _parse_date(date_) -> date:
    """parse to return date object"""
    if isinstance(date_, date):
        return date_
    else:
        dt = parse(date_)
        if isinstance(dt, datetime):
            return dt.date()
        return dt


def _get_time_sheets_for_user(user: USER):
    return TimeSheet.objects.filter(timesheet_user=user)


def _get_time_sheets_for_range(user: USER, start: date, end: date):
    return TimeSheet.objects.filter(timesheet_user=user, timesheet_for__gte=start, timesheet_for__lte=end)


def _get_overtime_duration(user: USER, start: date, end: date):
    """Claimed overtime duration and normalized duration for given user for given range"""
    queryset = OvertimeClaim.objects.filter(status=CONFIRMED).annotate(
        _confirmed_history=FilteredRelation(
            'overtime_histories', condition=Q(overtime_histories__action_performed=CONFIRMED)
        )
    ).filter(
        overtime_entry__timesheet__timesheet_user=user,
    )

    if settings.GENERATE_PAYROLL_EVEN_IF_OVERTIME_EXISTS:
        queryset = queryset.annotate(
            _confirmed_at=F('_confirmed_history__created_at')
        ).filter(
            _confirmed_at__date__gte=start,
            _confirmed_at__date__lte=end
        )
    else:
        queryset = queryset.filter(
            overtime_entry__timesheet__timesheet_for__gte=start,
            overtime_entry__timesheet__timesheet_for__lte=end
        )
    result = queryset.aggregate(
        claimed_duration=Sum('overtime_entry__overtime_detail__claimed_overtime'),
        normalized_duration=Sum('overtime_entry__overtime_detail__normalized_overtime'),
    )
    claimed_duration = result['claimed_duration'] or timedelta(0)
    normalized_duration = result['normalized_duration'] or timedelta(0)

    return claimed_duration, normalized_duration


def get_work_duration(user: USER, start: date, end: date) -> timedelta:
    """Duration worked by user in given time frame"""
    working_duration = _get_time_sheets_for_range(user, start, end).filter(
        punch_in__isnull=False, punch_out__isnull=False
    ).aggregate(
        working_duration=Sum(Coalesce(F('worked_hours'), timedelta(0)))
    ).get('working_duration') or timedelta(0)

    return working_duration


def get_overtime_seconds(user: USER, start: date, end: date):
    """Claimed overtime seconds and normalized seconds"""
    claimed_duration, normalized_duration = _get_overtime_duration(user, start, end)
    return claimed_duration.total_seconds(), normalized_duration.total_seconds()


def get_normal_work_seconds(user: USER, start: date, end: date):
    """
    Total seconds of work (previously excluding overtime now total logged seconds)
    """
    actual_work_duration = get_work_duration(user, start, end) or timedelta(0)
    # claimed_overtime_duration, _ = _get_overtime_duration(user, start, end)
    # return (actual_work_duration - claimed_overtime_duration).total_seconds()
    return actual_work_duration.total_seconds()


def get_hours_of_work(user: USER, start: date, end: date, name: str, hours=True):
    """
    Total hours worked by user for given range
    """
    if name == 'Overtime':
        _, normalized_overtime_seconds = get_overtime_seconds(user, start, end)
        return normalized_overtime_seconds / (60 * 60) if hours else normalized_overtime_seconds
    elif name == 'Total Hour Worked':
        total_worked_seconds = get_normal_work_seconds(user, start, end)
        return total_worked_seconds / (60 * 60) if hours else total_worked_seconds


def get_expected_work_hours(user: USER, start: date, end: date):
    queryset = _get_time_sheets_for_range(user=user, start=start, end=end)

    timesheet_data = queryset.aggregate(
        expected_work=Coalesce(
            Sum(
                Case(
                    When(
                        expected_punch_in__isnull=False,
                        expected_punch_out__isnull=False,
                        coefficient=WORKDAY,
                        then=F('work_time__working_minutes')
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            Value(0)
        )
    )
    return timesheet_data.get('expected_work')


def get_work_days_count_from_virtual_timesheets(virtual_timesheets, include_holiday_offday=False):
    sorted_values = sorted(virtual_timesheets.items(), key=lambda ts: ts[1])
    groups = itertools.groupby(sorted_values, key=lambda ts: ts[1])

    result = {key: len(list(val)) for key, val in groups}
    if not include_holiday_offday:
        return result.get("Workday") or 0.0
    return sum([result[key] for key in result])


def get_work_days_count_from_simulated_timesheets(user: USER, start: date, end: date):
    shift = nested_getattr(user, 'attendance_setting.work_shift')
    if not shift:
        return 0
    return get_work_days_count_from_virtual_timesheets(
        simulate_timesheets(user, shift, start, end)
    )


def get_working_days_from_organization_calendar(
    user: USER, start: date, end: date, include_holiday_offday: bool = False
):
    """
    Return total number of working days for given user for given date range.
    """

    first_time_sheet = _get_time_sheets_for_user(user).filter(
        timesheet_for__gte=start
    ).order_by('timesheet_for').first()

    last_time_sheet = _get_time_sheets_for_user(user).filter(
        timesheet_for__lte=end
    ).order_by('-timesheet_for').first()

    if not (first_time_sheet and last_time_sheet):
        return 0

    start_date = _parse_date(start)
    end_date = _parse_date(end)

    work_days_before_time_sheets = 0.0
    work_days_after_time_sheets = 0.0

    if first_time_sheet.timesheet_for > start_date:
        # took first time_sheet with ws into consideration because
        # when user joins in middle, there might be timesheets with no
        # work shift as shift can be assigned late
        first_time_sheet_with_ws = _get_time_sheets_for_user(user).filter(
            timesheet_for__gte=start
        ).order_by(
            'timesheet_for'
        ).filter(
            work_shift__isnull=False
        ).first() or first_time_sheet
        # we do not have time_sheets for all date range
        if first_time_sheet_with_ws.work_shift:
            # if there is work_shift then
            vt_before = simulate_timesheets(
                user,
                first_time_sheet_with_ws.work_shift,
                start_date,
                first_time_sheet.timesheet_for - timedelta(days=1),
                ignore_holidays=include_holiday_offday
            )
            work_days_before_time_sheets = get_work_days_count_from_virtual_timesheets(vt_before)

    if last_time_sheet.timesheet_for < end_date:
        if last_time_sheet.work_shift:
            # if there is work_shift then
            vt_after = simulate_timesheets(
                user,
                last_time_sheet.work_shift,
                last_time_sheet.timesheet_for + timedelta(days=1),
                end_date,
                ignore_holidays=include_holiday_offday
            )
            work_days_after_time_sheets = get_work_days_count_from_virtual_timesheets(vt_after)

    fil = dict()
    if not include_holiday_offday:
        fil = {
            'coefficient': WORKDAY
        }
    # group by is for multiple timings in a day
    return _get_time_sheets_for_range(user, start, end).filter(**fil).order_by().values(
        'timesheet_for'
    ).annotate(count=Count('timesheet_for')).count() + work_days_before_time_sheets + work_days_after_time_sheets


def get_users_by_status(status, user_key, user_filter=None):
    from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
    user_status = {user_key: status}

    return UserThinSerializer(
        USER.objects.filter(is_active=True, **user_status, **user_filter).distinct('id'),
        fields=('id', 'full_name', 'profile_picture', 'is_current', 'organization', 'job_title', 'is_online'),
        many=True).data


def get_adjustment_request_status_summary(
        organization_slug: str, start: date, end: date,
        user_filter: dict, exclude_filter: typing.Union[dict, None] = None
) -> dict:
    """
    Adjustment Request Status Summary
    ---------------------------------

    Adjustment request status summary for given filters

    :param organization_slug: organization slug of user
    :param start: start of range for timesheet_for
    :param end: end of range for timesheet_for
    :param user_filter: dictionary of filters to be applied on USER model
    :param exclude_filter: dictionary of filters to be excluded on USER model
    :return: counts of adjustment request status pending, forwarded, approved
    """
    fil = dict(detail__organization__slug=organization_slug)
    fil.update(user_filter)

    adjustment_filter = {f"timesheet__timesheet_user__{key}": value for key, value in fil.items()}
    adjustment_filter.update({
        'timesheet__timesheet_for__range': [start, end]
    })
    qs = AttendanceAdjustment.objects.filter(
        **adjustment_filter)
    if exclude_filter:
        qs = qs.exclude(**exclude_filter)

    stat = qs.aggregate(
        pending=Count('id', filter=Q(status=REQUESTED), distinct=True),
        forwarded=Count('id', filter=Q(status=FORWARDED), distinct=True),
        approved=Count('id', filter=Q(status=APPROVED), distinct=True),
    )

    user_fil = {}
    user_fil['detail__organization__slug'] = organization_slug
    user_fil['timesheets__timesheet_for__range'] = [start, end]

    user_ids = user_filter.get('id__in')

    if user_ids:
        user_fil['timesheets__timesheet_user_id__in'] = user_ids

    return {
        "pending_users": get_users_by_status(REQUESTED, 'timesheets__adjustment_requests__status', user_fil),
        "forwarded_users": get_users_by_status(FORWARDED, 'timesheets__adjustment_requests__status', user_fil),
        "approved_users": get_users_by_status(APPROVED, 'timesheets__adjustment_requests__status', user_fil),
        **stat}


def get_attendance_aprroval_request_summary(
        organization_slug: str, start: date,
        end: date, user_filter: dict,
        exclude_filter: typing.Union[dict, None] = None
) -> dict:
    """
    Attendance approval Request Status Summary

    ---------------------------------
    Attendance approval request status summary for given filters

    :param organization_slug: organization slug of user
    :param start: start of range for timesheet_for
    :param end: end of range for timesheet_for
    :param user_filter: dictionary of filters to be applied on USER model
    :param exclude_filter: dictionary of filters to be excluded on USER model
    :return: counts of adjustment request status pending, forwarded, approved
    """
    fil = dict(detail__organization__slug=organization_slug)
    fil.update(user_filter)

    adjustment_filter = {f"timesheet__timesheet_user__{key}": value for key, value in fil.items()}
    adjustment_filter.update({
        'timesheet__timesheet_for__range': (start, end)
    })
    qs = TimeSheetApproval.objects.filter(**adjustment_filter)
    if exclude_filter:
        qs = qs.exclude(**exclude_filter)
    stat = qs.aggregate(
        pending=Count('id', filter=Q(status=REQUESTED), distinct=True),
        forwarded=Count('id', filter=Q(status=FORWARDED), distinct=True),
        approved=Count('id', filter=Q(status=APPROVED), distinct=True),
    )



    user_fil = {}
    user_fil['detail__organization__slug'] = organization_slug
    user_fil['timesheets__timesheet_for__range'] = [start, end]

    user_ids = user_filter.get('id__in')

    if user_ids:
        user_fil['timesheets__timesheet_user_id__in'] = user_ids

    return {
        "pending_users": get_users_by_status(REQUESTED, 'timesheets__timesheet_approval__status', user_fil),
        "forwarded_users": get_users_by_status(FORWARDED, 'timesheets__timesheet_approval__status', user_fil),
        "approved_users": get_users_by_status(APPROVED, 'timesheets__timesheet_approval__status', user_fil),
        **stat}


def get_overtime_request_status_summary(
        organization_slug: str, start: date, end: date,
        user_filter: dict,
        exclude_filter: typing.Union[dict, None] = None
) -> dict:
    """
    Overtime Request Status Summary

    -------------------------------
    Overtime request status summary for given filters

    :param organization_slug: organization slug of user
    :param start: start of range for timesheet_for
    :param end: end of range for timesheet_for
    :param exclude_filter: dictionary of filters to be excluded on USER model
    :param user_filter: dictionary of filters to be applied on USER model
    :return: counts of adjustment request status pending, forwarded, approved
    """
    fil = dict(detail__organization__slug=organization_slug)
    fil.update(user_filter)

    overtime_filter = {f"overtime_entry__user__{key}": value for key, value in fil.items()}
    overtime_filter.update({
        'overtime_entry__timesheet__timesheet_for__range': [start, end]
    })

    qs = OvertimeClaim.objects.filter(**overtime_filter)
    if exclude_filter:
        qs = qs.exclude(**exclude_filter)
    stat = qs.aggregate(
        pending=Count('id', filter=Q(status=REQUESTED), distinct=True),
        forwarded=Count('id', filter=Q(status=FORWARDED), distinct=True),
        approved=Count('id', filter=Q(status=APPROVED), distinct=True),
        confirmed=Count('id', filter=Q(status=CONFIRMED), distinct=True)
    )

    user_fil = {}
    user_fil['detail__organization__slug'] = organization_slug
    user_fil['overtime_entries__timesheet__timesheet_for__range'] = [start, end]

    user_ids = user_filter.get('id__in')

    if user_ids:
        user_fil['overtime_entries__user_id__in'] = user_ids

    return {
        "pending_users": get_users_by_status(REQUESTED, 'overtime_entries__claim__status', user_fil),
        "forwarded_users": get_users_by_status(FORWARDED, 'overtime_entries__claim__status', user_fil),
        "approved_users": get_users_by_status(APPROVED, 'overtime_entries__claim__status', user_fil),
        "confirmed_users": get_users_by_status(CONFIRMED, 'overtime_entries__claim__status', user_fil),
        **stat}


def get_salary_holdings_count(organization_slug: str, start: date, end: date) -> dict:
    """
    Salary Holding Count
    -------------------------------

    Salary holding count for given filters

    :param organization_slug: organization slug of user
    :param start: start of range for to_date_patched__date__gte
    :param end: end of range for from_date__date__lte
    :param user_filter: dictionary of filters to be applied on USER model
    :return: total count Salary Holdings
    """

    fil = dict(detail__organization__slug=organization_slug)

    salary_holding_filter = {f"employee__{key}": value for key, value in fil.items()}
    if start:
        salary_holding_filter['to_date_patched__date__gte'] = start

    if end:
        salary_holding_filter['from_date__date__lte'] = end

    from irhrs.payroll.models import SalaryHolding
    total_count = SalaryHolding.objects.filter(
        employee__detail__organization__slug=organization_slug
    ).annotate(
            to_date_patched=Case(
                When(
                    to_date__isnull=True,
                    then=timezone.now()
                ),
                default=F('to_date'),
                output_field=models.DateTimeField()
            )
        ).filter(
        **salary_holding_filter
    ).count()

    return {'total_count': total_count}


def get_employee_left_and_joined_summary(
    organization_slug: str,
    start: date,
    end: date
) -> dict:
    """
    Employee Left and Joined Summary
    -------------------------------

    Employee left and joined summary for given filters

    :param organization_slug: organization slug of user
    :param start: start date
    :param end: end date
    :return: counts of joined users, resigned users and turnover users
    """

    queryset = USER.objects.filter(
        detail__organization__slug=organization_slug
    ).prefetch_related(
        Prefetch(
            'detail',
            queryset=UserDetail.objects.select_related(
                'job_title', 'organization', 'division', 'employment_level'
            )
        )
    )

    from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

    if start and end:
        joined_filter = dict(detail__joined_date__gte=start, detail__joined_date__lte=end)
        turnover_filter = dict(
            detail__last_working_date__gte=start,
            detail__last_working_date__lte=end
        )
    else:
        joined_filter = dict(
            detail__joined_date__isnull=False
        )
        turnover_filter = dict(
            detail__last_working_date__isnull=False
        )

    return {
        "joined_users": UserThinSerializer(queryset.filter(**joined_filter), many=True).data,
        "turnover_users": UserThinSerializer(queryset.filter(**turnover_filter), many=True).data
    }


def get_worked_days(
    user: USER,
    start: date,
    end: date,
    include_non_working_days: bool = False,
    count_offday_holiday_as_worked: bool = False,
):
    """
    if include_non_working_days == False

        if leave_coefficient is NO_LEAVE then,
            number += 1

        if leave coefficient in [FIRST_HALF, SECOND_HALF] then,
            number += 0.5

        :returns:
            worked days of user for given date range (no of days present on working days)

    if include_non_working_days == True

        :returns: no of all days present regardless of working days

    if count_offday_holiday_as_worked == True
        **NOTE** don't set this flag to true when include non_working_days=True (Makes no sense)
        :returns: no of present on worked days + offday + holiday
    """
    if include_non_working_days:

        # if include non working days (just send count of all days user is present)
        fil = Q(is_present=True)

        return _get_time_sheets_for_range(user, start, end).filter(fil).order_by().values(
            'timesheet_for'
        ).annotate(count=Count('timesheet_for')).count()
    else:

        no_leave = Q(
            coefficient=WORKDAY,
            is_present=True,
            leave_coefficient=NO_LEAVE
        )
        half_leave = Q(
            coefficient=WORKDAY,
            is_present=True,
            leave_coefficient__in=[FIRST_HALF, SECOND_HALF]
        )
        _exclude = Q()
        annotation = {}
        if count_offday_holiday_as_worked:
            # include no offday and holiday as worked non leave days
            no_leave = no_leave | Q(coefficient__in=[OFFDAY, HOLIDAY])
            # count unpaid leave in offday/holiday as leave
            annotation["is_unpaid"] = Exists(LeaveSheet.objects.filter(
                leave_for=OuterRef("timesheet_for"),
                request__user=OuterRef("timesheet_user"),
                request__is_deleted=False,
                request__leave_rule__is_paid=False
            ))
            _exclude = Q(coefficient__in=[OFFDAY, HOLIDAY], is_unpaid=True)

        no_leave_timesheets_count = _get_time_sheets_for_range(
            user, start, end
        ).filter(
            no_leave
        ).annotate(**annotation).exclude(_exclude).order_by().values(
            'timesheet_for'
        ).annotate(count=Count('timesheet_for')).count()

        half_leave_timesheets_count = _get_time_sheets_for_range(
            user, start, end
        ).filter(
            half_leave
        ).order_by().values(
            'timesheet_for'
        ).annotate(count=Count('timesheet_for')).count()

        # If user applies credit hour leave for 1st/2nd half and is present; make 0.5 present instead of 1
        # present_with_half_credit_leave = get_half_credit_leave_sum(
        #     user, start, end
        # )

        return (
                no_leave_timesheets_count
                + (half_leave_timesheets_count * 0.5)
                # - present_with_half_credit_leave
        )


def get_worked_days_for_daily_heading(
    user: USER,
    start: date,
    end: date,
    pay_when_present_holiday_offday: bool,
    deduct_amount_on_leave: bool,
    deduct_amount_on_remote_work: bool
):
    """Worked days count for daily heading"""
    fil = {'is_present': True}
    if not pay_when_present_holiday_offday:
        fil.update({'coefficient': WORKDAY})
    if deduct_amount_on_leave:
        fil.update({'leave_coefficient': NO_LEAVE})
    if deduct_amount_on_remote_work:
        fil.update({'working_remotely': False})
    present_count = _get_time_sheets_for_range(user, start, end).filter(**fil).order_by().values(
        'timesheet_for'
    ).annotate(count=Count('timesheet_for')).count()

    if deduct_amount_on_leave:
        half_leave = Q(
            coefficient=WORKDAY,
            is_present=True,
            leave_coefficient__in=[FIRST_HALF, SECOND_HALF]
        )
        half_leave_present = _get_time_sheets_for_range(user, start, end).filter(
            half_leave
        ).order_by().values('timesheet_for').annotate(count=Count('timesheet_for')).count()

        # half leave not considered so adding it
        present_count += (half_leave_present * 0.5)

        # # credit leave considered as present so deducting it
        # present_with_half_credit_leave = get_half_credit_leave_sum(
        #     user, start, end
        # )
        # present_count -= present_with_half_credit_leave  # no need to x0.5 as it is sum of
        # balance
    return present_count



def get_absent_days(user: USER, start: date, end: date):
    """
    Return total number of absent without leave days.
    """
    # group by is for multiple timings in a day
    no_leave = Q(
        coefficient=WORKDAY,
        is_present=False,
        leave_coefficient=NO_LEAVE
    )
    half_leave = Q(
        coefficient=WORKDAY,
        is_present=False,
        leave_coefficient__in=[FIRST_HALF, SECOND_HALF]
    )
    full_absent = _get_time_sheets_for_range(user, start, end).filter(no_leave).order_by().values(
        'timesheet_for'
    ).annotate(count=Count('timesheet_for')).count()

    half_absent = _get_time_sheets_for_range(user, start, end).filter(half_leave).order_by(
        ).values('timesheet_for').annotate(count=Count('timesheet_for')).count()

    # Zero Hour Work time is the case where, 1st half leave, and 2nd half leave is applied separately.
    # In those scenarios, the punch in shifts to 1:00 PM (and punch out shifts to 1:00 PM).
    # This scenario is filtered with 2 scenarios, No Leave, and 1st/2nd Half Leave.
    # Calculating to 1 day leverage and 0.5 day leverage.
    zero_hour_work_time = _get_time_sheets_for_range(user, start, end).filter(
        expected_punch_in__isnull=False,
        expected_punch_out__isnull=False,
        expected_punch_in=F('expected_punch_out')
    ).annotate(
        leverage=Case(
            When(
                coefficient=WORKDAY,
                is_present=False,
                leave_coefficient__in=[FIRST_HALF, SECOND_HALF],
                hour_off_coefficient=CREDIT_HOUR,
                then=0.5
            ),
            default=0,
            output_field=FloatField()
        )
    ).order_by().values('timesheet_for', 'leverage').aggregate(
        total=Sum('leverage')
    ).get('total') or 0

    return full_absent + (half_absent * 0.5)


def get_timesheet_penalty_days(employee: USER, from_date: date, to_date: date) -> float:
    """Calculates the number of penalty days accumulated.

    Args:
        employee (USER): User to get timesheet penalty for
        from_date (date): start date
        to_date (date): end_date

    Returns:
        float: Number of days to be treated as penalty in payroll.
    """
    return TimeSheetPenaltyToPayroll.objects.filter(
        user_penalty__user=employee,
        confirmed_on__range=(from_date, to_date),
    ).aggregate(
        penalty_count=Sum('days')
    ).get('penalty_count') or 0
