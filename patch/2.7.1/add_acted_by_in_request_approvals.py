from django.db.models import F

from irhrs.core.constants.payroll import DENIED, APPROVED
from irhrs.reimbursement.models import AdvanceExpenseRequestApproval, SettlementApproval

# for advance
request_approvals = AdvanceExpenseRequestApproval.objects.filter(
    acted_by__isnull=True, status__in=[APPROVED, DENIED]
)
print('Updated advance request approvals: ')
print(request_approvals.values_list('id', flat=True))
request_approvals.update(acted_by=F('modified_by'))

# for settlement
settlement_approvals = SettlementApproval.objects.filter(
    acted_by__isnull=True, status__in=[APPROVED, DENIED]
)
print('Updated settlement request approvals: ')
print(settlement_approvals.values_list('id', flat=True))
settlement_approvals.update(acted_by=F('modified_by'))
