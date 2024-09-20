from irhrs.attendance.models.breakout_penalty import BreakoutPenaltyLeaveDeductionSetting
import logging
import math
from datetime import time, datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.db.models import Sum, Q, F, Count, OuterRef, Subquery
from django.utils import timezone
from django.utils.timezone import now

from irhrs.attendance.constants import OFFDAY, HOLIDAY, WORKDAY, NO_LEAVE, FIRST_HALF, SECOND_HALF
from irhrs.attendance.models import TimeSheet, IndividualUserShift
from irhrs.core.utils import nested_getattr, get_system_admin
from irhrs.core.utils import common
from irhrs.core.utils.common import get_today
from irhrs.leave.models.account import CompensatoryLeaveAccount, LeaveEncashment, \
    LeaveEncashmentHistory
from irhrs.leave.constants.model_constants import (
    REMOVED, DAYS, MONTHS, YEARS, ADDED,
    DEDUCTED, GENERATED, REQUESTED, FORWARDED, ASSIGNED, ASSIGNED_WITH_BALANCE, APPROVED)
from irhrs.leave.models import (
    MasterSetting, LeaveRule, LeaveAccount, LeaveAccountHistory, LeaveSheet
)
from irhrs.leave.models.rule import CompensatoryLeaveCollapsibleRule
# Leave Logger Config
from irhrs.leave.utils.balance import get_fiscal_year_for_leave
from irhrs.users.models import UserExperience

leave_logger = logging.getLogger(__name__)

ONE_DAY = timezone.timedelta(days=1)


# End Leave Logger Config


def expire_master_settings():
    today = common.get_today()
    yesterday = today - timezone.timedelta(days=1)

    expired = MasterSetting.objects.all().expired().filter(
        effective_till__lte=yesterday
    )

    # Delete All Leave Type Settings with expired master setting
    BreakoutPenaltyLeaveDeductionSetting.objects.filter(
        leave_type_to_reduce__master_setting__in=expired
    ).delete()

    # archive leave rules
    LeaveRule.objects.filter(leave_type__master_setting__in=expired).update(
        is_archived=True
    )

    # archive user accounts
    accounts_to_archive = LeaveAccount.objects.filter(
        rule__leave_type__master_setting__in=expired,
        is_archived=False
    )
    remarks = "Archived user's account by system due to expiration of leave " \
              "master setting."

    for account in accounts_to_archive:
        account.is_archived = True
        account.save()

        LeaveAccountHistory.objects.create(
            account=account,
            user=account.user,
            actor=get_system_admin(),
            action=REMOVED,
            previous_balance=account.balance,
            previous_usable_balance=account.usable_balance,
            new_balance=account.balance,
            new_usable_balance=account.usable_balance,
            remarks=remarks
        )


def get_active_master_setting(organization=None):
    if organization:
        return MasterSetting.objects.filter(
            organization=organization
        ).active().first()
    return MasterSetting.objects.all().active().first()


def carry_forward_balance(
    leave_account, carry_forward_balance, balance_in_hand
):
    """
    Carry forwards the remaining balance in a leave account based on the
    master setting flag and the leave rule value
    :param leave_account: Account to Carry Forward the old balance.
    :return: None
    """
    carry_allowed = leave_account.master_setting.carry_forward
    if not carry_allowed:
        return balance_in_hand, 0
    max_balance_forwarded = carry_forward_balance
    remaining_balance_in_hand = balance_in_hand
    if max_balance_forwarded and (
        remaining_balance_in_hand > 0 and max_balance_forwarded > 0
    ):
        if remaining_balance_in_hand <= max_balance_forwarded:
            carry_balance = remaining_balance_in_hand
        else:
            carry_balance = max_balance_forwarded
        return balance_in_hand - carry_balance, carry_balance
    return balance_in_hand, 0


def encash_balance(
    leave_account, encash_balance, balance_in_hand
):
    # using carry balance to determine the balance to reduce before consumption
    encash_allowed = leave_account.master_setting.encashment
    if not encash_allowed:
        leave_logger.info(f"Leave Encashment rejected for {leave_account.id}")
        return balance_in_hand, 0
    max_balance_encashed = encash_balance or 0

    if max_balance_encashed > 0 and balance_in_hand > 0:
        if balance_in_hand <= max_balance_encashed:
            encashment_balance = balance_in_hand
        else:
            encashment_balance = max_balance_encashed

        encashment = LeaveEncashment(
            user=leave_account.user,
            account=leave_account,
            status=GENERATED,
            balance=encashment_balance
        )
        balance_in_hand -= encashment_balance
        with transaction.atomic():
            encashment.save()
            LeaveEncashmentHistory.objects.create(
                encashment=encashment,
                actor=get_system_admin(),
                action=GENERATED,
                previous_balance=None,
                new_balance=encashment_balance,
                remarks="encashment added during renewal"
            )
            return balance_in_hand, encashment_balance
    return balance_in_hand, 0


def collapse_accumulative_balance(leave_account) -> None:
    """
    Collapse the remaining balance in the leave account if permitted by the
    system.
    :param leave_account:
    :return:
    """
    collapse_allowed = leave_account.master_setting.collapsible
    if (
        not collapse_allowed
        or not leave_account.rule.accumulation_rule.is_collapsible
    ):
        return
    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),  # SYSTEM is the Actor
        action=DEDUCTED,
        previous_balance=leave_account.balance,
        previous_usable_balance=leave_account.usable_balance,
        remarks=f'Collapsed by the System under collapsible'
    )
    # Collapse Usable Balance to Zero.
    difference = leave_account.balance - leave_account.usable_balance
    # difference is the no. of pending leaves.
    leave_account.usable_balance = 0
    leave_account.balance = leave_account.usable_balance + difference

    account_history.new_balance = leave_account.balance
    account_history.new_usable_balance = leave_account.usable_balance

    with transaction.atomic():
        leave_account.save()
        account_history.save()


def get_next_accrue_date_for_duration_days(
    leave_account: LeaveAccount,
    last_accrued: datetime.date
) -> datetime.date:
    def count_attendance_days(qs):
        """Count days from TimeSheet qs"""
        return qs.order_by().values('timesheet_for').annotate(count=Count('timesheet_for')).count()

    def count_leave_days(qs):
        """Return Leave days count from leave sheet qs"""
        return qs.aggregate(sum=Sum('balance'))['sum'] or 0

    today = common.get_today()
    accumulation_rule = leave_account.rule.accumulation_rule
    date_range_timesheets = TimeSheet.objects.filter(
        timesheet_for__gte=last_accrued,
        timesheet_for__lt=today,
        timesheet_user=leave_account.user
    )
    date_range_leavesheets = LeaveSheet.objects.filter(
        request__user=leave_account.user,
        leave_for__gte=last_accrued,
        leave_for__lt=today,
        request__is_deleted=False,
        request__status=APPROVED
    )

    deduct_days = 0

    leave_logger.debug(f"\n\nCALCULATING NEXT ACCRUE DATE OF {leave_account}")

    if accumulation_rule.exclude_absent_days:
        full_absent = date_range_timesheets.filter(
            is_present=False,
            coefficient=WORKDAY,
            leave_coefficient__in=[NO_LEAVE],
        )
        half_absent = date_range_timesheets.filter(
            is_present=False,
            coefficient=WORKDAY,
            leave_coefficient__in=[FIRST_HALF, SECOND_HALF],
        )
        leave_logger.debug(f"------------> FULL ABSENT {full_absent}")
        leave_logger.debug(f"------------> HALF ABSENT {half_absent}")
        deduct_days += (
            count_attendance_days(full_absent) +
            count_attendance_days(half_absent) * 0.5
        )

    if accumulation_rule.exclude_off_days:
        off_days = date_range_timesheets.filter(coefficient=OFFDAY)
        if accumulation_rule.count_if_present_in_off_day:
            off_days = off_days.exclude(is_present=True)
        leave_logger.debug(f"------------> OFF DAYS {off_days}")
        deduct_days += count_attendance_days(off_days)

    if accumulation_rule.exclude_holidays:
        holidays = date_range_timesheets.filter(coefficient=HOLIDAY)
        if accumulation_rule.count_if_present_in_holiday:
            holidays = holidays.exclude(is_present=True)

        leave_logger.debug(f"------------> HOLIDAYS {holidays}")
        deduct_days += count_attendance_days(holidays)

    if accumulation_rule.exclude_unpaid_leave:
        unpaid_leaves = date_range_leavesheets.filter(request__leave_account__rule__is_paid=False)
        if not accumulation_rule.exclude_half_leave:
            # balance can be one of 1 and 0.5
            unpaid_leaves = unpaid_leaves.exclude(balance__lt=1)
        leave_logger.debug(f"------------> UNPAID LEAVE {unpaid_leaves}")
        deduct_days += count_leave_days(unpaid_leaves)

    if accumulation_rule.exclude_paid_leave:
        paid_leaves = date_range_leavesheets.filter(request__leave_account__rule__is_paid=True)
        if not accumulation_rule.exclude_half_leave:
            # balance can be one of 1 and 0.5
            paid_leaves = paid_leaves.exclude(balance__lt=1)
        leave_logger.debug(f"------------> PAID LEAVE {paid_leaves}")
        deduct_days += count_leave_days(paid_leaves)

    leave_logger.debug(f"----------------->TOTAL DEDUCT DAYS: {deduct_days}")
    deduct_days = math.ceil(deduct_days)
    leave_logger.debug(f"----------------->TOTAL DEDUCT DAYS CEIL: {deduct_days}")
    leave_logger.debug(
        f"\n\nCALCULATED NEXT ACCRUE DATE OF {leave_account} as "
        f"{last_accrued + timezone.timedelta(days=(accumulation_rule.duration + deduct_days))}"
    )

    return last_accrued + timezone.timedelta(days=(accumulation_rule.duration + deduct_days))


def get_next_accrue_date(leave_account):
    next_run_after = leave_account.rule.accumulation_rule.duration
    next_run_after_unit = leave_account.rule.accumulation_rule.duration_type
    # Get Fiscal Year
    leave_account.refresh_from_db()
    leave_account_last_accrued = (
        leave_account.last_accrued.astimezone() if leave_account.last_accrued
        else get_leave_account_assigned_date(leave_account)
    )
    fiscal_year = get_fiscal_year_for_leave(
        organization=leave_account.master_setting.organization,
        date=leave_account_last_accrued
    )
    default = {
        DAYS: leave_account_last_accrued + timezone.timedelta(days=next_run_after + 1),
        MONTHS: leave_account_last_accrued + relativedelta(months=+next_run_after, days=1),
        YEARS: leave_account_last_accrued + relativedelta(years=+next_run_after, days=1),
    }.get(next_run_after_unit)
    if not fiscal_year:
        return default
    if next_run_after_unit == DAYS:
        return get_next_accrue_date_for_duration_days(leave_account, leave_account_last_accrued)
    if next_run_after_unit == MONTHS:
        fiscal_month_for_date = fiscal_year.fiscal_months.exclude(
            start_at__gt=leave_account_last_accrued,
        ).order_by('-start_at').first()
        if not fiscal_month_for_date:
            return default
        fiscal_month = fiscal_year.fiscal_months.filter(
            month_index=fiscal_month_for_date.month_index + next_run_after
        ).order_by('-start_at').first()
        return common.combine_aware(
            fiscal_month.start_at,
            time(0, 0)
        ) if fiscal_month else default
    if next_run_after_unit == YEARS:
        return common.combine_aware(
            fiscal_year.applicable_to + timezone.timedelta(days=1),
            time(0, 0)
        )


def get_next_renew_date(leave_account, today=common.get_today()):
    """To avoid multiple leave renewals due to date check, enforce timestamp check."""
    next_run_after = leave_account.rule.renewal_rule.duration
    next_run_after_unit = leave_account.rule.renewal_rule.duration_type
    fiscal = get_fiscal_year_for_leave(
        organization=leave_account.master_setting.organization,
        date=today
    )
    if next_run_after_unit == YEARS:
        # For yearly, the next renew date is start of next fiscal year.
        return fiscal.applicable_to + ONE_DAY if fiscal else None
    elif next_run_after_unit == MONTHS:
        this_fiscal_month = fiscal.fiscal_months.filter(
            start_at__lte=today,
            end_at__gte=today
        ).first() if fiscal else None
        if this_fiscal_month:
            return this_fiscal_month.start_at + relativedelta(
                months=next_run_after
            ) + ONE_DAY
        else:
            leave_logger.error(
                f"No Fiscal Month for {today}. Generated during Leave Renewal "
                f"for Leave Account {leave_account.id}"
            )
    elif next_run_after_unit == DAYS:
        return today + timezone.timedelta(days=next_run_after) + ONE_DAY


def accrue_balance_to_leave_account(leave_account) -> None:
    """
    Adds Balance to a given Leave Account.
    The values to add are taken from its accumulation rule.
    :param leave_account: applicable leave addition account.
    :return: None
    """
    # Previous balance preserved to log at the end.
    previous_balance = leave_account.balance
    previous_usable_balance = leave_account.usable_balance
    balance_to_add = leave_account.rule.accumulation_rule.balance_added
    last_accrued_date = leave_account.last_accrued.astimezone().date() if isinstance(
        leave_account.last_accrued, datetime
    ) else leave_account.last_accrued
    next_accrue = get_next_accrue_date(leave_account)
    if next_accrue > now():
        return
    # this balance to add would have worked if there were no gaps. As seen
    # in production, and a possible case anytime, the leave task does not
    # run regularly, hence leaping over the possible date of renewal.

    if not balance_to_add:
        leave_logger.warning(
            f"Found no balance to add on leave account {leave_account.id} "
        )
        return

    difference = leave_account.balance - leave_account.usable_balance
    leave_account.balance = leave_account.balance + balance_to_add
    max_bal = nested_getattr(leave_account, 'rule.max_balance')

    if max_bal and leave_account.balance > max_bal:
        leave_account.balance = leave_account.rule.max_balance

    leave_account.usable_balance = leave_account.balance - difference

    # next_accrue date is no longer valid.
    # Accrual now works dynamically, traversing valid accounts, and testing for their accrual date.
    # next_accrue date is guaranteed to be from the past.
    # it is set this way, so that leave accounts will not add a multiplier derived value to the leave account,
    # rather it moves in its own window, fixing absurd cases after each successive iteration.
    leave_account.last_accrued = leave_account.next_accrue = next_accrue

    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),  # SYSTEM is the Actor
        action=ADDED,
        previous_balance=previous_balance,
        previous_usable_balance=previous_usable_balance,
        new_balance=leave_account.balance,
        new_usable_balance=leave_account.usable_balance,
        remarks=f'Added {float(balance_to_add)} by the System under Accrual for period '
                f'{last_accrued_date} - {next_accrue.date()}'
    )
    with transaction.atomic():
        added_balance = (
            account_history.new_usable_balance
            - account_history.previous_balance
        )
        leave_logger.info(
            f"Added {added_balance} to {leave_account.user} on leave account "
            f"{leave_account.id} for period {last_accrued_date} - {next_accrue.date()}"
        )
        leave_account.save()
        account_history.accrued = added_balance
        account_history.save()


def renew_balance_to_leave_account(
    leave_account, balance_in_hand, carry_forward=0, encashment_balance=0
):
    """
    Adds Balance to a given Leave Account.
    The values to add are taken from its Renewal rule.
    :param leave_account: applicable leave addition account.
    :return: None
    """
    difference = leave_account.balance - leave_account.usable_balance
    if balance_in_hand > 0:
        if not nested_getattr(
            leave_account, 'rule.renewal_rule.is_collapsible'
        ):
            leave_logger.warning(
                f"The balance is greater than 0 for leave account "
                f"{leave_account.id} before renewal. It is expected 0"
            )
        else:
            is_credit = leave_account.usable_balance < 0
            leave_account.usable_balance = 0 if is_credit else \
                leave_account.usable_balance
            leave_account.balance = leave_account.usable_balance + difference

    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),  # SYSTEM is the Actor
        action=ADDED,
        previous_balance=leave_account.balance,
        previous_usable_balance=leave_account.usable_balance
    )

    user = leave_account.user
    currently_granted = leave_account.rule.renewal_rule.initial_balance
    proportionate_on_contract_end_date = leave_account.rule.proportionate_on_contract_end_date
    fiscal_year = get_fiscal_year_for_leave(user.detail.organization)

    if proportionate_on_contract_end_date:
        balance_to_add = get_balance_to_grant_after_contract_termination_penalty(
            user.current_experience,
            fiscal_year,
            currently_granted,
            currently_granted
        )
    else:
        balance_to_add = currently_granted

    leave_account.usable_balance = carry_forward + balance_to_add
    leave_account.balance = leave_account.usable_balance + difference

    leave_account.last_renewed = timezone.now()

    # get next renewal
    next_renew_date = get_next_renew_date(leave_account)
    leave_account.next_renew = common.combine_aware(
        next_renew_date, time(0, 0)
    ) if next_renew_date else None

    account_history.new_balance = leave_account.balance
    account_history.new_usable_balance = leave_account.usable_balance
    account_history.remarks = f'Renewed {balance_to_add} balance '
    if carry_forward and carry_forward > 0:
        account_history.remarks += f'and carry added {carry_forward} balance '
        account_history.carry_forward = carry_forward
    if encashment_balance and encashment_balance > 0:
        account_history.remarks += f'and encashed {encashment_balance} balance '
        account_history.encashed = encashment_balance
    if balance_in_hand > 0:
        account_history.remarks += f'and collapsed {balance_in_hand} balance '
        account_history.deducted = balance_in_hand
    account_history.renewed = balance_to_add
    account_history.remarks += 'by the System under Renewal'
    with transaction.atomic():
        leave_logger.info(
            f"Added {balance_to_add} to {leave_account.user} on leave account "
            f"{leave_account.id}"
        )
        leave_account.save()
        account_history.save()


def get_balance_to_grant_after_contract_termination_penalty(current_experience, fiscal_year,
                                                            currently_granted, yearly_balance):
    if fiscal_year and (
            current_experience and
            current_experience.end_date and
            current_experience.end_date < fiscal_year.end_at
    ):
        days_to_end = (
                fiscal_year.end_at - current_experience.end_date
        ).days
        balance_to_grant = currently_granted - int(
            yearly_balance / 365 * days_to_end
        )
        return balance_to_grant
    return currently_granted


def add_pro_rata_leave_balance(leave_account) -> None:
    """
    Adds initial balance to leave account.
    The balance will be a fraction of Renewal Balance based on the no. of days
    since fiscal year start

    Proportionate leave is calculated on the basis of how many days since the
    fiscal year has started.
    For 12 balance per annum:-
    Days Since Fiscal | Balance Granted
    ---|---
    1 | 12
    . | .
    30| 11
    . | .
    360|1

    :param leave_account: Leave Account to Add Initial Balance if applicable
    :return: None
    """
    current_user_experience = nested_getattr(leave_account, 'user.current_experience')
    if not current_user_experience:
        return

    enabled_pro_rata = leave_account.master_setting.proportionate_leave
    proportionate_on_joined_date = leave_account.rule.proportionate_on_joined_date
    proportionate_on_probation_end_date = leave_account.rule.proportionate_on_probation_end_date
    proportionate_on_contract_end_date = leave_account.rule.proportionate_on_contract_end_date
    # Check whether LeaveAccountHistory is assigned with default_balance or not.
    # If yes, return so that proportionate balance won't be granted.
    if leave_account.history.filter(action=ASSIGNED_WITH_BALANCE).exists():
        leave_logger.info(
            f"Leave Account {leave_account} have proportionate "
            f"enabled. Default balance input from user has been set."
        )
        return

    if not (
        enabled_pro_rata and (proportionate_on_joined_date or proportionate_on_contract_end_date
                              or proportionate_on_probation_end_date)
    ):
        renew_date = get_next_renew_date(leave_account)
        leave_logger.info(
            f"Leave Account {leave_account} does not have proportionate "
            f"enabled. No balance has been set. And the next renew date has "
            f"been set to {renew_date}"
        )
        leave_account.next_renew = renew_date
        leave_account.save()
        return
    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),  # SYSTEM is the Actor
        action=ADDED,
        previous_balance=leave_account.balance,
        previous_usable_balance=leave_account.usable_balance,
        remarks=f'Proportionate Leave by the System'
    )
    # proportionate leave according to the no. of days since fiscal start.
    doj = leave_account.user.detail.joined_date
    balance_to_grant = get_proportionate_leave_balance(
        leave_account,
        doj,
        current_user_experience.end_date
    )

    if balance_to_grant <= 0:
        leave_logger.info(
            f"Failed Proportionate Leave as calibrated balance was zero."
        )
        return
    leave_account.balance = leave_account.balance + balance_to_grant
    leave_account.usable_balance = (
        leave_account.usable_balance + balance_to_grant
    )
    account_history.new_balance = leave_account.balance
    account_history.new_usable_balance = leave_account.usable_balance
    leave_account.last_renewed = common.get_today(with_time=True)
    leave_account.next_renew = get_next_renew_date(leave_account)
    account_history.renewed = balance_to_grant
    with transaction.atomic():
        leave_account.save()
        account_history.save()


def get_proportionate_leave_balance(leave_account, start_date, end_date):
    proportionate_on_joined_date = leave_account.rule.proportionate_on_joined_date
    proportionate_on_contract_end_date = leave_account.rule.proportionate_on_contract_end_date
    proportionate_on_probation_end_date = leave_account.rule.proportionate_on_probation_end_date
    organization = leave_account.master_setting.organization
    fiscal_year = get_fiscal_year_for_leave(organization, common.get_today())

    renewal_rule = getattr(leave_account.rule, "renewal_rule", None)
    if not renewal_rule:
        return 0

    if not fiscal_year:
        leave_logger.debug('No fiscal Year to calculate proportionate leave balance')
        return 0

    yearly_balance = renewal_rule.initial_balance
    days_in_fy = (fiscal_year.end_at - fiscal_year.start_at).days + 1

    # CASES:
    # 1. start_date >= fy.start && end_date <= fy.end
    # A: _yearly * (to_pay)
    # ----------->
    # B: _yearly * (start-fy.start) given, fy.start <= start
    # -----------<
    # C: _yearly * (end-start) given, fy.end >= end

    if proportionate_on_probation_end_date and not proportionate_on_joined_date:
        probation_end_date = getattr(leave_account.user.user_experiences.first(), 'probation_end_date')
        if probation_end_date:
            from_date = max(fiscal_year.start_at, probation_end_date)
        else:
            return 0

    elif proportionate_on_joined_date and not proportionate_on_probation_end_date:
        from_date = max(fiscal_year.start_at, start_date)

    elif proportionate_on_joined_date and proportionate_on_probation_end_date:
        probation_end_date = getattr(leave_account.user.user_experiences.first(),
                                     'probation_end_date')
        from_date = max(fiscal_year.start_at, probation_end_date) if probation_end_date \
            else max(fiscal_year.start_at, start_date)
    else:
        from_date = fiscal_year.start_at

    if proportionate_on_contract_end_date:
        till_date = min(fiscal_year.end_at, end_date) if end_date else fiscal_year.end_at
    else:
        till_date = fiscal_year.end_at
    expected_user_availability_in_fy = (till_date - from_date).days + 1
    return round(yearly_balance / days_in_fy * expected_user_availability_in_fy)


def get_leave_account_assigned_date(leave_account):
    """
    Return the date, leave account was assigned to the user.

    :param leave_account:
    :return: latest Leave Account "ASSIGNED" history.created_at
    """
    leave_account_assigned_date = leave_account.history.filter(
        action=ASSIGNED
    ).order_by('-created_at').values_list('created_at', flat=True).first()
    if not leave_account_assigned_date:
        # default logic: now()
        leave_logger.warning(
            f"(Leave Account) fresh accrual without assigned history: ID({leave_account.id})"
        )
        return now()
    return leave_account_assigned_date


def accrue_leave_balance(
    *args, **kwargs  # args kwargs for backward compatibility of background task
):
    """
    Task for increment of leaves in intervals.
    """
    accrual_leave_rules = LeaveRule.objects.filter(
        leave_type__master_setting__in=MasterSetting.objects.all().active(),
        leave_type__master_setting__accumulation=True,
        accumulation_rule__isnull=False
    )  # Filter Leave Rules with accumulation
    leave_accounts_for_accrual = LeaveAccount.objects.filter(
        rule__in=accrual_leave_rules
    )  # Leave Accounts with accruable leave rules
    first_accrual = leave_accounts_for_accrual.filter(
        last_accrued__isnull=True
    )

    # today = common.get_today(with_time=True)

    # dry run leave accounts, set next_accure date
    for leave_account in first_accrual:
        # next_accrue_date = get_next_accrue_date(leave_account)
        # leave_logger.info(
        #     f"Setting next Accrue date to {next_accrue_date} for "
        #     f"user {leave_account.user} on leave account {leave_account.id}"
        # )
        leave_account.last_accrued = get_leave_account_assigned_date(leave_account)
        # leave_account.next_accrue = next_accrue_date
        leave_account.save()

    # Recurring Accruals
    # modify the logic to require next accrue date.
    # All leave accounts will be tested.
    # This will make the process slow; but be more reactive to changes
    # valid_accounts = filter(
    #     lambda leave_acc: get_next_accrue_date(leave_acc) <= today,
    #     leave_accounts_for_accrual
    # )
    for leave_account in leave_accounts_for_accrual:
        accrue_balance_to_leave_account(leave_account)


def renew_leave_balance(
    *args, **kwargs  # args kwargs for backward compatibility of background task
):
    """
    Renews Leave Balance in fixed durations
    :return: None
    """
    experience_qs = UserExperience.objects.filter(user=OuterRef('user__id')).values(
        'probation_end_date')[:1]
    # look at dry run and recurring runs.
    renewal_leave_rules = LeaveRule.objects.filter(
        leave_type__master_setting__in=MasterSetting.objects.all().active(),
        leave_type__master_setting__renewal=True,
        renewal_rule__isnull=False
    )  # Filter Leave Rules with Renewal
    leave_accounts_for_renewal = LeaveAccount.objects.filter(
        rule__in=renewal_leave_rules,
        is_archived=False
    )  # Leave Accounts with renewable leave rules
    first_renewal = leave_accounts_for_renewal.filter(
        last_renewed__isnull=True,
    ).annotate(prob_end_date=Subquery(experience_qs),
               prob_setting=F('rule__proportionate_on_probation_end_date'))
    changes_to_apply = []
    # dry run leave accounts.
    for leave_account in first_renewal:
        probation_end_date = leave_account.prob_end_date
        if not (leave_account.prob_setting and probation_end_date and probation_end_date > get_today()):
            changes_to_apply.append(leave_account.id)
            add_pro_rata_leave_balance(leave_account)

    recurring_renewal = leave_accounts_for_renewal.filter(
        last_renewed__isnull=False,
    )
    first_renewal.filter(id__in=changes_to_apply).update(
        last_renewed=timezone.now()
    )

    def test_valid_renew(account):
        last_renewed = account.last_renewed.astimezone()
        renew_date = get_next_renew_date(account, last_renewed)
        if renew_date:
            return last_renewed < common.combine_aware(
                renew_date, time(0, 0)
            ) <= common.get_today(with_time=True)
        return None

    for leave_account in filter(test_valid_renew, recurring_renewal):
        # filter renewal accounts if they meet their date.
        # handle functions with balance-in-hand logic
        balance_in_hand = leave_account.usable_balance
        max_forwarded = nested_getattr(
            leave_account,
            'rule.renewal_rule.max_balance_forwarded'
        )
        carry_balance = 0
        if max_forwarded and max_forwarded > 0:
            balance_in_hand, carry_balance = carry_forward_balance(
                leave_account=leave_account,
                carry_forward_balance=max_forwarded,
                balance_in_hand=balance_in_hand
            )
        max_encashed = nested_getattr(
            leave_account,
            'rule.renewal_rule.max_balance_encashed'
        )
        encashment_balance = 0
        if max_encashed and max_encashed > 0 and balance_in_hand > 0:
            balance_in_hand, encashment_balance = encash_balance(
                leave_account=leave_account,
                encash_balance=max_encashed,
                balance_in_hand=balance_in_hand
            )
        renew_balance_to_leave_account(
            leave_account,
            balance_in_hand=balance_in_hand,
            carry_forward=carry_balance,
            encashment_balance=encashment_balance
        )


def get_next_run_date(leave_account):
    next_run_after = leave_account.rule.deduction_rule.duration
    next_run_after_unit = leave_account.rule.deduction_rule.duration_type
    next_run_date = {
        DAYS: timezone.now() + timezone.timedelta(days=next_run_after),
        MONTHS: timezone.now() + relativedelta(months=+next_run_after),
        YEARS: timezone.now() + relativedelta(years=+next_run_after),
    }.get(next_run_after_unit)
    return next_run_date


def deduct_balance_from_leave(leave_account):
    """
    Takes a leave account and deducts the balance defined in its Deduction Rule.
    :param leave_account: Leave Account for balance deduction
    :return: None
    """
    balance_to_deduct = leave_account.rule.deduction_rule.balance_deducted
    difference = leave_account.balance - leave_account.usable_balance
    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),  # SYSTEM is the Actor
        action=DEDUCTED,
        previous_balance=leave_account.balance,
        previous_usable_balance=leave_account.usable_balance,
        remarks=f'Balance Deducted by the System according to deduction rule.'
    )
    leave_account.usable_balance = (
        leave_account.usable_balance - balance_to_deduct
    )
    min_balance_allowed = nested_getattr(
        leave_account, 'rule.min_balance'
    ) or 0
    if leave_account.usable_balance < min_balance_allowed:
        leave_account.usable_balance = min_balance_allowed
    leave_account.balance = leave_account.usable_balance + difference

    account_history.new_usable_balance = leave_account.usable_balance
    account_history.new_balance = leave_account.balance

    leave_account.last_deduction = timezone.now()

    # get next deduction
    leave_account.next_deduction = get_next_run_date(leave_account)

    with transaction.atomic():
        reduced_balance = (
            account_history.new_usable_balance
            - account_history.previous_usable_balance
        )
        leave_logger.info(
            f"Reduced {reduced_balance} from {leave_account.user} on leave "
            f"account {leave_account.id}"
        )
        leave_account.save()
        account_history.deducted = reduced_balance
        account_history.save()


def deduct_leave_balance(
    *args, **kwargs  # args kwargs for backward compatibility of background task
) -> None:
    """
    Deducts Leave Balance based on Deduction Rules
    :return:
    """
    today = timezone.now()
    deduction_leave_rules = LeaveRule.objects.filter(
        leave_type__master_setting__in=MasterSetting.objects.all().active(),
        leave_type__master_setting__deductible=True,
        deduction_rule__isnull=False
    )
    leave_accounts_for_deduction = LeaveAccount.objects.filter(

        rule__in=deduction_leave_rules
    )  # Leave Accounts with renewable leave rules
    first_deduction = leave_accounts_for_deduction.filter(
        last_renewed__isnull=True,
        next_renew__isnull=True
    )
    # dry run leave accounts.
    for leave_account in first_deduction:
        leave_account.next_deduction = get_next_run_date(leave_account)
        leave_account.save()

    recurring_deduction = leave_accounts_for_deduction.filter(
        last_deduction__isnull=False,
        next_deduction__isnull=False
    ).filter(
        next_deduction__lt=today,
        next_deduction__gte=today + timezone.timedelta(days=-1)
    )
    for leave_account in recurring_deduction:
        deduct_balance_from_leave(leave_account)


def collapse_yos_leaves(leave_account):
    """
    Collapses the leaves if not used within the timeframe.
    :param leave_account:
    :return:
    """
    now = timezone.now()
    if not leave_account.last_accrued:
        return  # Removal Inapplicable.
    collapse_after = leave_account.rule.yos_rule.collapse_after
    collapse_after_unit = leave_account.rule.yos_rule.collapse_after_unit
    if not collapse_after:
        return
    to_be_consumed_before = {
        DAYS: leave_account.last_accrued + timezone.timedelta(
            days=collapse_after),
        MONTHS: leave_account.last_accrued + relativedelta(
            months=collapse_after),
        YEARS: leave_account.last_accrued + relativedelta(years=collapse_after)
    }.get(collapse_after_unit)
    yos_granted = nested_getattr(
        leave_account,
        'rule.yos_rule.balance_added'
    )
    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),  # SYSTEM is the Actor
        action=REMOVED,
        previous_balance=leave_account.balance,
        previous_usable_balance=leave_account.usable_balance,
        remarks=f'Collapsed by the system according to YOS collapsible.'
    )
    if now >= to_be_consumed_before:
        # leave has expired.
        # remove the balance
        difference = leave_account.balance - leave_account.usable_balance
        if leave_account.balance >= yos_granted:
            leave_account.usable_balance -= yos_granted
            leave_account.balance = leave_account.usable_balance + difference
        else:
            leave_account.usable_balance = leave_account.rule.min_balance
            leave_account.balance = leave_account.usable_balance + difference

        account_history.new_usable_balance = leave_account.usable_balance
        account_history.new_balance = leave_account.balance

        leave_account.last_deduction = timezone.now()

        with transaction.atomic():
            f"Collapsed Year of Service of {leave_account.user} on leave "
            f"account {leave_account.id}"
            leave_account.save()
            account_history.save()


def add_yos_leaves(leave_account) -> None:
    """
    Adds Balance to Leave Accounts whose years of service have completed.
    :param leave_account:  Leave Account for YOS leave addition
    :return: None
    """
    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),  # SYSTEM is the Actor
        action=ADDED,
        previous_balance=leave_account.balance,
        previous_usable_balance=leave_account.usable_balance,
        remarks=f'Added by the System under YOS Addition'
    )
    doj = leave_account.user.detail.joined_date
    if not doj:
        return
    if doj > (
        common.get_today()
        - relativedelta(years=leave_account.rule.yos_rule.years_of_service)
    ):
        return

    leave_account.usable_balance += leave_account.rule.yos_rule.balance_added
    leave_account.balance += leave_account.rule.yos_rule.balance_added
    leave_account.last_accrued = timezone.now()

    account_history.new_balance = leave_account.balance
    account_history.new_usable_balance = leave_account.usable_balance

    with transaction.atomic():
        leave_logger.info(
            f"Added {leave_account.rule.yos_rule.balance_added} to "
            f"{leave_account.user} on leave account {leave_account.id} "
            f"according to year of service rule"
        )
        leave_account.save()
        account_history.save()


def manage_yos_leaves(
    *args, **kwargs  # args kwargs for backward compatibility of background task
) -> None:
    """
    Adds Leave to Users whose employment experience has exceeded the defined
    years of organization service.
    Needs the check in Master Setting.
    # NOTE: `yos` refers to `Years of Service`
    :return: None
    """

    yos_leave_rules = LeaveRule.objects.filter(
        leave_type__master_setting__in=MasterSetting.objects.all().active(),
        leave_type__master_setting__years_of_service=True,
        yos_rule__isnull=False
    )

    yos_applicable_leave_accounts = LeaveAccount.objects.filter(

        rule__in=yos_leave_rules
    )
    for leave_account in yos_applicable_leave_accounts.filter(
        last_accrued__isnull=False
    ):
        collapse_yos_leaves(leave_account)
    for leave_account in yos_applicable_leave_accounts.filter(
        last_accrued__isnull=True
    ):
        add_yos_leaves(leave_account)


def unchanged(account_history):
    """
    Helper function to decide if the account_history has any changes made.
    This is to prevent from unnecessary history made.
    :param account_history: Account History Object
    :return: if the account history is necessarily changed.
    """
    difference_balance = (
        account_history.previous_balance - account_history.new_balance
    )
    difference_usable = (
        account_history.previous_usable_balance
        - account_history.new_usable_balance
    )
    return difference_usable == 0 or difference_balance == 0


@transaction.atomic()
def add_compensatory_leave(leave_account, timesheet):
    """
    Add compensatory leave to a timesheet
    :param leave_account:
    :param timesheet:
    :return:
    """
    time_at_office = timesheet.punch_out - timesheet.punch_in  # total worked
    working_hours = time_at_office.total_seconds() / (60 * 60)
    compensatory_leave = leave_account.rule.compensatory_rules.filter(
        hours_in_off_day__lte=working_hours
    ).order_by('-balance_to_grant').first()
    if not compensatory_leave:
        return
    hours_in_off_day = compensatory_leave.hours_in_off_day
    balance_to_grant = compensatory_leave.balance_to_grant

    if working_hours >= hours_in_off_day:
        leave, created = leave_account.compensatory_leave.get_or_create(
            timesheet=timesheet,
            leave_for=timesheet.timesheet_for,
            balance_granted=balance_to_grant
        )
        if not created:
            return
        account_history = LeaveAccountHistory(
            account=leave_account,
            user=leave_account.user,
            actor=get_system_admin(),
            action=ADDED,
            previous_balance=leave_account.balance,
            previous_usable_balance=leave_account.usable_balance,
            remarks=f'Granted {balance_to_grant} leave as worked for '
                    f'{round(working_hours, 2)} hours on '
                    f'{timesheet.timesheet_for} which was '
                    f'{timesheet.get_coefficient_display()}'
        )
        leave_account.balance += balance_to_grant
        leave_account.usable_balance += balance_to_grant
        leave.balance_granted = balance_to_grant
        account_history.new_usable_balance = leave_account.usable_balance
        account_history.new_balance = leave_account.balance

        if unchanged(account_history):
            return
        leave_account.save()
        account_history.save()


def calculate_collapse_balance(pending_balance, collapse_balance):
    if pending_balance >= collapse_balance:
        pending_balance -= collapse_balance
        collapse_balance = 0
    else:
        collapse_balance = collapse_balance - pending_balance
        pending_balance = 0
    return pending_balance, collapse_balance


@transaction.atomic()
def collapse_compensatory_leave(leave_account):
    """
    :param leave_account:
    :return:
    """
    today = common.get_today()
    collapsible_rule = leave_account.rule.leave_collapsible_rule
    collapse_after = collapsible_rule.collapse_after
    collapse_after_unit = collapsible_rule.collapse_after_unit

    if not (collapse_after and collapse_after_unit):
        return

    collapse_on = {
        YEARS: relativedelta(years=collapse_after),
        MONTHS: relativedelta(months=collapse_after),
        DAYS: relativedelta(days=collapse_after)
    }.get(collapse_after_unit)

    if not collapse_on:
        return
    compensatory_leave_begin_date = today - collapse_on
    compensatory_leaves = leave_account.compensatory_leave.filter(
        balance_consumed__lt=F('balance_granted'),
        leave_for__lte=compensatory_leave_begin_date
    )

    pending_balance = leave_account.leave_requests.filter(
        status__in=(
            REQUESTED,
            FORWARDED
        )
    ).aggregate(
        pending_balance=Sum(
            'balance'
        )
    ).get(
        'pending_balance'
    ) or 0

    for granted_date in compensatory_leaves.order_by('-leave_for'):
        """
        The collapses here are valid for most cases;
        However, as per
        [HRIS-1366]:
            If compensatory leave balance deadline is reached and leave is in requested status,
            It should be collapsed after leave is denied.
            Currently leave balance collapse if it is in requested state i.e. pending.
        """
        collapse_balance = granted_date.balance_granted - granted_date.balance_consumed
        pending_balance, collapse_balance = calculate_collapse_balance(
            pending_balance, collapse_balance
        )
        if collapse_balance == 0:
            continue
        account_history = LeaveAccountHistory(
            account=leave_account,
            user=leave_account.user,
            actor=get_system_admin(),
            action=DEDUCTED,
            previous_balance=leave_account.balance,
            previous_usable_balance=leave_account.usable_balance,
        )
        difference = leave_account.balance - leave_account.usable_balance
        leave_account.usable_balance -= collapse_balance
        leave_account.balance = leave_account.usable_balance + difference
        account_history.new_usable_balance = leave_account.usable_balance
        account_history.new_balance = leave_account.balance
        remarks = f'Collapsed {collapse_balance} balance for {granted_date.leave_for}'
        account_history.remarks = remarks
        granted_date.balance_consumed = granted_date.balance_consumed + collapse_balance
        granted_date.save()
        leave_account.save()
        account_history.save()


def add_compensatory_leaves(
    *args, **kwargs  # args kwargs for backward compatibility of background task
):
    """
    Generates compensatory leave if the timesheet exceeds the defined hours.
    :return:
    """
    compensatory_leave_rules = LeaveRule.objects.filter(
        leave_type__master_setting__in=MasterSetting.objects.all().active(),
        leave_type__master_setting__compensatory=True,
        compensatory_rules__isnull=False,
        leave_collapsible_rule__isnull=False
    )
    today = timezone.now().date()
    from_date = (today - timezone.timedelta(days=settings.COMPENSATORY_LEAVE_CALCULATION_DURATION))
    attendance_with_shifts = IndividualUserShift.objects.filter(
        Q(applicable_to__isnull=True) |
        Q(applicable_to__gte=timezone.now().date())
    ).values('individual_setting')
    applicable_accounts = LeaveAccount.objects.filter(
        rule__in=compensatory_leave_rules,
        user__attendance_setting__isnull=False,
        user__attendance_setting__in=attendance_with_shifts
    )
    for leave_account in applicable_accounts:
        collapse_compensatory_leave(leave_account)

    # timesheets for grant Compensatory
    fil = {
        'timesheet_for__gte': from_date,
        'timesheet_for__lte': today
    }

    for timesheet in TimeSheet.objects.filter(
        punch_out__isnull=False,
        is_present=True,
        coefficient__in=[HOLIDAY, OFFDAY],
        compensatory_leave__isnull=True,
        timesheet_user__leave_accounts__in=applicable_accounts,
        **fil
    ):
        user = timesheet.timesheet_user
        leave_account = applicable_accounts.filter(
            user=user,
            is_archived=False
        ).first()
        if leave_account:
            add_compensatory_leave(leave_account, timesheet)


def add_reduce_leaves(
    *args, **kwargs  # args kwargs for backward compatibility of background task
):
    """
    Main Task for Leave Addition and Deduction methods.
    Runs the task in following sequence:
        * Leave Accrue
        * Leave Renew
        * Leave Deduction
        * YOS Leave
    :return: None
    """
    leave_logger.debug("Task for Leave Accrue Started")
    accrue_leave_balance()
    leave_logger.debug("Task for Leave Deduction Started")
    deduct_leave_balance()
    leave_logger.debug("Task for YOS Leave Started")
    manage_yos_leaves()
    leave_logger.debug("Task for Compensatory Leave Started")
    add_compensatory_leaves()
    leave_logger.debug("Task for Leave Renew Started")
    renew_leave_balance()
    leave_logger.debug("Task for Leave Ended")


def add_credit_balance_to_leave_account(leave_account, balance) -> None:
    """
    Adds Balance to a given Leave Account.
    :param leave_account: applicable credit leave account.
    :param balance: balance to add to the account.
    :return: None
    """
    # Previous balance preserved to log at the end.
    previous_balance = leave_account.balance
    previous_usable_balance = leave_account.usable_balance
    balance_to_add = leave_account.rule.accumulation_rule.balance_added
    # this balance to add would have worked if there were no gaps. As seen
    # in production, and a possible case anytime, the leave task does not
    # run regularly, hence leaping over the possible date of renewal.

    if not balance_to_add:
        leave_logger.warning(
            f"Found no balance to add on leave account {leave_account.id} "
        )
        return

    # find balance to add over the course of time
    # i.e. if the balance to be added is 1 for 20 days,
    # if the days magically became 40, grant 2.
    # if the days became 50, grant 2, set the next renewal for 10 days later.

    if leave_account.rule.accumulation_rule.duration_type == DAYS:
        overshoot_period = (
            now() - leave_account.next_accrue
        ).days
    else:
        delta_overshoot = relativedelta(
            dt1=now(),
            dt2=leave_account.next_accrue
        )
        # get relative from accumulation rule.duration_type
        overshoot_period = {
            MONTHS: delta_overshoot.months,
            YEARS: delta_overshoot.years
        }.get(leave_account.rule.accumulation_rule.duration_type)

    # mod divide, the balance to be granted and next accrual.
    multiplier, interval_renew = divmod(
        overshoot_period,
        leave_account.rule.accumulation_rule.duration
    )
    to_add = leave_account.rule.accumulation_rule.duration * (multiplier + 1)
    next_run_date = leave_account.next_accrue + {
        DAYS: relativedelta(days=to_add),
        MONTHS: relativedelta(months=to_add),
        YEARS: relativedelta(years=to_add)
    }.get(
        leave_account.rule.accumulation_rule.duration_type
    )
    balance_added = balance_to_add * (multiplier + 1)

    difference = leave_account.balance - leave_account.usable_balance
    leave_account.balance = leave_account.balance + balance_added
    max_bal = nested_getattr(leave_account, 'rule.max_balance')

    if max_bal and leave_account.balance > max_bal:
        leave_account.balance = leave_account.rule.max_balance

    leave_account.usable_balance = leave_account.balance - difference

    leave_account.last_accrued = timezone.now()

    leave_account.next_accrue = next_run_date

    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),  # SYSTEM is the Actor
        action=ADDED,
        previous_balance=previous_balance,
        previous_usable_balance=previous_usable_balance,
        new_balance=leave_account.balance,
        new_usable_balance=leave_account.usable_balance,
        remarks=f'Added by the System under Accrual'
    )
    with transaction.atomic():
        added_balance = (
            account_history.new_usable_balance
            - account_history.previous_balance
        )
        leave_logger.info(
            f"Added {added_balance} to {leave_account.user} on leave account "
            f"{leave_account.id}"
        )
        leave_account.save()
        account_history.accrued = added_balance
        account_history.save()


def reduce_credit_balance_from_leave_account(leave_account, balance) -> None:
    """
    Adds Balance to a given Leave Account.
    The values to add are taken from its accumulation rule.
    :param leave_account: applicable leave addition account.
    :param balance: balance to reduce from leave account.
    :return: None
    """
    # Previous balance preserved to log at the end.
    previous_balance = leave_account.balance
    previous_usable_balance = leave_account.usable_balance
    balance_to_add = leave_account.rule.accumulation_rule.balance_added
    # this balance to add would have worked if there were no gaps. As seen
    # in production, and a possible case anytime, the leave task does not
    # run regularly, hence leaping over the possible date of renewal.

    if not balance_to_add:
        leave_logger.warning(
            f"Found no balance to add on leave account {leave_account.id} "
        )
        return

    # find balance to add over the course of time
    # i.e. if the balance to be added is 1 for 20 days,
    # if the days magically became 40, grant 2.
    # if the days became 50, grant 2, set the next renewal for 10 days later.

    if leave_account.rule.accumulation_rule.duration_type == DAYS:
        overshoot_period = (
            now() - leave_account.next_accrue
        ).days
    else:
        delta_overshoot = relativedelta(
            dt1=now(),
            dt2=leave_account.next_accrue
        )
        # get relative from accumulation rule.duration_type
        overshoot_period = {
            MONTHS: delta_overshoot.months,
            YEARS: delta_overshoot.years
        }.get(leave_account.rule.accumulation_rule.duration_type)

    # mod divide, the balance to be granted and next accrual.
    multiplier, interval_renew = divmod(
        overshoot_period,
        leave_account.rule.accumulation_rule.duration
    )
    to_add = leave_account.rule.accumulation_rule.duration * (multiplier + 1)
    next_run_date = leave_account.next_accrue + {
        DAYS: relativedelta(days=to_add),
        MONTHS: relativedelta(months=to_add),
        YEARS: relativedelta(years=to_add)
    }.get(
        leave_account.rule.accumulation_rule.duration_type
    )
    balance_added = balance_to_add * (multiplier + 1)

    difference = leave_account.balance - leave_account.usable_balance
    leave_account.balance = leave_account.balance + balance_added
    max_bal = nested_getattr(leave_account, 'rule.max_balance')

    if max_bal and leave_account.balance > max_bal:
        leave_account.balance = leave_account.rule.max_balance

    leave_account.usable_balance = leave_account.balance - difference

    leave_account.last_accrued = timezone.now()

    leave_account.next_accrue = next_run_date

    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),  # SYSTEM is the Actor
        action=ADDED,
        previous_balance=previous_balance,
        previous_usable_balance=previous_usable_balance,
        new_balance=leave_account.balance,
        new_usable_balance=leave_account.usable_balance,
        remarks=f'Added by the System under Accrual'
    )
    with transaction.atomic():
        added_balance = (
            account_history.new_usable_balance
            - account_history.previous_balance
        )
        leave_logger.info(
            f"Added {added_balance} to {leave_account.user} on leave account "
            f"{leave_account.id}"
        )
        leave_account.save()
        account_history.accrued = added_balance
        account_history.save()
