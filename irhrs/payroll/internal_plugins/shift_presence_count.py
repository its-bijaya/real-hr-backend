from typing import Sequence

from django.db import models
from django.db.models import Value, F

from irhrs.attendance.models import TimeSheet, WorkShift
from irhrs.attendance.constants import WORKDAY
from irhrs.payroll.internal_plugins.registry import register_plugin
from irhrs.payroll.models import PackageHeading
from irhrs.payroll.utils.rule_validator import Equation


def args_validator(fxn_args: Sequence[str], equation_validator: Equation):
    errors = []

    if any(type(item) != str for item in fxn_args):
        errors.append('Function doesnt accept argument other than string')

    if len(fxn_args) != 1:
        errors.append('Function accepts exactly one argument')

    return errors


@register_plugin('shift-presence-count', is_func=True, args_validator=args_validator)
def shift_presence_count_fxn_plugin(calculator, package_heading):
    employee = calculator.employee
    to_date = calculator.to_date
    from_date = calculator.from_date
    include_holiday_offday = calculator.payroll_config.include_holiday_offday_in_calculation

    def get_shift_presence_count(shift_name):
        fil = dict(
            timesheet_for__gte=from_date,
            timesheet_for__lte=to_date,
            work_shift__name=shift_name,
            is_present=True
        )
        if not include_holiday_offday:
            fil.update({
                'coefficient': WORKDAY
            })

        presence_count_qs = employee.timesheets.filter(**fil)
        presence_count = presence_count_qs.count()
        total_amount = presence_count
        sources = list(presence_count_qs.values(
            model_name=Value('TimeSheet', output_field=models.CharField()),
            instance_id=F('pk'),
            url=Value('', output_field=models.CharField())
        ))
        return total_amount, sources

    return get_shift_presence_count
