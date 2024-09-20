from irhrs.leave.models import LeaveRule, AccumulationRule, LeaveAccount

leave_rule_to_modify = 6


leave_rule = LeaveRule.objects.get(pk=leave_rule_to_modify)
YEARS, MONTHS, DAYS = "Years", "Months", "Days"

AccumulationRule.objects.update_or_create(
    rule=leave_rule,
    defaults={
        'duration': 1,
        'duration_type': MONTHS,
        'balance_added': 1,
    }
)

for leave_account in LeaveAccount.objects.filter(
    rule=leave_rule,
    is_archived=False,
):
    leave_account.last_accrued = '2020-09-01'
    leave_account.save()
