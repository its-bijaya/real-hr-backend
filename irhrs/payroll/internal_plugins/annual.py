from functools import reduce
from irhrs.payroll.utils.rule_validator import Equation
from irhrs.payroll.utils.calculator_variable import CalculatorVariable
from django.db.models import Q

from .registry import register_plugin
from irhrs.payroll.models import (
    Heading, UserVoluntaryRebate
)

from typing import Sequence

from ..constants import MONTHLY
from ..utils.user_voluntary_rebate import get_annual_amount_from_rebate
from ...organization.models import FiscalYear


def iexact__in(field, name_list):
    q_list = map(lambda n: Q(**{f'{field}__iexact':n}), name_list)
    q_list = reduce(lambda a, b: a | b, q_list)
    return q_list


def args_validator(fxn_args: Sequence[str], equation_validator: Equation):
    errors = []

    if any(type(item) != str for item in fxn_args):
        errors.append('Function doesnt accept argument other than string')

    model = equation_validator.heading.__class__  # Either Header or PackageHeading

    query = None
    possible_dependents_query = dict()
    if model.__name__ == 'Heading':
        query = iexact__in('name', fxn_args)
        possible_dependents_query['organization'] = equation_validator.heading.organization
    elif model.__name__ == 'PackageHeading':
        query = iexact__in('heading__name', fxn_args)
        possible_dependents_query['package'] = equation_validator.heading.package

    argument_headings = model.objects.filter(
        query,
        **possible_dependents_query
    ).values_list('id', flat=True)

    if not errors:

        if len(fxn_args) != len(argument_headings):
            errors.append('Annual function: all arguments should be proper heading name')

    if not errors:
        possible_dependents = model.objects.filter(
            order__lt=equation_validator.heading.order,
            **possible_dependents_query
        ).values_list('id', flat=True)

        if not set(argument_headings).issubset(set(possible_dependents)):
            errors.append(
                'Annual function: heading arguments must be subset of possible dependent headings.'
            )

    if not errors:
        for arg in fxn_args:
            equation_validator.used_variables.add(
                CalculatorVariable.calculator_variable_name_from_heading_name(
                        arg
                    )
            )

    return errors


@register_plugin('annual-amount', is_func=True, args_validator=args_validator)
def annual_amount_fxn_plugin(calculator, package_heading):

    taxable_slot_in_fy = calculator.taxable_slot_in_fy
    organization = calculator.get_organization()
    employee = calculator.employee
    to_date = calculator.to_date

    def get_current_amount(heading):
        return calculator.payroll.get_heading_amount_from_heading(
            heading
        )

    def get_annual_amount(*heading_names):
        headings = Heading.objects.filter(
            iexact__in('name', heading_names),
            organization=organization
        )

        if calculator.calculate_annual_amount:
            # to stop recursion
            package_calculator = calculator.future_package_calculator
        else:
            package_calculator = None

        total_amount = 0

        for heading in headings:

            if heading.rules.rfind("__USER_VOLUNTARY_REBATE__") != -1:
                active_fiscal_year = FiscalYear.objects.active_for_date(
                    organization=employee.detail.organization,
                    date_=to_date,
                )
                total_amount += get_annual_amount_from_rebate(
                    employee, heading, calculator.payroll.package, organization, active_fiscal_year.id)
                continue
            total_amount += calculator.get_annual_amount_from_heading(
                employee=employee,
                heading=heading,
                taxable_slot=taxable_slot_in_fy,
                current_amount=get_current_amount(heading),
                future_package_salary_calculator=package_calculator,
            )

        return total_amount, []

    return get_annual_amount
