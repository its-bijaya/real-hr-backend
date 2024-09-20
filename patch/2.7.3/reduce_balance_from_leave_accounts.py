from django.contrib.auth import get_user_model

from irhrs.core.utils import get_system_admin
from irhrs.leave.constants.model_constants import UPDATED
from irhrs.leave.models import LeaveRule, LeaveAccount, LeaveAccountHistory

User = get_user_model()
eligible_users = User.objects.filter().current()

leave_rule_filter = LeaveRule.objects.filter(
    id=5
).get()

eligible_leave_accounts_base = LeaveAccount.objects.filter(
    rule=leave_rule_filter,
    user__in=eligible_users,
    is_archived=False,
)
reduction_filter = eligible_leave_accounts_base.filter(
    is_archived=False
)

BALANCE_TO_REDUCE = 2
leave_accounts_with_sufficient_balance = reduction_filter.filter(usable_balance__gt=BALANCE_TO_REDUCE)
for leave_account in leave_accounts_with_sufficient_balance:
    previous_balance = leave_account.balance
    previous_usable_balance = leave_account.usable_balance
    leave_account.balance = leave_account.balance - BALANCE_TO_REDUCE
    leave_account.usable_balance = leave_account.usable_balance - BALANCE_TO_REDUCE
    leave_account.save()

    # excerpt from Leave Account Serializer

    LeaveAccountHistory.objects.create(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),
        action=UPDATED,
        previous_balance=previous_balance,
        previous_usable_balance=previous_usable_balance,
        new_balance=leave_account.balance,
        new_usable_balance=leave_account.usable_balance,
        remarks="Leave Audit"
    )

print(
    leave_accounts_with_sufficient_balance.count(),
    f'Leave Accounts were updated with (-{BALANCE_TO_REDUCE})'
)

insufficient = reduction_filter.exclude(usable_balance__gt=BALANCE_TO_REDUCE)
if insufficient.exists():
    print(
        insufficient.count(),
        'Leave Accounts could not be reduced. Listed Below: '
    )
    for la in insufficient:
        print(la.usable_balance, la)
