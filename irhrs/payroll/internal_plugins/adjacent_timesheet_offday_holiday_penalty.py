from django.db.models import Sum

from irhrs.leave.models.account import AdjacentTimeSheetOffdayHolidayPenalty
from irhrs.payroll.internal_plugins.registry import register_plugin


@register_plugin('adjacent-offday-penalty-days')
def adjacent_timesheet_offday_holiday_penalty_reduction(calculator, package_heading):
    employee = calculator.employee
    from_date = calculator.from_date
    to_date = calculator.to_date
    queryset = AdjacentTimeSheetOffdayHolidayPenalty.objects.exclude(
        processed=True
    ).filter(
        leave_account__user=employee,
        penalty_for__range=(from_date, to_date),
    )
    days = queryset.aggregate(penalty_count=Sum('penalty')).get('penalty_count') or 0
    sources = [{
            'model_name': 'AdjacentTimeSheetOffdayHolidayPenalty',
            'instance_id': pk,
            'url': ''
        } for pk in queryset.values_list('id', flat=True)
    ]
    return days, sources
