from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.core.utils import get_system_admin
from irhrs.leave.constants.model_constants import DEDUCTED, GENERAL, CREDIT_HOUR
from irhrs.leave.models import LeaveAccount, LeaveRequest, LeaveAccountHistory

REQUESTED, APPROVED, DENIED, FORWARDED = 'Requested', 'Approved', 'Denied', 'Forwarded'


def get_display(leave_acc, balance):
    if leave_acc.rule.leave_type.category == GENERAL:
        return balance
    if leave_acc.rule.leave_type.category == CREDIT_HOUR:
        return humanize_interval(balance * 60)


for leave_account in LeaveAccount.objects.all():
    # if leave account has requests in undecided state, do not process.
    pending_leave_requests = LeaveRequest.objects.filter(
        leave_account=leave_account,
        status__in=[REQUESTED, FORWARDED]
    ).exists()
    if pending_leave_requests:
        print('Existing Leave Requests for', leave_account)
        continue

    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),  # SYSTEM is the Actor
        action=DEDUCTED,
        previous_balance=leave_account.balance,
        previous_usable_balance=leave_account.usable_balance
    )
    leave_account.usable_balance = 0
    leave_account.balance = 0

    account_history.new_balance = leave_account.balance
    account_history.new_usable_balance = leave_account.usable_balance
    account_history.remarks = f'Revert Leave Account to {get_display(leave_account, 0)}'
    leave_account.save()
    account_history.save()
