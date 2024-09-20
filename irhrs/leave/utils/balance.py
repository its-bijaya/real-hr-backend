"""@irhrs_docs"""
import logging
from datetime import timedelta, time

from dateutil import rrule
from django.db import transaction
from django.db.models import Q, Max, Min, Avg, Value, F, DateField
from rest_framework.exceptions import ValidationError

from irhrs.attendance.constants import FULL_LEAVE as A_FULL_LEAVE, FIRST_HALF as A_FIRST_HALF, \
    SECOND_HALF as A_SECOND_HALF
from irhrs.attendance.models import IndividualUserShift, WorkTiming, TimeSheet
from irhrs.attendance.signals import recalibrate_overtime
from irhrs.attendance.utils.helpers import get_weekday
from irhrs.core.constants.organization import LEAVE
from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.core.utils.common import combine_aware, humanize_interval
from irhrs.leave.constants.model_constants import (
    EXCLUDE_HOLIDAY_AND_OFF_DAY, INCLUDE_HOLIDAY, INCLUDE_OFF_DAY, APPROVED
)
from irhrs.leave.constants.model_constants import TIME_OFF, FULL_DAY, \
    FIRST_HALF, SECOND_HALF, ADDED, CREDIT_HOUR, UPDATED, INSUFFICIENT_BALANCE
from irhrs.leave.models import LeaveType, MasterSetting, LeaveAccountHistory, LeaveSheet
from irhrs.leave.models.request import HourlyLeavePerDay
from irhrs.leave.utils.leave_request import apply_leave_on_behalf_by_system_if_applicable
from irhrs.leave.utils.timesheet import revert_timesheet_for_leave, get_shift_timings, \
    get_leave_coefficient
from irhrs.notification.utils import notify_organization
from irhrs.organization.models import FiscalYear
from irhrs.permission.constants.permissions import LEAVE_BALANCE_PERMISSION, \
    OFFLINE_LEAVE_PERMISSION, ASSIGN_LEAVE_PERMISSION

HOURLY_LEAVES = (CREDIT_HOUR, TIME_OFF)


def get_half_day_balance(start_time, end_time, user, is_half_day,
                         holiday_inclusive):
    if holiday_inclusive:
        return 0.5 if is_half_day else 1
    start_day = user.attendance_setting.work_day_for(start_time)
    if start_day:
        if is_half_day:
            shifts = start_day.timings.count()
            if shifts > 1:
                raise ValidationError({
                    'start': 'Half day leaves for Multiple Shift Users is not allowed.'
                })
            else:
                return 0.5
        else:
            return 1
    return 0


def check_leave_inclusive(leave_account, start_date, end_date):
    leave_inclusive = (
        leave_account.rule.inclusive_leave != EXCLUDE_HOLIDAY_AND_OFF_DAY
    )
    leave_range = (end_date - start_date).days
    valid_date_range = leave_range + 1 >= leave_account.rule.inclusive_leave_number
    return leave_inclusive and valid_date_range


def validate_leave_apply_for_day(leave_account, inclusive_leave, user, for_date):
    if inclusive_leave:
        if leave_account.rule.inclusive_leave == INCLUDE_HOLIDAY:
            return user.is_offday(for_date)
        elif leave_account.rule.inclusive_leave == INCLUDE_OFF_DAY:
            return user.is_holiday(for_date)
        else:
            return False
    else:
        return user.is_holiday(for_date) or user.is_offday(for_date)


def get_leave_balance(start_time, end_time, user, leave_account, part_of_day):
    # shifts after start
    is_half_day = True if part_of_day in [FIRST_HALF, SECOND_HALF] else False
    if not getattr(user, 'attendance_setting', None):
        raise ValidationError('The user does not have attendance setting.')
    leave_category = leave_account.rule.leave_type.category
    if leave_category in (TIME_OFF, CREDIT_HOUR):
        # In case of Time Off/Credit Hour the balance deducted is the minutes of leave.
        workday = user.attendance_setting.work_day_for(end_time)
        errors = list()
        if not workday:
            errors.append({
                'start_time': 'User has no shift for the day.'
            })
        else:
            timings = workday.timings.aggregate(
                sh_start=Min('start_time'),
                sh_end=Max('end_time'),
                sh_time=Avg('working_minutes')
            )
            shift_start = timings.get('sh_start')
            shift_end = timings.get('sh_end')
            shift_minutes = timings.get('sh_time')
            if leave_category == TIME_OFF:
                if shift_start > start_time.astimezone().time():
                    errors.append({
                        'start_time': f'The shift begins at {shift_start}'
                    })
                if shift_end < end_time.astimezone().time():
                    errors.append({
                        'end_time': f'The shift ends at {shift_end}'
                    })
            elif leave_category == CREDIT_HOUR:
                if start_time.astimezone().time() < shift_start:
                    errors.append({
                        'start_time': f'The shift begins at {shift_start}. '
                                      f'Please select time after the shift begins.'
                    })
                if end_time.astimezone().time() > shift_end:
                    errors.append({
                        'end_time': f'The shift ends at {shift_end}. '
                                    'Please select time before the shift ends.'
                    })
        if errors:
            raise ValidationError(errors)
        time_delta = end_time - start_time
        if time_delta.total_seconds() < 0:
            # invalid request
            raise ValidationError(
                "The start time cannot be greater than end time."
            )
        else:
            balance_minutes = int(time_delta.total_seconds() / 60)
            if (
                start_time.astimezone().time() == shift_start
                and end_time.astimezone().time() == shift_end
            ):
                balance = 1
                return balance_minutes, [
                    {
                        'leave_for': start_time.date(),
                        'start_time': start_time,
                        'end_time': end_time,
                        'balance': balance,
                        'balance_minutes': 0
                    }
                ]
            half_time = int(shift_minutes / 2)
            if balance_minutes >= half_time and (
                start_time.astimezone().time() == shift_start
                or end_time.astimezone().time() == shift_end
            ):
                return balance_minutes, [
                    {
                        'leave_for': start_time.date(),
                        'start_time': start_time,
                        'end_time': end_time,
                        'balance': 0.5,
                        'balance_minutes': (balance_minutes - half_time)
                    }
                ]

            return balance_minutes, [
                {
                    'leave_for': start_time.date(),
                    'start_time': start_time,
                    'end_time': end_time,
                    'balance': 0,
                    'balance_minutes': balance_minutes
                }
            ]

    holiday_inclusive = (
        leave_account.master_setting.holiday_inclusive
        and check_leave_inclusive(leave_account, start_time, end_time)
    )
    if validate_leave_apply_for_day(leave_account, holiday_inclusive, user, start_time):
        first_day_balance = 0
    else:
        first_day_balance = get_half_day_balance(
            start_time,
            end_time,
            user,
            is_half_day,
            holiday_inclusive
        )
    # last_day_exists = IndividualUserShift.objects.filter(
    #     individual_setting=user.attendance_setting,
    # ).annotate(
    #     date_to_test=Value(end_time.date(), output_field=DateField())
    # ).filter(
    #     Q(
    #         date_to_test__range=(F('applicable_from'), F('applicable_to'))
    #     ) | Q(
    #         date_to_test__gte=F('applicable_from'),
    #     )
    # ).exists()
    errors = dict()
    if first_day_balance == 0:
        errors.update({
            'start': "The start of leave is holiday or off-day "
        })
    if validate_leave_apply_for_day(leave_account, holiday_inclusive, user, end_time):
        errors.update({
            'end': "The end of leave is holiday or off-day "
        })
    if errors:
        raise ValidationError(errors)
    total_leave_balance = first_day_balance
    steps = calibrate_leave_range(
        leave_account=leave_account,
        user=user,
        start_time=start_time,
        end_time=end_time,
        part_of_day=part_of_day
    )
    balance_to_add_from_steps = sum([
        step.get('balance') for step in steps[1:]
    ])
    total_leave_balance += balance_to_add_from_steps
    if total_leave_balance <= 0:
        raise ValidationError(
            "The leave may be due to request on holidays or off-days. No need "
            "to apply for leave."
        )
    return total_leave_balance, steps


def validate_sufficient_leave_balance(leave_account, leave_balance):
    """
    Check if account has enough balance to take the leave

    *Note -> Takes Beyond Balance into account as well*

    :param leave_account: Leave Account
    :param leave_balance: Balance to use
    :return: None
    """
    leave_rule = leave_account.rule
    required_credit = leave_balance - leave_account.usable_balance
    if required_credit > 0:
        if not leave_rule.can_apply_beyond_zero_balance:
            raise ValidationError({
                "error": "The user does not have sufficient balance, "
                "and credit leave is not allowed",
                "error_type": INSUFFICIENT_BALANCE
            })

        elif required_credit > leave_rule.beyond_limit:
            raise ValidationError(
                "The leave request consumes more than credit leave allowance."
            )


def get_applicable_leave_types_for_organization(organization):
    """
    :return: list of applicable leave types for an organization
    """
    active_master_setting_qs = MasterSetting.objects.filter(
        organization=organization
    ).active()
    qs = LeaveType.objects.filter(
        master_setting__in=active_master_setting_qs
    ).values_list('id', 'name').order_by('name')
    return [
        {'id': id, 'name': name} for id, name in qs
    ]


def is_workday(date, user):
    is_holiday = user.is_holiday(date)
    weekday = get_weekday(date)
    previous = IndividualUserShift.objects.filter(
        applicable_to__gte=date,
        applicable_to__isnull=False,
        individual_setting__user=user,
        applicable_from__lte=date,
    ).values_list('shift', flat=True)
    current = IndividualUserShift.objects.filter(
        applicable_to__isnull=True,
        individual_setting__user=user,
        applicable_from__lte=date,
    ).values_list('shift', flat=True)
    is_work_day = WorkTiming.objects.filter(
        work_day__day=weekday
    ).filter(
        Q(work_day__shift__in=previous) |
        Q(work_day__shift__in=current)
    ).exists()
    return not is_holiday and is_work_day


def calibrate_leave_range(
    leave_account, user, start_time, end_time, part_of_day=FULL_DAY
):
    half_day_for_range = False  # can take 1st half leave for entire week?
    headers = (
        'leave_for',
        'start_time',
        'end_time',
        'balance'
    )
    holiday_inclusive = (
        leave_account.master_setting.holiday_inclusive
        and check_leave_inclusive(leave_account, start_time, end_time)
    )
    trails = list()

    for index, each_day in enumerate(list(rrule.rrule(
        rrule.DAILY, dtstart=start_time, until=end_time
    ))):
        if index != 0:
            part_of_day = part_of_day if half_day_for_range else FULL_DAY
        w_day = user.attendance_setting.work_day_for(each_day)
        if validate_leave_apply_for_day(leave_account, holiday_inclusive, user, each_day.date()):
            continue
        if holiday_inclusive or w_day:
            try:
                timing = w_day.timings.first()
            except AttributeError:
                timing = None
            sh_start = timing.start_time if timing else time(0, 0)
            sh_end = timing.end_time if timing else time(23, 59)
            half_working_minutes = (
                (timing.working_minutes if timing else 0) // 2
            )
            starts_at = combine_aware(each_day, sh_start)
            start = {
                FULL_DAY: starts_at,
                FIRST_HALF: starts_at,
                SECOND_HALF: starts_at + timedelta(
                    minutes=half_working_minutes
                )
            }.get(
                part_of_day
            )
            ends_at = combine_aware(each_day, sh_end)
            end = {
                FULL_DAY: ends_at,
                FIRST_HALF: ends_at - timedelta(minutes=half_working_minutes),
                SECOND_HALF: ends_at
            }.get(
                part_of_day
            )
            balance = 1 if part_of_day == FULL_DAY else 0.5
            data = dict(
                zip(
                    headers,
                    (
                        each_day,
                        start,
                        end,
                        balance  # leave_for_range
                    )
                )
            )
            trails.append(data)
    return trails


def recalibrate_overtime_due_to_leave_updates(
    leave_request,
    actor=None
):
    actor = actor or get_system_admin()
    time_sheets = list()
    with transaction.atomic():
        for timesheet in TimeSheet.objects.filter(
            timesheet_user=leave_request.user,
            timesheet_for__range=(
                leave_request.start.date(),
                leave_request.start.date(),
            )
        ):
            timesheet.fix_entries()
            time_sheets.append(timesheet)
    for ts in time_sheets:
        ts.refresh_from_db()
        recalibrate_overtime(
            timesheet,
            actor,
            (
                'Leave Deletion was approved '
                if leave_request.is_deleted
                else f'leave was {leave_request.get_status_display()} '
            )
        )


def calculate_addition_balance_for_leave_revert(leave_account, leave_request_balance):
    """
    Validates if the leave request reverted balance exceeds max balance and calculates
    additive balance accordingly
    :param leave_account: Leave Account to which balance is to be added.
    :param leave_request_balance: balance consumed by deleted leave request.
    :return: returns balance to add, not exceeding the max balance.
    """
    max_balance = leave_account.rule.max_balance
    if max_balance:
        current_balance = leave_account.balance
        if (current_balance + leave_request_balance) > max_balance:
            return max_balance - current_balance
    return leave_request_balance


def revert_leave_for_date(leave_request_delete_history):
    leave_request = leave_request_delete_history.leave_request
    leave_account = leave_request.leave_account
    leave_request_balance = leave_request.balance
    actor = leave_request_delete_history.modified_by or get_system_admin()

    leave_request.is_deleted = True
    leave_request.save()

    revert_timesheet_for_leave(leave_request)
    from irhrs.leave.api.v1.serializers.leave_request import LeaveRequestHelper
    if not nested_getattr(leave_account, 'rule.renewal_rule.back_to_default_value'):
        account_history = LeaveAccountHistory(
            account=leave_account,
            user=leave_account.user,
            actor=actor,
            action=ADDED,
            previous_balance=leave_account.balance,
            previous_usable_balance=leave_account.usable_balance,
        )
        balance_that_can_be_added_to_leave_account = calculate_addition_balance_for_leave_revert(
            leave_account,
            leave_request_balance
        )
        balance_display = LeaveRequestHelper.get_balance_display(
            balance_that_can_be_added_to_leave_account,
            leave_request.leave_rule.leave_type.category
        )
        if balance_that_can_be_added_to_leave_account < leave_request.balance:
            balance_display = str(balance_display) \
                              + ' and collapsed {} due to max balance constraint'.format(
                humanize_interval((leave_request.balance - balance_that_can_be_added_to_leave_account) * 60)
            )
        account_history.remarks = \
            'Added Balance {} after cancellation of approved request for {} - {}'.format(
                balance_display,
                leave_request.start.date(),
                leave_request.end.date(),
            )
        leave_account.balance += balance_that_can_be_added_to_leave_account
        leave_account.usable_balance += balance_that_can_be_added_to_leave_account
        account_history.new_balance = leave_account.balance
        account_history.new_usable_balance = leave_account.usable_balance
        account_history.save()
        leave_account.save()

    recalibrate_overtime_due_to_leave_updates(leave_request, actor)

    logger = logging.getLogger(__name__)
    logger.info(
        f'Deleted approved request of {leave_account.user} for '
        f'{leave_request.start} - {leave_request.end}'
    )

    update_hourly_leave_per_day_for_leave_request(leave_request_delete_history.leave_request)


def leave_approve_post_actions(leave_request):
    recalibrate_leave_balance_for_default_value(leave_account=leave_request.leave_account)
    update_hourly_leave_per_day_for_leave_request(leave_request)
    prevent_default = getattr(leave_request, 'prevent_default', None)
    if not prevent_default:
        apply_leave_on_behalf_by_system_if_applicable(leave_request)


def recalibrate_leave_balance_for_default_value(leave_account):
    """
    This util is used to make leave balance to default value if
    back_to_default_value is set to be True and leave 'balance' and
    'usable_balance' becomes zero.
    """
    renewal_rule = nested_getattr(leave_account, 'rule.renewal_rule')
    if renewal_rule and renewal_rule.back_to_default_value:
        balance = renewal_rule.initial_balance
        user = leave_account.user
        leave_account_history = LeaveAccountHistory(
            account=leave_account,
            user=user,
            actor=get_system_admin(),
            previous_balance=leave_account.balance,
            previous_usable_balance=leave_account.usable_balance,
            new_balance=balance,
            new_usable_balance=balance,
            action=UPDATED,
            remarks=f"Leave balance changed by the System under 'Back To Default Value'."
        )
        leave_account.balance = balance
        leave_account.usable_balance = balance
        leave_account.save()
        leave_account_history.save()
        organization = user.detail.organization
        notify_organization(
            text=f'Leave Account {leave_account.rule.leave_type} for {user.full_name}'
                 f' has been updated under \'Back to Default Value\'.',
            action=leave_account,
            organization=organization,
            url=f'/admin/{organization.slug}/leave/leave-balance',
            permissions=[
                LEAVE_BALANCE_PERMISSION,
                OFFLINE_LEAVE_PERMISSION,
                ASSIGN_LEAVE_PERMISSION
            ],
        )


def update_hourly_leave_per_day(user, leave_for):
    shift, timings = get_shift_timings(user, leave_for)
    if timings is None:
        return
    timing = timings.first()
    if not timing:
        return
    actual_in = combine_aware(
        leave_for,
        timing.start_time
    )
    actual_out = combine_aware(
        leave_for,
        timing.end_time
    )

    base_qs = LeaveSheet.objects.filter(
        leave_for=leave_for,
        request__user=user,
        request__status=APPROVED,
        request__is_deleted=False,
        request__leave_rule__leave_type__category__in=HOURLY_LEAVES,
        start__gte=actual_in,
        end__lte=actual_out
    )
    paid_qs = base_qs.filter(request__leave_rule__is_paid=True)
    unpaid_qs = base_qs.filter(request__leave_rule__is_paid=False)

    coefficient_balance_map = {
        A_FULL_LEAVE: 1,
        A_FIRST_HALF: 0.5,
        A_SECOND_HALF: 0.5
    }

    paid_coefficient, _, _ = get_leave_coefficient(actual_in, actual_out, paid_qs, timing)
    paid_balance = coefficient_balance_map.get(paid_coefficient, 0)

    unpaid_coefficient, _, _ = get_leave_coefficient(actual_in, actual_out, unpaid_qs, timing)
    unpaid_balance = coefficient_balance_map.get(unpaid_coefficient, 0)

    def update_leave_per_day(is_paid_, balance_):
        if balance_ > 0:
            HourlyLeavePerDay.objects.update_or_create(
                user=user,
                leave_for=leave_for,
                is_paid=is_paid_,
                defaults={'balance': balance_}
            )
        else:
            HourlyLeavePerDay.objects.filter(
                user=user, leave_for=leave_for, is_paid=is_paid_).delete()

    update_leave_per_day(is_paid_=True, balance_=paid_balance)
    update_leave_per_day(is_paid_=False, balance_=unpaid_balance)


def update_hourly_leave_per_day_for_leave_request(leave_request):
    if leave_request.leave_rule.leave_type.category in HOURLY_LEAVES:
        for day in leave_request.sheets.all().values_list('leave_for', flat=True):
            update_hourly_leave_per_day(leave_request.user, day)


def get_fiscal_year_for_leave(organization, date=None):
    has_fiscal_year = FiscalYear.objects.for_category_exists(
        organization=organization,
        date=date,
        category=LEAVE
    )
    fil = dict(
        organization=organization,
    )
    if date:
        fil.update({'date_': date})
    if has_fiscal_year:
        fiscal_year = FiscalYear.objects.active_for_date(
            **fil,
            category=LEAVE
        ) if date else FiscalYear.objects.current(**fil, category=LEAVE)
        if not fiscal_year:
            return None
    else:
        fiscal_year = FiscalYear.objects.active_for_date(**fil) if date else \
            FiscalYear.objects.current(**fil)
    return fiscal_year
