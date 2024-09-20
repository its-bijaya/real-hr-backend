from logging import getLogger

from django.db.models import F, ExpressionWrapper, DurationField, FloatField, Sum
from django.db.models.functions import Greatest, Least, Extract

from irhrs.hris.models import DutyStationAssignment
from irhrs.organization.models import FiscalYear
from irhrs.payroll.internal_plugins.registry import register_plugin

logger = getLogger(__name__)


@register_plugin('employee-duty-station-rebate')
def duty_station_plugin(calculator, package_heading):

    employee = calculator.employee
    from_date = calculator.from_date
    to_date = calculator.to_date

    active_fiscal_year = FiscalYear.objects.active_for_date(
        organization=employee.detail.organization,
        date_=to_date,
    )
    logger.debug(f"------------------- INSIDE PLUGIN ----------------------")
    logger.debug(f"employee: {employee} from_date: {from_date}, to_date: {to_date}")
    if not active_fiscal_year:
        logger.debug(f"No fiscal year found")
        return 0, []

    fiscal_start_date = active_fiscal_year.start_at
    fiscal_end_date = active_fiscal_year.end_at
    days_in_fy = (active_fiscal_year.end_at - active_fiscal_year.start_at).days + 1

    queryset = DutyStationAssignment.objects.filter(
        user=employee,
        to_date__gte=fiscal_start_date,
        from_date__lte=fiscal_end_date
    ).annotate(
        actual_from_date=Greatest(fiscal_start_date, F('from_date')),
        actual_to_date=Least(fiscal_end_date, F('to_date'))
    ).annotate(
        num_days=(Extract(
            ExpressionWrapper(
                F('actual_to_date') - F('actual_from_date'), output_field=DurationField()
            ), 'epoch'
        ) / 86400) + 1
    )
    logger.debug(queryset.values('duty_station__name', 'num_days'))
    rebate = queryset.annotate(
        rebate_amount=ExpressionWrapper(
            F('num_days') * (F('duty_station__amount') / days_in_fy),
            output_field=FloatField()
        )
    ).aggregate(
        total_rebate=Sum(
            'rebate_amount'
        )
    )['total_rebate'] or 0

    sources = [
        {'model_name': 'DutyStation', 'instance_id': pk, 'url': ''}
        for pk in
        queryset.values_list('id', flat=True)
    ]

    return rebate, sources
