from django.db import models
from django.db.models import Subquery, OuterRef, Sum, Value, F

from irhrs.core.constants.payroll import APPROVED
from irhrs.reimbursement.models import ExpenseSettlement, SettlementHistory

from irhrs.payroll.internal_plugins.registry import register_plugin


@register_plugin('employee-taxable-expense')
def taxable_expense(calculator, package_heading):

    employee = calculator.employee
    from_date = calculator.from_date
    to_date = calculator.to_date

    queryset = ExpenseSettlement.objects.filter(
        status=APPROVED,
        employee=employee,
        is_taxable=True
    ).annotate(
        approved_date=Subquery(
            SettlementHistory.objects.filter(
                request=OuterRef('pk'),
                action=APPROVED
            ).order_by('-created_at').values('created_at__date')[:1]
        )
    ).filter(
        approved_date__lte=to_date,
        approved_date__gte=from_date,
    )
    amount = queryset.aggregate(amount=Sum('total_amount'))['amount'] or 0
    sources = list(queryset.values(
        model_name=Value('ExpenseSettlement', output_field=models.CharField()),
        instance_id=F('pk'),
        url=Value('', output_field=models.CharField())
    ))

    return amount, sources
