"""
TimeSheetPenaltyToPayroll [break-in-break-out-penalty)
TimeSheetPenaltyToPayroll [offday-unpaid-full-leave]
"""
from django.db.models import Sum

from irhrs.attendance.models.breakout_penalty import TimeSheetPenaltyToPayroll
from irhrs.payroll.internal_plugins.registry import register_plugin


@register_plugin('days-deduction-from-penalty')
def timesheet_penalty_reduction(calculator, package_heading):

    employee = calculator.employee
    from_date = calculator.from_date
    to_date = calculator.to_date

    queryset = TimeSheetPenaltyToPayroll.objects.filter(
        user_penalty__user=employee,
        confirmed_on__range=(from_date, to_date),
    )
    days = queryset.aggregate(penalty_count=Sum(
        'days')).get('penalty_count') or 0
    sources = [{
        'model_name': 'TimeSheetPenaltyToPayroll',
        'instance_id': pk,
        'url': ''
    } for pk in queryset.values_list('id', flat=True)
    ]
    return days, sources
