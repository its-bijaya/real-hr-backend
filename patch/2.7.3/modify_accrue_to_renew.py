from django.contrib.auth import get_user_model

from irhrs.leave.constants.model_constants import UPDATED, YEARS
from irhrs.leave.models import LeaveRule, RenewalRule, AccumulationRule, LeaveAccount

User = get_user_model()
eligible_users = User.objects.filter().current()

leave_rule = LeaveRule.objects.filter(
    id=5
).get()

# modify leave rule from accumulation to renewal.
# if accumulation exists, delete,
# if renewal does not exist, create
# if renewal exists, modify

RenewalRule.objects.update_or_create(
    rule=leave_rule,
    defaults={
        'duration': 1,
        'duration_type': YEARS,
        'initial_balance': 12,
        'max_balance_encashed': None,
        'max_balance_forwarded': None,
        'is_collapsible': True,
        'back_to_default_value': False,
    }
)

base = AccumulationRule.objects.filter(rule=leave_rule)
print(
    'Existing accumulation rule',
    'Found' if base.exists() else 'False'
)
if base.exists():
    base.delete()


for leave_account in LeaveAccount.objects.filter(rule=leave_rule):
    leave_account.last_renewed = '2020-04-13'
    leave_account.next_renew = '2021-04-13'
    leave_account.save()
    print(leave_account, leave_account.last_renewed, leave_account.next_renew)
