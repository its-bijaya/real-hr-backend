from datetime import timedelta
from math import floor

from irhrs.core.utils import nested_getattr
from irhrs.leave.constants.model_constants import CREDIT_HOUR
from irhrs.leave.models import LeaveAccount, MasterSetting


def convert_timedelta_to_minutes(duration):
    assert isinstance(duration, timedelta), "Only pass timedelta"
    return floor(duration.total_seconds() / 60)


def get_leave_account_for(credit_timesheet_entry):
    user = credit_timesheet_entry.timesheet.timesheet_user
    # Filter currently active leave account of user with Credit Hour Enabled.
    account = get_credit_leave_account_qs().filter(
        user=user,
    ).first()
    return account


def get_credit_leave_account_qs():
    return LeaveAccount.objects.filter(
        rule__leave_type__category=CREDIT_HOUR,
        is_archived=False,
        rule__leave_type__master_setting__in=MasterSetting.objects.all().active()
    )


def is_credit_hours_editable(credit_hour_request):
    return nested_getattr(
        credit_hour_request,
        'sender.attendance_setting.credit_hour_setting.allow_edit_of_pre_approved_credit_hour'
    )


def get_credit_leave_account_for_user(user):
    return get_credit_leave_account_qs().filter(
        user=user
    ).first()


def leave_account_exceeds_max_limit(leave_account, duration, undecided_sum):
    limit = leave_account.rule.max_balance
    if not limit:
        # If zero or null, we take it as unlimited.
        return False
    additive = convert_timedelta_to_minutes(duration)
    potential = convert_timedelta_to_minutes(undecided_sum)
    current_balance = leave_account.usable_balance
    if (additive + current_balance + potential) > limit:
        return True


def deletable_credit_request(credit_hour_request):
    credit_entry = getattr(credit_hour_request, 'credit_entry', None)
    if not credit_entry:
        return True
    leave_account = get_leave_account_for(credit_entry)
    if not leave_account:
        return True
    balance_added_to_leave_account = convert_timedelta_to_minutes(
        credit_entry.earned_credit_hours
    )
    balance_remaining_in_leave_account = leave_account.usable_balance
    if balance_remaining_in_leave_account >= balance_added_to_leave_account:
        return True
    return False
