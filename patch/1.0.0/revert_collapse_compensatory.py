from django.db import transaction

from irhrs.core.utils import get_system_admin
from irhrs.leave.models import LeaveAccountHistory

CGREEN = '\33[32m'
CRED = '\33[31m'
CBOLD = '\33[1m'
CEND = '\33[0m'

account_history = LeaveAccountHistory.objects.filter(
    actor=get_system_admin(),
    action='Deducted',
    remarks__startswith='Collapsed'
)
print(
    CGREEN + CBOLD,
    account_history.count(), 'to be reverted',
    CEND
)
reverted = []

with transaction.atomic():
    for history in account_history.order_by('-new_balance'):
        leave_account = history.account
        remarks = history.remarks
        usable_balance_reduced = history.previous_usable_balance - history.new_usable_balance
        hist = LeaveAccountHistory(
            account=leave_account,
            user=leave_account.user,
            actor=get_system_admin(),
            action='Added',
            previous_balance=leave_account.balance,
            previous_usable_balance=leave_account.usable_balance,
            remarks=f'Reverted the collapsed balance'
        )
        difference = leave_account.balance - leave_account.usable_balance
        leave_account.usable_balance += usable_balance_reduced
        leave_account.balance = leave_account.usable_balance + difference
        hist.new_usable_balance = leave_account.usable_balance
        hist.new_balance = leave_account.balance
        history.remarks = f"[Reverted] {remarks}"
        history.save()
        leave_account.save()
        hist.save()
        reverted.append(history.id)
        print(
            CGREEN,
            'Added', usable_balance_reduced, 'to ', leave_account.id,
            CEND
        )

print(CRED, CBOLD, 'Reverted Ids', CEND)
print(CGREEN, CBOLD, reverted, CEND)
