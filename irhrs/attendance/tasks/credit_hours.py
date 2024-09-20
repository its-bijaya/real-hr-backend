"""
Background Task Work Plan.

Unlike, overtime, it may need to be processed for weekly/monthly cases.

TimeSheetCreditHour
    -> Indicates, the total credit hour earned/applicable.

CreditHourBalance
    -> This balance links to multiple credit hours. And based on d/w/m, grants a
    cumulative balance to Leave Account.
    -> Pre Approved Credit Hour Links Here.

Rest is up to leave.

Leave Master Setting
 -> Enable `credit leave`
Leave Type
 -> Credit Leave Type
Leave Rule
 ->  max apply
 ->  min apply
 -> auto expiration.
Leave Request
 -> should now allow multiple leave request for the same day.
 -> will be using timings to test no conflicts.

"""
import logging
from datetime import timedelta

from irhrs.attendance.constants import APPROVED, WORKDAY, HOLIDAY, OFFDAY
from irhrs.attendance.models import CreditHourRequest, TimeSheet
from irhrs.attendance.models.credit_hours import CreditHourTimeSheetEntry
from irhrs.attendance.utils.credit_hours import get_leave_account_for, get_credit_leave_account_qs, \
    convert_timedelta_to_minutes
from irhrs.attendance.utils.pre_approval_utils import hold_credit_if_overtime_undecided
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import humanize_interval
from irhrs.leave.constants.model_constants import ADDED, DEDUCTED
from irhrs.leave.models import LeaveAccountHistory

logger = logging.getLogger(__name__)
ZERO_CREDIT = timedelta(0)


def get_credit_addition_remarks(duration, date, action=ADDED):
    interval = humanize_interval(duration)
    awarded_date = date.isoformat()
    return f"{action} {interval} credit hours for {awarded_date}"


def add_credit_to_leave_account(credit_timesheet_entry):
    leave_account = get_leave_account_for(credit_timesheet_entry)
    if not leave_account:
        return
    balance_to_add = credit_timesheet_entry.earned_credit_hours
    # because earned credit hours is in duration, we shall convert it to min.
    balance_to_add = convert_timedelta_to_minutes(balance_to_add)
    if balance_to_add <= 0:
        return
    previous_balance, previous_usable = leave_account.balance, leave_account.usable_balance
    max_balance = leave_account.rule.max_balance
    balance_to_add = min(balance_to_add, max_balance-leave_account.usable_balance)
    leave_account.balance += balance_to_add
    leave_account.usable_balance += balance_to_add
    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),
        action=ADDED,
        previous_balance=previous_balance,
        previous_usable_balance=previous_usable,
        new_balance=leave_account.balance,
        new_usable_balance=leave_account.usable_balance,
        remarks=get_credit_addition_remarks(
            duration=credit_timesheet_entry.earned_credit_hours,
            date=credit_timesheet_entry.timesheet.timesheet_for,
            action=ADDED
        )
    )
    account_history.save()
    leave_account.save()
    add_status_to_approved_credit_hour_requests()


def get_earned_credit(current_credit, adjacent_timesheet, credit_setting, reserved=ZERO_CREDIT):
    # HRIS-2108: Allow credit & Overtime both.
    # For such cases, we have to test for the overtime requested for the day.

    """

    Scenario I: CREDIT ONLY APPROVED
        >> Grant Credit Hours

    Scenario II: OVERTIME ONLY APPROVED
        >> Grant Overtime Hours

    Scenario III: OVERTIME AND CREDIT BOTH APPROVED
        >> Overtime Follows Scenario II
        >> Extra from OVERTIME goes to CREDIT
            CREDIT: 1, OVERTIME: 1, WORKED: 1.5
                > OVERTIME (1), CREDIT (0.5)

    SCENARIO IV: OVERTIME REQUESTED, CREDIT APPROVED
        >> Credit Hold if Overtime Undecided.

    SCENARIO V: CREDIT GRANTED, OVERTIME APPROVED
        >> Not Possible, but if allowed for past dates, follows scenario II.

    SCENARIO VI: OVERTIME GRANTED, CREDIT APPROVED
        >> Not Possible, but if allowed for past dates, follows scenario III
    """
    if not credit_setting.reduce_credit_if_actual_credit_lt_approved_credit:
        return max(ZERO_CREDIT, current_credit-reserved)
    total = ZERO_CREDIT
    if (
            adjacent_timesheet.punch_in_delta is None
            or adjacent_timesheet.punch_out_delta is None
    ) and adjacent_timesheet.coefficient == WORKDAY:
        return total
    elif adjacent_timesheet.coefficient in (HOLIDAY, OFFDAY):
        adjacent_timesheet.punch_in_delta = ZERO_CREDIT
        adjacent_timesheet.punch_out_delta = (
                adjacent_timesheet.punch_out - adjacent_timesheet.punch_in
        )
    # actual - expected on both cases. If pid is -ve, we have credit. If pod is +ve, we have credit
    punch_in_delta = adjacent_timesheet.punch_in_delta
    if punch_in_delta < ZERO_CREDIT:
        total = total - punch_in_delta
    punch_out_delta = adjacent_timesheet.punch_out_delta
    if punch_out_delta > ZERO_CREDIT:
        total = total + punch_out_delta
    # always reduce penalty working hours.
    if adjacent_timesheet.unpaid_break_hours:
        total = max(ZERO_CREDIT, total - adjacent_timesheet.unpaid_break_hours)
    # Reserved is the amount that goes into overtime, credit only gets (total - reserved)
    total_after_reserved = max(ZERO_CREDIT, total-reserved)
    return min(total_after_reserved, current_credit)


def create_entry_from_approved_credit(approved_credit):
    if approved_credit.status != APPROVED:
        return
    user = approved_credit.sender
    credit_setting = user.attendance_setting.credit_hour_setting

    adjacent_timesheet = TimeSheet.objects.filter(
        timesheet_user=user,
        timesheet_for=approved_credit.credit_hour_date,
        # Adding Additional Filters, so we dont break later.
        punch_in__isnull=False,
        punch_out__isnull=False
    ).first()
    if not adjacent_timesheet:
        logger.debug(f'No Adjacent ts for {approved_credit}')
        return

    hold, reserved_duration = hold_credit_if_overtime_undecided(adjacent_timesheet)
    if hold:
        return

    approved_credit_duration = approved_credit.credit_hour_duration

    if credit_setting.reduce_credit_if_actual_credit_lt_approved_credit:
        earned_credit = get_earned_credit(
            approved_credit_duration,
            adjacent_timesheet,
            credit_setting,
            reserved=reserved_duration
        )
        granted_credit_hours = min(approved_credit_duration, earned_credit)
    else:
        granted_credit_hours = approved_credit_duration

    if granted_credit_hours == ZERO_CREDIT:
        return

    credit_entry = CreditHourTimeSheetEntry(
        timesheet=adjacent_timesheet,
        credit_setting=credit_setting,
        earned_credit_hours=granted_credit_hours,
        status=approved_credit.status
    )
    credit_entry.save()
    approved_credit.credit_entry = credit_entry
    approved_credit.save()
    return credit_entry


def generate_credit_hours_for_approved_credit_hours(exclude_no_account=True):
    pre_approved_credit_hours = CreditHourRequest.objects.filter(
        # Only Approved Credit Hours
        status=APPROVED
    ).exclude(
            is_deleted=True
    ).filter(
        # Whose entry has not been created yet,
        credit_entry__isnull=True
    ).filter(
        # extra security
        sender__attendance_setting__credit_hour_setting__isnull=False,
        sender__attendance_setting__enable_credit_hour=True,
    )

    if exclude_no_account:
        pre_approved_credit_hours = pre_approved_credit_hours.filter(
            sender__in=get_credit_leave_account_qs().values_list('user', flat=True)
        )
    for approved_credit in pre_approved_credit_hours:
        credit_entry = create_entry_from_approved_credit(approved_credit)
        if credit_entry:
            add_credit_to_leave_account(credit_entry)


def add_status_to_approved_credit_hour_requests():
    CreditHourRequest.objects.exclude(
        is_deleted=True
    ).filter(
        credit_entry__isnull=False,
        status=APPROVED,
        sender__attendance_setting__credit_hour_setting__isnull=False,
        sender__attendance_setting__enable_credit_hour=True
    ).update(credit_hour_status = "Added")
   
        
def is_pre_approved_credit_hour_editable(pre_approval, new_duration):
    return is_leave_account_editable(pre_approval.credit_entry, new_duration)


def is_leave_account_editable(credit_timesheet_entry, new_credit_hours):
    if not credit_timesheet_entry:
        return True, ""
    # if action is addition, we can add the balance.
    # If action is reduction, we have to check if can reach below zero.
    if new_credit_hours == credit_timesheet_entry.earned_credit_hours:
        return False, "Resulting Credit Hour is Equal."
    if new_credit_hours > credit_timesheet_entry.earned_credit_hours:
        return True, ""
    consumed_credit_hours = credit_timesheet_entry.consumed_credit_hours or ZERO_CREDIT
    if (new_credit_hours - consumed_credit_hours) < timedelta(0):
        return False, "Credit Hours Has been consumed"
    return True, ""


def modify_leave_balance_after_recalibration(credit_timesheet_entry, old_credit_given):
    leave_account = get_leave_account_for(credit_timesheet_entry)
    if not leave_account:
        return
    previous_balance, previous_usable = leave_account.balance, leave_account.usable_balance
    new_credit = credit_timesheet_entry.earned_credit_hours

    if not is_leave_account_editable(credit_timesheet_entry, credit_timesheet_entry.earned_credit_hours):
        return
    if new_credit > old_credit_given:
        action = ADDED
        balance_to_add = convert_timedelta_to_minutes(
            new_credit - old_credit_given
        )
        allowed_from_leave = leave_account.rule.max_balance - leave_account.usable_balance
        # balance_to_add = min(allowed-have, balance_to_add)
        balance_to_add = min(balance_to_add, allowed_from_leave)
        leave_account.balance += balance_to_add
        leave_account.usable_balance += balance_to_add
    elif new_credit < old_credit_given:
        action = DEDUCTED
        duration = old_credit_given - new_credit
        balance_to_deduct = convert_timedelta_to_minutes(
            duration
        )
        leave_account.balance -= balance_to_deduct
        leave_account.usable_balance -= balance_to_deduct
    else:
        return

    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),
        action=action,
        previous_balance=previous_balance,
        previous_usable_balance=previous_usable,
        new_balance=leave_account.balance,
        new_usable_balance=leave_account.usable_balance,
        remarks=get_credit_addition_remarks(
            duration=timedelta(minutes=(leave_account.usable_balance - previous_usable)),
            date=credit_timesheet_entry.timesheet.timesheet_for,
            action=action
        )
    )
    account_history.save()
    leave_account.save()
    return True


def recalibrate_credit_when_pre_approval_is_modified(pre_approval):
    credit_entry = pre_approval.credit_entry
    if not credit_entry:
        # no need to re-calibrate.
        return
    if not credit_entry.timesheet.punch_out:
        # Can not process timesheets without entries.
        return
    perform_credit_hour_recalibration(credit_entry)


def perform_credit_hour_recalibration(credit_entry):
    credit_request = credit_entry.credit_request
    credit_setting = credit_entry.credit_setting
    if not (credit_request and credit_setting):
        return
    approved_credit_duration = credit_request.credit_hour_duration
    earned_credit = get_earned_credit(approved_credit_duration, credit_entry.timesheet, credit_setting)

    granted_credit_hours = min(approved_credit_duration, earned_credit)
    old_credit_hours = credit_entry.earned_credit_hours
    if old_credit_hours == granted_credit_hours:
        return
    credit_entry.earned_credit_hours = granted_credit_hours
    credit_entry.save()
    return modify_leave_balance_after_recalibration(credit_entry, old_credit_hours)


def get_balance_to_deduct(balance_to_deduct, leave_account):
    """
    :param balance_to_deduct: Balance granted from Credit Hour Request.
    :param leave_account: Leave Account to reduce balance from
    :return: deletable balance
    """
    return min(balance_to_deduct, leave_account.usable_balance)


def revert_credit_hour_from_leave_account(credit_hour_delete_request):
    if credit_hour_delete_request.status != APPROVED:
        return "Did not revert as status was not approved!"
    request = credit_hour_delete_request.request
    if request.is_deleted:
        return "Already deleted."
    request.is_deleted = True
    request.save()
    # [HRIS - 2897]
    #    If remaining leave balance is less then the deducting balance
    #    deduct possible one and ignore insufficient balance.
    # if not deletable_credit_request(credit_hour_delete_request.request):
    #     return "Deletable Test Failed!"
    credit_entry = getattr(request, 'credit_entry', None)
    if not credit_entry:
        return "No entry was generated"
    leave_account = get_leave_account_for(credit_entry)
    previous_balance, previous_usable = leave_account.balance, leave_account.usable_balance
    action = DEDUCTED
    duration = credit_entry.earned_credit_hours
    balance_to_deduct = convert_timedelta_to_minutes(duration)
    balance_to_deduct = get_balance_to_deduct(balance_to_deduct, leave_account)
    leave_account.balance -= balance_to_deduct
    leave_account.usable_balance -= balance_to_deduct
    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),
        action=action,
        previous_balance=previous_balance,
        previous_usable_balance=previous_usable,
        new_balance=leave_account.balance,
        new_usable_balance=leave_account.usable_balance,
        remarks=get_credit_addition_remarks(
            duration=timedelta(minutes=balance_to_deduct),
            date=credit_entry.timesheet.timesheet_for,
            action=action
        )
    )
    account_history.save()
    leave_account.save()
