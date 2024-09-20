from typing import Sequence

from django.db import models
from django.db.models import Value, F, Sum

from irhrs.organization.models import FiscalYear
from irhrs.payroll.constants import MONTHLY
from irhrs.payroll.internal_plugins.registry import register_plugin
from irhrs.payroll.models import UserVoluntaryRebate, CREATED, DELETED, RebateSetting
from irhrs.payroll.utils.rule_validator import Equation


def args_validator(fxn_args: Sequence[str], equation_validator: Equation):
    errors = []

    if any(type(item) != str for item in fxn_args):
        errors.append('Function doesnt accept argument other than string')

    if not errors:
        rebate_type_choices = RebateSetting.objects.all().values_list('title', flat=True)
        for arg in fxn_args:
            if arg not in rebate_type_choices:
                errors.append(
                    'Argument must be among user voluntary rebate type choices')

    if len(fxn_args) != 1:
        errors.append('Function accepts exactly one argument')

    return errors


@register_plugin('user-voluntary-rebate', is_func=True, args_validator=args_validator)
def user_voluntary_rebate_fxn_plugin(calculator, package_heading):
    employee = calculator.employee
    to_date = calculator.to_date

    active_fiscal_year = FiscalYear.objects.active_for_date(
        organization=employee.detail.organization,
        date_=to_date,
        category="global"
    )
    fiscal_month = active_fiscal_year.fiscal_months.filter(
        start_at__lte=to_date, end_at__gte=to_date).first().display_name

    def get_user_voluntary_rebate(heading_names):
        queryset = employee.voluntary_rebates.filter(
            rebate__title=heading_names,
            fiscal_year=active_fiscal_year,
            statuses__action=CREATED
        ).exclude(statuses__action__in=[DELETED])
        total_amount = queryset.aggregate(rebate_amount=Sum('amount'))['rebate_amount'] or 0

        user_rebate = queryset.first()
        if user_rebate and user_rebate.rebate.duration_type == MONTHLY:
            fiscal_months_amount = getattr(user_rebate, 'fiscal_months_amount', {})
            total_amount = fiscal_months_amount.get(fiscal_month, 0)
        sources = list(UserVoluntaryRebate.objects.all().values(
            model_name=Value('UserVoluntaryRebate',
                             output_field=models.CharField()),
            instance_id=F('pk'),
            url=Value('', output_field=models.CharField())
        ))
        return total_amount, sources

    return get_user_voluntary_rebate
