# GENESE LEAVE PATCH [#2760]
# Update Leave rule: Annual Leave
#
# id: 19,
# require_prior_approval: true,
# prior_approval: "3",
# prior_approval_unit: "Days"
from irhrs.leave.models import LeaveRule
YEARS, MONTHS, DAYS = "Years", "Months", "Days"


leave_rule = LeaveRule.objects.get(pk=19)
leave_rule.require_prior_approval = True
leave_rule.prior_approval = 3
leave_rule.prior_approval_unit = DAYS

leave_rule.save()
