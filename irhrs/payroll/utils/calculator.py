"""This file contains utils needed to calculate payroll for an employee.

Calculator Workflow:
-------------------

    :func:`~EmployeeSalaryCalculator` Initializes Calculator

    :func:`~EmployeeSalaryCalculator.start_calculation`  Starts Calculation

        Then for each heading

            1) if heading is edited
                :func:`~EmployeeSalaryCalculator.set_edited_general_headings`

            2) if heading is Type1 or Type2 cnst

                * if Type2 cnst
                    :func:`~EmployeeSalaryCalculator.set_global_variables_for_type2cnst`

                :func:`~EmployeeSalaryCalculator.variable_heading_handler`

            3) if heading is `Addition`, `Deduction`, `Tax Deduction`
                :func:`~EmployeeSalaryCalculator.addition_and_deduction_heading_handler`

            4) if heading is `ExtraAddition` or `ExtraDeduction`
                :func:`~EmployeeSalaryCalculator.extra_addition_and_deduction_headings`

            * If replayment heading
                :func:`~EmployeeSalaryCalculator.set_repayment_heading`

    For further detail, view source code

Using Calculator:
----------------

    .. code-block:: python

        import datetime

        from django.contrib.auth import get_user_model
        from irhrs.organization.models import FY

        Employee = get_user_model()

        employee = Employee.objects.first()
        organization = employee.detail.organization

        datework =  FY(organization)

        from_date = datetime.date(2020, 01, 01)
        to_date = datetime.date(2020, 01, 31)

        package = employee.current_experience.user_experience_packages.first()

        salary_packages = [
            {
                "package": package,
                "from_date": package.active_from_date,
                "to_date": to_date,
                "applicable_from": package.active_from_date
            }
        ]

        appoint_date = employee.detail.joined_date
        dismiss_date = None # employee has not resigned
        PAYROLL_MONTH_DAYS_SETTING = 'ORGANIZATION_CALENDAR'



        calculation = EmployeeSalaryCalculator(
            employee=employee,
            datework=datework,
            from_date=from_date,
            to_date=to_date,
            salary_package=salary_packages,
            appoint_date=appoint_date,
            dismiss_date=dismiss_date,
            month_days_setting=PAYROLL_MONTH_DAYS_SETTING,
            package_assigned_date=salary_packages[0]["applicable_from"]
        )

        # now print the calculations
        for row in calculation.payroll.rows:
            print("Heading", row.heading.name", "amount", row.amount)

        # to store to the database
        calculation.payroll.record_to_model()



"""
import os
import sys
import importlib
import json
import logging
import functools

from typing import Dict, List, MutableMapping, Tuple, Union, Optional
from numbers import Number

from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from irhrs.attendance.models import TimeSheet
from irhrs.core.utils.datework import AbstractDatework
from irhrs.payroll.models.payroll import Package, Payroll, YearlyHeadingDetail
from irhrs.payroll.models.user_voluntary_rebate_requests import UserVoluntaryRebate
from irhrs.payroll.utils.helpers import get_variable_name

from irhrs.payroll.utils.unit_of_work import get_unit_of_work_done
from irhrs.payroll.utils.helpers import get_days_to_be_paid as gwd
from irhrs.attendance.utils.payroll import (
    get_working_days_from_organization_calendar as gwdfoc,
    get_hours_of_work as ghow, get_absent_days, get_work_days_count_from_simulated_timesheets,
    get_worked_days_for_daily_heading,
)
from irhrs.leave.utils.payroll import get_unpaid_leave_days

import regex
from datetime import date, timedelta
from django.db.transaction import atomic
from django.db.models import Sum, Max, Q
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError

from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import get_today, get_random_class_name

from irhrs.core.utils.common import get_today, get_random_class_name, DummyObject
from irhrs.leave.utils.payroll import get_unpaid_leave_days
from irhrs.organization.models import FY, FiscalYearMonth
from irhrs.payroll.models import (
    Employee,
    PayrollVariablePlugin,
    EmployeePayroll as EmployeePayrollModel,
    ReportRowRecord,
    UserExperiencePackageSlot, OrganizationPayrollConfig, ReportRowUserExperiencePackage,
    AdvanceSalarySetting, PackageHeading, Heading, cached_property, BackdatedCalculation)
from irhrs.payroll.models.advance_salary_request import AdvanceSalaryRepayment
from irhrs.payroll.utils.helpers import (
    # get_model_from_string,
    EmployeeConditionalVariableAdapter,
    EmployeeRuleVariableAdapter,
    merge_two_dicts,
    InvalidVariableTypeOperation,
    get_appoint_date, NoEmployeeConditionalVariableAdapter,
    NoEmployeeRuleVariableAdapter, get_heading_name_from_variable)

from irhrs.payroll.internal_plugins.registry import (
    REGISTERED_INTERNAL_CALCULATOR_PLUGIN_VARS,
    REGISTERED_INTERNAL_CALCULATOR_PLUGIN_FXNS
)

from irhrs.payroll.constants import FXN_CAPTURING_REGEX

# DesignationVariableAdapter,
# EmployeeAndDesignationCommonFieldAdapter
from irhrs.payroll.utils.user_voluntary_rebate import update_monthly_rebate_rows, \
    get_user_voluntary_rebate_from_heading

logger = logging.getLogger(__name__)
FuncitonNameType = str


def get_default_simulated_from() -> date:
    """Get default payroll simulated from

    This function is used to get default simulated from date in payroll
    generation. While generating future payroll, or past to future date range,
    (today-end date) will be simulated according to user's timesheet.

    This function was created to set hard coded simulated from date while
    debugging.


    :return: today's date in production
        and if `DEFBUG` is set to `True` and
        `DEFAULT_PAYROLL_SIMULATED_FROM` is set,
        then that value will be returned
    """
    if settings.DEBUG and getattr(settings, 'DEFAULT_PAYROLL_SIMULATED_FROM', None):
        return settings.DEFAULT_PAYROLL_SIMULATED_FROM
    return get_today()


class ReportRow(object):
    """Entity representing amount calculated for a heading.

    A ReportRow will be generated for each heading


    :param employee: Employee (User) instance
    :param from_date: Start date of payroll calculation whose output is amount
    :param to_date: End date of payroll calculation whose output is amount
    :param package_heading: **Deprecation Warning: use heading instead** Package heading instance
    :param heading: Heading instance
    :param amount: Amount calculated
    :param plugin_sources: list of sources (usually dict containing model_name and id) if payroll
    is generated using plugin

    """

    def __init__(self, **kwargs):
        self.employee = kwargs.get('employee')
        self.from_date = kwargs.get('from_date')
        self.to_date = kwargs.get('to_date')
        self.package_heading = kwargs.get('package_heading')
        self.heading = kwargs.get('heading') or self.package_heading.heading
        self.amount = round(kwargs.get('amount'), 2)
        self.plugin_sources = kwargs.get('plugin_sources', list())

    def __repr__(self):
        return f"Report Row {self.package_heading}: {self.amount}"


class EmployeePayroll(object):
    """Payroll of an Employee

    :param employee: Employee (User) whose payroll is being generated
    :param package: Package of the employee

    :ivar employee: Employee instance
    :ivar package: Package of the employee

    :ivar annual_gross_salary: Annual Gross Salary (Annual Taxable Payment )
        calculated during payroll
    :ivar rebate_amount: Rebate amount calculated
    :ivar annual_gross_salary_after_rebate: Annual Gross Salary - Rebate
    :ivar annual_tax: Calculated Annual tax to be paid
    :ivar paid_tax: Tax paid in this year
    :ivar tax_to_be_paid: Tax to be paid
    :ivar tax_condition: When multiple condition in tax heading, which condition
        caused fulfilled
    :ivar tax_rule: Using which rule(formula) tax was calculated
    :ivar tds_type: TDS type of rule used

    :ivar rows: collection of ReportRow calculated
    :ivar package_rows: collection of ReportRow but containing package(full)
        amount
    :ivar future_projected_rows: If payroll generated for future date, future
        rows
    :ivar backdated_calculations: If any backdated calculation is adjusted in
        this row

    """

    def __init__(self, employee, package):

        self.employee = employee
        # self.datework = datework
        self.package = package

        self.annual_gross_salary = 0.0
        self.rebate_amount = 0.0
        self.annual_gross_salary_after_rebate = 0.0
        self.annual_tax = 0.0
        self.paid_tax = 0.0
        self.tax_to_be_paid = 0.0

        self.tax_condition = ''
        self.tax_rule = ''
        self.tds_type = ''

        self.rows = list()
        self.package_rows = list()
        self.future_projected_rows = list()

        # this value will be QuerySet of backdated calculations
        # will be set while adjusting backdated calculation
        self.backdated_calculations = None

    def get_heading_amount(self, package_heading: PackageHeading) -> Number:
        """Get heading amount from PackageHeading instance

        :param package_heading: PackageHeading instance whose amount is required

        :return: amount of that heading in `self.rows`
        """
        filterd_rows = list(
            filter(
                lambda x: x.heading == package_heading.heading,
                self.rows
            )
        )

        return filterd_rows[0].amount if filterd_rows else 0

    def get_heading_amount_from_heading(self, heading: Heading) -> Number:
        """get heading amount from Heading instance

        :param heading: Heading instance

        :return: amount of that heading in `self.rows`
        """
        filterd_rows = list(
            filter(
                lambda x: x.heading == heading,
                self.rows
            )
        )

        return filterd_rows[0].amount if filterd_rows else 0

    def get_plugin_sources_from_heading(self, heading: Heading) -> list:
        """
        :param heading: Heading instance

        :return: list of plugin sources for that heading1`
        """
        filterd_rows = list(
            filter(
                lambda x: x.heading == heading,
                self.rows
            )
        )

        return filterd_rows[0].plugin_sources if filterd_rows else []

    def add_future_projected_rows(self, projected_rows) -> None:
        """setter for projected rows"""
        self.future_projected_rows = projected_rows

    def get_projected_amount_from_heading(self, heading: Heading) -> Number:
        """get projected amount for given heading

        :param heading: heading instance

        :return: Projected amount if projected else 0
        """
        filterd_rows = list(
            filter(
                lambda x: x.heading == heading and heading.duration_unit in [
                    'Monthly',
                    'Yearly'
                ],
                self.future_projected_rows
            )
        )

        return filterd_rows[0].amount if filterd_rows else 0

    def get_heading_amount_from_variable(self, heading_variable: str) -> Number:
        """get heading amount from heading variable

        :param heading_variable: Heading variable eg. `BASIC_SALARY`

        :return: total amount of heading
        """
        heading_name = get_heading_name_from_variable(heading_variable)
        filterd_rows = list(
            filter(
                lambda x: x.package_heading.heading.name.upper() == heading_name,
                self.rows
            )
        )

        return filterd_rows[0].amount if filterd_rows else 0

    def get_package_heading_amount(self, heading: Heading) -> Number:
        """Get package amount for that heading

        :param heading: Heading instance

        :return: Actual amount defined in package for that heading
        """
        filterd_rows = list(
            filter(
                lambda x: x.heading == heading,
                self.package_rows
            )
        )

        return filterd_rows[0].amount if filterd_rows else 0

    def add_or_update_row(self, row: ReportRow) -> ReportRow:
        """Add row.amount to payroll

        If row already exists, adds to previous amount else creates new row

        :param row: new ReportRow instance

        :return: Updated ReportRow
        """
        for r in self.rows:
            if row.heading.id == r.heading.id:
                r.amount += row.amount
                r.to_date = row.to_date
                return r
        self.rows.append(row)
        return row

    def update_row(self, row: ReportRow) -> ReportRow:
        """Update amount of existing row

        Unlike add_or_update row, it replaces previous amount if exists

        :param row: new ReportRow instance

        :return: Updated ReportRow
        """
        try:
            r = next(
                filter(lambda _r: row.heading.id ==
                       _r.heading.id, self.rows)
            )
            r.amount = row.amount
            r.to_date = row.to_date
            return r
        except StopIteration:
            return self.add_or_update_row(row)

    def record_to_model(
        self,
        payroll: Payroll,
        instance: Optional[EmployeePayrollModel] = None
    ) -> EmployeePayrollModel:
        """Save payroll to database

        :param payroll: Payroll instance
        :param instance: Employee payroll instance in case of update

        :return: EmployeePayroll (Model) instance recorded to database
        """
        with atomic():
            if instance:

                # In case of update
                employee_payroll = instance

                employee_payroll.annual_gross_salary = self.annual_gross_salary
                employee_payroll.annual_tax = self.annual_tax
                employee_payroll.paid_tax = self.paid_tax
                employee_payroll.tax_to_be_paid = self.tax_to_be_paid
                employee_payroll.tax_rule = self.tax_rule
                employee_payroll.tax_condition = self.tax_condition
                employee_payroll.tds_type = self.tds_type

                employee_payroll.save()

                # delete old records to create new ones later
                employee_payroll.report_rows.all().delete()

            else:
                employee_payroll = EmployeePayrollModel.objects.create(
                    employee=self.employee,
                    payroll=payroll,
                    package=self.package,
                    annual_gross_salary=self.annual_gross_salary,
                    rebate_amount=self.rebate_amount,
                    annual_gross_salary_after_rebate=self.annual_gross_salary_after_rebate,
                    annual_tax=self.annual_tax,
                    paid_tax=self.paid_tax,
                    tax_to_be_paid=self.tax_to_be_paid,
                    tax_rule=self.tax_rule,
                    tax_condition=self.tax_condition,
                    tds_type=self.tds_type
                )

            ReportRowRecord.objects.bulk_create(
                [
                    ReportRowRecord(
                        employee_payroll=employee_payroll,
                        from_date=row.from_date,
                        to_date=row.to_date,
                        heading=row.heading,
                        amount=row.amount,
                        projected_amount=self.get_projected_amount_from_heading(
                            row.heading
                        ),
                        package_amount=self.get_package_heading_amount(
                            row.heading),
                        plugin_sources=self.get_plugin_sources_from_heading(
                            row.heading
                        )
                    )
                    for row in self.rows
                ]
            )

            if self.backdated_calculations:
                self.backdated_calculations.update(
                    adjusted_payroll=employee_payroll)

            return employee_payroll


class EmployeeSalaryCalculator(object):
    """Util to calculate employee salary

    :param employee: Employee whose salary is being calculated
    :param datework: Fiscal Year (:class:`irhrs.organization.models.fiscal_year.FY`)
         instance or implementing :class:`irhrs.core.utils.datework.AbstractDatework`
    :param from_date: Payroll start date
    :param to_date: Payroll end date
    :param salary_package: :class:`irhrs.payroll.models.payroll.Package` instance
        representing payroll package,
        or
        a list containing dictionary of `package`, `from_date`, `to_date`
        and `applicable_from` in case of multiple packages for example::

            [
                {
                    "package": <irhrs.payroll.models.payroll.Package>,
                    "from_date": <datetime.date 2020-01-01>,
                    "to_date": <datetime.date 2020-01-31>,
                    "applicable_from": <datetime.date 2020-01-01>
                }, ...
            ]

    :param appoint_date: Employee appointed date / joined_date / experience
        start date
    :param dismiss_date: Employee's dismiss date / last worked date
    :param calculate_tax: When True(default), Tax Deduction heading will be
        calculated, otherwise tax deduction heading amount will be 0
    :param initial_extra_headings: Extra Addition/Deduction headings to
        calculate amount initially.
        Normally, Extra Headings will have amount 0, and you have to edit to
        set new value. With this input heading amount will be calculated from
        formula set in heading. Eg:  [<Heading Festival Allowance>, ...]
    :param extra_headings: Update details of extra headings. If amount is
        assigned/updated, new amount should be assigned to heading id
        Suppose heading of id 1 is updated to 2000 then,
        `['1': {'value': 2000 }]`

    :param edited_general_headings_difference_except_tax_heading:
        *Deprecated [Not used]* Income difference due to payroll edit
    :param edited_general_headings: Dictionary of edited heading values
        Suppose heading id 1 is updated from 1000 to 2000, then::

           {
               "1": {
                   "initialValue": "1000",
                   "currentValue": "2000",
                   "type": "Addition"
               },
           }
    :param month_days_setting: Setting representing calculation of days in month
        Values can be `ORGANIZATION_CALENDAR` [default] where values will be
        fetched from fiscal year.
        Or Fixed number like `30` for static month days.
    :param simulated_from: Date to start payroll simulation from. Defaults to
        today
    :param package_assigned_date: Package assigned date to the employee
        In case of multiple packages, will be fetched from salary_package arg
    :param calculate_yearly: Boolean Value if set to True [default] will
        calculate yearly headings, otherwise those headings
        will have Zero amount
    :param calculate_annual_amount: When True [default] will calculate
        annual amount of heading using `annual-amount` function, otherwise it
        won't calculate value



    """
    employee_conditional_variable_adapter_class = EmployeeConditionalVariableAdapter
    employee_rule_variable_adapter_class = EmployeeRuleVariableAdapter
    calculate_package_amount = True

    calculate_backdated_payroll = True

    def __init__(
        self,
        employee: Employee,
        datework: AbstractDatework,
        from_date: date,
        to_date: date,
        salary_package: Union[List[dict], Package],
        appoint_date: date,
        dismiss_date: Optional[date] = None,
        calculate_tax: Optional[bool] = True,

        initial_extra_headings: Optional[List[Heading]] = None,
        extra_headings: Optional[dict] = None,

        # not used anywhere
        edited_general_headings_difference_except_tax_heading: Optional[Number] = 0,
        edited_general_headings: Optional[dict] = None,

        # is one of ['DATE_CALENDAR', 'ORGANIZATION_CALENDAR', FIXED_NUMBER like 28, 30]
        month_days_setting: Optional[Union[str, int]] =
        'ORGANIZATION_CALENDAR',
        simulated_from: Optional[date] = None,
        package_assigned_date: Optional[date] = None,
        calculate_yearly: Optional[bool] = True,
        calculate_annual_amount: Optional[bool] = True,
        **kwargs
        # all extra kwargs that we need to pass during recursion or others
        # will be set to  self.init_kwargs
    ) -> None:

        # lru cache setup
        self._get_working_days = functools.lru_cache(self._get_working_days)
        self._get_worked_days = functools.lru_cache(self._get_worked_days)

        self.get_internal_fxns_plugin_locals = functools.lru_cache(
            self.get_internal_fxns_plugin_locals)

        self.get_conditional_variable_adapter = functools.lru_cache(
            self.get_conditional_variable_adapter)
        self.get_rule_variable_adapter = functools.lru_cache(
            self.get_rule_variable_adapter)

        # since we have multiple packages for calculating payroll,
        # so @cached property won't work
        # below are variables to store values and settings for cached property

        self.__package_salary_calculator = None
        self.__package_salary_from_date = None
        self.__package_salary_to_date = None
        self.__package_salary_package = None

        self.__ags = None
        self.__ags_package = None
        self.__ags_from_date = None
        self.__ags_to_date = None

        self.__taxable_slots_in_fy = None
        self.__taxable_slots_in_fy_from_date = None
        self.__taxable_slots_in_fy_to_date = None

        self.__remaining_slots_count = None
        self.__remaining_slots_count_from_date = None
        self.__remaining_slots_count_to_date = None

        # -- end --

        # if editing payroll save instance if payroll being edited
        self.employee_payroll = kwargs.get('employee_payroll')

        # package assigned date is used in calculating payroll increments after package assigned
        # if None is passed default today is taken and payroll increments are not considered

        self.init_kwargs = kwargs
        self.package_assigned_date = package_assigned_date or get_today()

        if extra_headings is None:
            extra_headings = {}
        if edited_general_headings is None:
            edited_general_headings = {}

        self.calculate_tax = calculate_tax
        self.calculate_yearly = calculate_yearly

        #  no use found here but is accessed by plugins
        self.calculate_annual_amount = calculate_annual_amount

        self.employee = employee
        self.datework = datework

        # if appoint date is after from_date
        if appoint_date and from_date < appoint_date:
            self.from_date = appoint_date
        else:
            self.from_date = from_date

        # if dismiss_date is before to_date
        if dismiss_date and dismiss_date < to_date:
            self.to_date = dismiss_date
        else:
            self.to_date = to_date

        self._actual_from_date = self.from_date
        self._actual_to_date = self.to_date

        # support to calculate payroll by multiple package added
        # so multiple salary packages  is stored
        self.salary_packages = self._parse_salary_package(salary_package)
        # placeholder for currently processing salary_package
        # used by existing utils
        self.salary_package = None

        self.appoint_date = appoint_date
        self.dismiss_date = dismiss_date

        # To calculate extra heading default value initially
        self.initial_extra_headings = initial_extra_headings or []

        self.extra_headings = extra_headings

        self.edited_general_headings = edited_general_headings
        self.edited_general_headings_difference_except_tax_heading = \
            edited_general_headings_difference_except_tax_heading

        self.month_days_setting = month_days_setting

        self.ADJUST_TAX_CHANGE_DUE_TO_EXTRA_ADDITION_DEDUCTION_IN_SAME_MONTH = getattr(
            settings,
            'ADJUST_TAX_CHANGE_DUE_TO_EXTRA_ADDITION_DEDUCTION_IN_SAME_MONTH',
            False
        )

        # instantiate employee payroll
        self.payroll = EmployeePayroll(
            self.employee, self.salary_packages[0]["package"])

        simulated_from = simulated_from or get_default_simulated_from()
        self.simulated_from = simulated_from if simulated_from <= to_date else None
        self.latest_tax_package_heading = None

        self.employee_global_variables = {}
        self.settled_repayment = None
        self.update_remaining_rebate_row = kwargs.get('update_remaining_rebate_row', False)

        # set variables from adaptors and payroll start and end dates
        self.get_easy_global_variables()

        # add backdated calculation to rows
        self.adjust_backdated_calculation(
            self.get_backdated_calculations(), self.payroll, self.from_date, self.to_date
        )

        self.start_calculation()

        # placeholder to keep which heading is being processed
        self.__processing_heading = None

        if self.calculate_package_amount:
            user_experience = employee.first_date_range_user_experiences(
                from_date,
                to_date
            )
            package_calculator = PackageSalaryCalculator(
                user_experience=user_experience,
                employee=employee,
                datework=datework,
                from_date=from_date,
                to_date=to_date,
                salary_package=salary_package,
                appoint_date=appoint_date,
                month_days_setting=month_days_setting,
                package_assigned_date=package_assigned_date,
                use_slot_days=True
            )
            self.payroll.package_rows = package_calculator.payroll.rows

        # -- clear cache, as we don't need them after calculation is complete --
        # This will early release of memory referenced with cached_property
        # instances of [adapters, plugins, etc.] immediately after calculation
        # is complete but calculator instance can still be referenced
        self.get_conditional_variable_adapter.cache_clear()
        self.get_rule_variable_adapter.cache_clear()
        self.get_internal_fxns_plugin_locals.cache_clear()
        self._get_working_days.cache_clear()
        self._get_worked_days.cache_clear()

    def get_conditional_variable_adapter(self, *args, **kwargs):
        return self.employee_conditional_variable_adapter_class(*args, **kwargs)

    def get_rule_variable_adapter(self, *args, **kwargs):
        return self.employee_rule_variable_adapter_class(*args, **kwargs)

    @staticmethod
    def get_clean_salary_packages(packages, actual_from_date, actual_to_date):
        clean_salary_packages = []
        for index, package in enumerate(packages):
            _package = package["package"]
            from_date = max(package["from_date"], actual_from_date)
            to_date = min(package["to_date"], actual_to_date)
            applicable_from = package["applicable_from"]
            if index == 0:
                clean_salary_packages.append({
                    "package": _package,
                    "from_date": from_date,
                    "to_date": to_date,
                    "applicable_from": applicable_from
                })
                continue
            if package["package"] == packages[index-1]["package"]:
                clean_salary_packages[-1]["to_date"] = to_date
            else:
                clean_salary_packages.append({
                    "package": _package,
                    "from_date": from_date,
                    "to_date": to_date,
                    "applicable_from": applicable_from
                })
        return clean_salary_packages

    def _parse_salary_package(self, package):
        """
        Parse salary package input to required format
            [
                {
                    "package": Package,
                    "from_date": date,
                    "to_date": date
                }
            ]

        """
        if not isinstance(package, list):
            return [{
                "package": package,
                "from_date": self._actual_from_date,
                "to_date": self._actual_to_date,
                "applicable_from": self.package_assigned_date
            }]
        else:
            return self.get_clean_salary_packages(
                package, self._actual_from_date, self._actual_to_date)

    @property
    def package_headings(self):
        return self.salary_package.package_headings.all(
        ).exclude(
            id=self.default_advance_salary_package_deduction_heading.id
        ).select_related('heading').order_by(
            'order'
        )

    @cached_property
    def payroll_config(self):
        return OrganizationPayrollConfig.objects.get(
            organization=self.get_organization()
        )

    @cached_property
    def previous_payroll(self):
        """
        Last generated payroll of self.employee
        """
        return EmployeePayrollModel.objects.filter(
            employee=self.employee,
            payroll__to_date__lte=self.from_date,
            payroll__status="Confirmed"
        ).order_by(
            '-payroll__to_date'
        ).first()

    @property
    def adjust_previous_payroll_from(self):
        # only send adjust status for first user expereience package slot
        if self.from_date == self._actual_from_date:
            return nested_getattr(self.previous_payroll, 'payroll.simulated_from', default=None)
        return None

    def set_heading_variable(self, heading_obj, amount, *suffixes):
        var_name = '_'.join(heading_obj.name.upper().split(' '))
        suffix = ''.join(suffixes)
        var_name += suffix
        self.employee_global_variables['__' + var_name + '__'] = amount

    def get_adapter_kwargs(self):
        return dict(
            instance=self.employee,
            payroll_from_date=self.from_date,
            payroll_to_date=self.to_date,
            package_assigned_date=self.package_assigned_date
        )

    def get_easy_global_variables(self):
        """
        sets employee variables using adapters (conditional and rule)
        starting from EMPLOYEE_ and __PAYMENT_DATE_FROM__ and __PAYMENT_DATE_TO__
        """

        employee_conditional_variable_adapter = self.get_conditional_variable_adapter(
            'EMPLOYEE_',
            **self.get_adapter_kwargs()
        )

        employee_rule_variable_adapter = self.get_rule_variable_adapter(
            'EMPLOYEE_',
            **self.get_adapter_kwargs()
        )

        self.employee_global_variables = merge_two_dicts(
            self.employee_global_variables,
            employee_conditional_variable_adapter.generate()
        )

        self.employee_global_variables = merge_two_dicts(
            self.employee_global_variables,
            employee_rule_variable_adapter.generate()
        )

        self.employee_global_variables['__PAYMENT_DATE_FROM__'] = self.from_date
        self.employee_global_variables['__PAYMENT_DATE_TO__'] = self.to_date

    def set_global_var__slot_variables(self, slot):
        # self.employee_global_variables['__EMPLOYEE_WORKED_YEARS__'] = slot.get(
        #     'worked_years')
        # self.employee_global_variables['__SLOT_START_DATE__'] = slot.get(
        #     'start')
        # self.employee_global_variables['__SLOT_END_DATE__'] = slot.get('end')
        # self.employee_global_variables['__SLOT_WORKING_DAYS__'] = self.get_working_days(slot)[
        #     0]
        # self.employee_global_variables['__SLOT_WORKING_MONTH_DAYS__'] = self.get_worked_days(slot)
        # [1]
        # self.employee_global_variables['__SLOT_WORKED_DAYS_COUNT__'] = self.get_worked_days(slot)[
        #     0]
        # self.employee_global_variables['__SLOT_MONTH_DAYS__'] = slot.get(
        #     'month_days')

        self.employee_global_variables['__SLOT_DAYS_COUNT__'] = slot.get(
            'days_count')
        self.employee_global_variables[
            '__REMAINING_DAYS_IN_FY'] = self.get_remaining_working_days_in_fy(
            self.taxable_slot_in_fy, slot.get('start')
        )
        self.employee_global_variables[
            '__REMAINING_MONTHS_IN_FY__'] = self.get_remaining_months_in_fy(
            slot.get('end')
        )

    def set_global_variables_for_type2cnst(self):
        self.employee_global_variables['__SLOT_DAYS_COUNT__'] = (
            self.to_date - self.from_date).days + 1

        # this is including current slot
        self.employee_global_variables['__REMAINING_DAYS_IN_FY__'] = \
            self.get_remaining_working_days_in_fy(self.taxable_slot_in_fy)

        self.employee_global_variables['__REMAINING_MONTHS_IN_FY__'] = \
            self.get_remaining_months_in_fy()

    def set_global_var__fiscal_year_data(self, fy_data):
        self.employee_global_variables['__CURRENT_FISCAL_YEAR_START_DATE__'] = \
            fy_data.get('fy_slot')[
            0]
        self.employee_global_variables['__CURRENT_FISCAL_YEAR_END_DATE__'] = \
            fy_data.get('fy_slot')[
            1]
        self.employee_global_variables['__CURRENT_FISCAL_YEAR_FROM_DATE__'] = fy_data.get(
            'date_range')[0]
        self.employee_global_variables['__CURRENT_FISCAL_YEAR_TO_DATE__'] = fy_data.get(
            'date_range')[1]

    def set_global_var__annual_gross_salary(self, amount):
        self.employee_global_variables['__ANNUAL_GROSS_SALARY__'] = amount

    def get_global_var__annual_gross_salary(self):
        return self.employee_global_variables.get('__ANNUAL_GROSS_SALARY__', None)

    def set_repayment_heading(self, package_heading, repayment=None):
        # If user has selected CIH in Advance Salary Setting.
        # Reduce the repayment Value from CIH
        # Set `auto_generated_adv_salary_deduction_heading` value equal to
        # repayment
        if not repayment:
            return
        amount = repayment.amount if repayment else 0.0
        default_advance_salary_heading = self.default_advance_salary_package_deduction_heading
        # Repayment will be done in two phases:

        # Phase I - Update package_heading as package_heading - repayment_amount

        # Phase II - Set default_advance_salary_heading amount.

        # Phase I Begin

        old_amt = self.get_advance_salary_heading_amount(package_heading)
        updated_amount_for_advance_salary_selected_heading = old_amt - amount
        row = self.payroll.update_row(
            ReportRow(
                from_date=self.from_date,
                to_date=self.to_date,
                employee=self.employee,
                package_heading=package_heading,
                amount=updated_amount_for_advance_salary_selected_heading
            )
        )
        self.set_heading_variable(
            package_heading.heading,
            row.amount
        )
        # Phase I End && Phase II Begin
        row = self.payroll.add_or_update_row(
            ReportRow(
                from_date=self.from_date,
                to_date=self.to_date,
                employee=self.employee,
                package_heading=default_advance_salary_heading,
                amount=amount
            )
        )
        self.set_heading_variable(
            default_advance_salary_heading.heading,
            row.amount
        )
        # Phase II End
        self.settled_repayment = repayment

    def get_advance_salary_heading_amount(self, package_heading):
        old_amt = self.payroll.get_heading_amount(package_heading)
        return old_amt

    def start_calculation(self):
        """Start Payroll Calculation"""
        for salary_package_detail in self.salary_packages:

            self.salary_package = salary_package_detail["package"]
            self.from_date = salary_package_detail["from_date"]
            self.to_date = salary_package_detail["to_date"]
            self.package_assigned_date = salary_package_detail["applicable_from"]

            latest_tax_package_heading = self.salary_package.package_headings.filter(
                type='Tax Deduction'
            )
            self.latest_tax_package_heading = latest_tax_package_heading.latest(
                '-order') if latest_tax_package_heading else None

            advance_salary_deduction_heading = self.get_advance_salary_deduction_heading()

            for package_heading in self.package_headings:
                # if user has edited of generated payroll

                not_tax_heading = package_heading.type != 'Tax Deduction'
                if not_tax_heading and (
                    str(package_heading.heading.id) in self.edited_general_headings.keys()
                ):
                    # Exclude tax deduction here as it predicts future metrices
                    # override it when it is being recorded in payroll

                    self.set_edited_general_headings(package_heading)
                    continue

                if package_heading.heading.type in ['Type1Cnst', 'Type2Cnst']:
                    if package_heading.heading.type == 'Type2Cnst':
                        self.set_global_variables_for_type2cnst()

                    self.variable_heading_handler(package_heading)

                elif package_heading.heading.type in [
                    'Addition',
                    'Deduction',
                    'Tax Deduction'
                ]:
                    self.addition_and_deduction_heading_handler(
                        package_heading)
                elif package_heading.heading.type in [
                    'Extra Addition',
                    'Extra Deduction'
                ]:
                    self.extra_addition_and_deduction_headings(package_heading)

                if package_heading.heading == advance_salary_deduction_heading:
                    repayment = AdvanceSalaryRepayment.objects.filter(
                        request__employee=self.employee, paid=False,
                        request__payslip_generation_date__lte=self.to_date
                    ).order_by('request__payslip_generation_date', 'order').first()
                    self.set_repayment_heading(package_heading, repayment)

    def get_advance_salary_deduction_heading(self):
        advance_salary_settings = AdvanceSalarySetting.objects.filter(
            organization=self.get_organization()).first()
        advance_salary_deduction_heading = getattr(
            advance_salary_settings, 'deduction_heading', None)
        return advance_salary_deduction_heading

    def get_backdated_calculations(self):
        """
        returns: Calculations which are not adjusted
        """
        if self.calculate_backdated_payroll:
            return BackdatedCalculation.objects.filter(
                package_slot__user_experience__user=self.employee
            ).filter(
                Q(adjusted_payroll__isnull=True) | Q(
                    adjusted_payroll=self.employee_payroll)
            )
        return BackdatedCalculation.objects.none()

    @staticmethod
    def adjust_backdated_calculation(backdated_calculations, payroll, from_date, to_date):

        for backdated_calculation in backdated_calculations:
            current_amount = payroll.get_heading_amount_from_heading(
                backdated_calculation.heading
            )

            current_plugin_sources = payroll.get_plugin_sources_from_heading(
                backdated_calculation.heading
            )
            row = ReportRow(
                from_date=from_date,
                to_date=to_date,
                employee=payroll.employee,
                heading=backdated_calculation.heading,
                amount=current_amount + backdated_calculation.difference,
                plugin_sources=current_plugin_sources
            )
            payroll.update_row(row)
        payroll.backdated_calculations = backdated_calculations

    def variable_heading_handler(self, package_heading):
        if (
            self.calculate_tax) or (not self.latest_tax_package_heading) or (
            self.latest_tax_package_heading and
            package_heading.order < self.latest_tax_package_heading.order
        ):
            r_amount, sources = self.unit_amount(
                package_heading, return_sources=True)
            report_row = ReportRow(
                from_date=self.from_date,
                to_date=self.to_date,
                employee=self.employee,
                package_heading=package_heading,
                amount=r_amount,
                plugin_sources=sources
            )

            if package_heading.heading.type in ['Type1Cnst', 'Type2Cnst']:
                # for constants override by final value
                row = self.payroll.update_row(report_row)
            else:
                row = self.payroll.add_or_update_row(report_row)

            self.set_heading_variable(
                package_heading.heading,
                row.amount
            )

    def addition_and_deduction_heading_handler(self, package_heading):
        if package_heading.heading.type in ['Tax Deduction'] and self.calculate_tax:
            self.tax_deduction_handler(package_heading)
        elif package_heading.type in ['Addition', 'Deduction']:
            self.addition_and_deduction_heading_excluding_tax_deduction_handler(
                package_heading
            )

    def addition_and_deduction_heading_excluding_tax_deduction_handler(self, package_heading):
        if (
            self.calculate_tax) or (not self.latest_tax_package_heading) or (
            self.latest_tax_package_heading and
            package_heading.order < self.latest_tax_package_heading.order
        ):
            logger.debug(f"procesing heading ----> {package_heading.heading}")

            for index, slot in enumerate(self.get_slots()):

                # In the first slot, append adjustment information from previous
                # payroll, so that any changes that occurred in simulated days
                # can be adjusted in this payroll
                if index == 0:
                    slot.update({
                        'adjust_payroll_from': self.adjust_previous_payroll_from
                    })

                # set slot specific variables
                self.set_global_var__slot_variables(slot)

                row = None

                amount, sources = 0, []

                if package_heading.duration_unit == 'Yearly':
                    logger.debug("Yearly package" + str(package_heading))
                    yearly_heading_detail = package_heading.heading.yearly_heading_details.all()
                    if yearly_heading_detail.filter(
                        date__isnull=True
                    ).exists():
                        # if pre_tax_setting has no date, temporarily we set date to fiscal year
                        # end, after calculating the __ags__ we again set date to None
                        yearly_heading_detail_with_no_date = yearly_heading_detail.first()
                        yearly_heading_detail_with_no_date.date = \
                            yearly_heading_detail_with_no_date.fiscal_year.end_at
                        yearly_heading_detail_with_no_date.save()
                        cache.set(
                            'yearly_heading_detail_id', yearly_heading_detail_with_no_date.id)

                    package_heading_fiscal_year_details = yearly_heading_detail.filter(
                            date__lte=slot.get('end'),
                            date__gte=slot.get('start')
                        )
                    logger.debug("Yearly package" +
                                 str(package_heading_fiscal_year_details))

                    if (
                            package_heading_fiscal_year_details
                    ) and (
                            slot.get('start') <=
                            package_heading_fiscal_year_details[0].date <= slot.get(
                                'end')
                    ):

                        if self.calculate_yearly:
                            # changed to_date so that employee with yos < 1 year doesn't get full
                            # payroll amount
                            temp_date = self.to_date
                            self.to_date = package_heading_fiscal_year_details[0].date
                            amount, sources = self.unit_amount(
                                package_heading,
                                return_sources=True
                            )
                            self.to_date = temp_date

                        print("recording row" + str(row))

                    yearly_heading_detail_id = cache.get('yearly_heading_detail_id', None)
                    # revert date to None, once the __ags__ is calculated for pre_tax_setting
                    # having no data
                    if yearly_heading_detail_id:
                        yd = YearlyHeadingDetail.objects.get(id=yearly_heading_detail_id)
                        yd.date = None
                        yd.save()

                else:

                    amount, sources = self.calculate_addition_and_deduction_type_heading(
                        package_heading,
                        slot
                    )

                row = ReportRow(
                    from_date=slot.get('start'),
                    to_date=slot.get('end'),
                    employee=self.employee,
                    package_heading=package_heading,
                    amount=amount,
                    plugin_sources=sources
                )
                updated_row = self.payroll.add_or_update_row(row)
                if self.calculate_package_amount and package_heading.heading.rules.rfind(
                    "__USER_VOLUNTARY_REBATE__"
                ) != -1:
                    updated_row.amount = row.amount
                self.set_heading_variable(
                    package_heading.heading,
                    updated_row.amount
                )

    def extra_addition_and_deduction_headings(self, package_heading):
        amount, sources = 0, []
        try:

            if package_heading.heading in self.initial_extra_headings:
                amount, sources = self.unit_amount(
                    package_heading,
                    return_sources=True
                )

            elif str(package_heading.heading.id) in self.extra_headings:
                amount = float(
                    self.extra_headings[
                        str(package_heading.heading.id)
                    ].get('value', 0))
        except ValueError:
            raise ValidationError(
                {"non_field_errors": [f"Invalid value for heading {str(package_heading)}"]})

        row = self.payroll.update_row(
            ReportRow(
                from_date=self.from_date,
                to_date=self.to_date,
                employee=self.employee,
                package_heading=package_heading,
                amount=amount,
                plugin_sources=sources
            )
        )

        self.set_heading_variable(
            package_heading.heading,
            row.amount
        )

    def set_edited_general_headings(self, package_heading):
        try:
            amount = float(
                self.edited_general_headings[
                    str(package_heading.heading.id)
                ].get('currentValue')
            )
        except ValueError:
            raise ValidationError(
                {"non_field_errors": [f"Invalid value for heading {str(package_heading)}"]})

        row = self.payroll.update_row(
            ReportRow(
                from_date=self.from_date,
                to_date=self.to_date,
                employee=self.employee,
                package_heading=package_heading,
                amount=amount
            )
        )
        self.set_heading_variable(
            package_heading.heading,
            row.amount
        )

    def get_unit_of_work_amount(self, slot):
        return get_unit_of_work_done(self.employee, slot)

    def calculate_addition_and_deduction_type_heading(self, package_heading, slot):
        _, month_days = self.get_working_days(slot)

        # # Below if condition is executed when particular heading general calculation value is
        #  edited Ratio because there can be many slots and edition is for over all
        # if str(package_heading_obj.heading.id) in self.edited_general_headings.keys():
        #     return (
        #         int(
        #             self.edited_general_headings[str(
        #                 package_heading_obj.heading.id)].get('currentValue')
        #         ) /
        #         (
        #             self.get_range_working_days(
        #                 self.from_date, self.to_date)
        #         )
        #     ) * self.get_working_days(slot)[0]

        # One shot edited heading

        duration_unit = package_heading.duration_unit

        if duration_unit == 'Hourly':

            h_unit_amount, sources = self.unit_amount(
                package_heading,
                return_sources=True
            )
            return (self.get_hours_of_work(slot, package_heading) * h_unit_amount), sources
        elif duration_unit == 'Daily':
            worked_days = self.get_worked_days_for_daily_heading(
                slot,
                package_heading,
                deduct_amount_on_leave=package_heading.deduct_amount_on_leave,
                pay_when_present_holiday_offday=package_heading.pay_when_present_holiday_offday,
                deduct_amount_on_remote_work=package_heading.deduct_amount_on_remote_work,
            )
            d_unit_amount, sources = self.unit_amount(
                package_heading,
                return_sources=True
            )
            return (worked_days * d_unit_amount), sources

        elif duration_unit == 'Weekly':
            return 0, []
        elif duration_unit == 'Monthly':
            worked_days = self.get_worked_days(slot, package_heading)[0]

            m_unit_amount, sources = self.unit_amount(
                package_heading,
                return_sources=True
            )

            user_rebate = get_user_voluntary_rebate_from_heading(
                    self.employee, package_heading, self.get_organization(), to_date=self.to_date
                )

            if user_rebate:
                return m_unit_amount, sources

            # Division by 0 error fix
            if worked_days == 0:
                return 0, []
            return (
                (m_unit_amount * (
                    worked_days)) / month_days
            ), sources
        elif duration_unit == 'Yearly':
            # Already handled by a callee function
            return 0, []
        elif duration_unit == 'Unit Of Work':
            return self.get_unit_of_work_amount(slot), []

    def update_variables_before_execution(self, expression):

        # set value of ags variable if not set but used.
        ags_var_name = "__ANNUAL_GROSS_SALARY__"
        if ags_var_name in expression:
            if self.calculate_tax:
                self.set_global_var__annual_gross_salary(
                    self.annual_gross_salary)
            else:
                self.set_global_var__annual_gross_salary(0)

        ytd_var = "__YTD__"
        if ytd_var in expression and self.__processing_heading:
            self.employee_global_variables[ytd_var] = \
                self.get_paid_amount_in_date_range_from_heading(
                    heading=self.__processing_heading,
                    employee=self.employee,
                    from_date=self.taxable_slot_in_fy[0],
                    to_date=self.taxable_slot_in_fy[1],
                    paid_this_time=self.payroll.get_heading_amount_from_heading(
                        self.__processing_heading
                    )
            )

    def get_internal_vars_plugin_locals(self, expression, package_heading):
        plugin_locals = dict()
        sources = list()
        plugin_variables_mapping = REGISTERED_INTERNAL_CALCULATOR_PLUGIN_VARS

        rgx = '|'.join(plugin_variables_mapping.keys())

        used_plugin_variables = set(
            regex.findall(rgx, expression)
        )

        if not rgx:
            used_plugin_variables = []

        for used_plugin_variable in list(used_plugin_variables):

            plugin_locals[used_plugin_variable], source = plugin_variables_mapping[
                used_plugin_variable](
                self,
                package_heading
            )

            sources.append(
                {
                    'used_variable_name': used_plugin_variable,
                    'type': 'internal plugin',
                    'value': plugin_locals[used_plugin_variable],
                    'source': source,
                }
            )

        return plugin_locals, sources

    def get_internal_fxns_plugin_locals(self, expression, package_heading):
        plugin_locals = dict()
        sources = list()

        matches = regex.finditer(FXN_CAPTURING_REGEX, expression)

        function_strings = set([match.group() for match in matches])

        function_args_value_mapping: MutableMapping[
            FuncitonNameType,
            Dict[int, Union[float, int]]
        ] = dict()

        for function_string in function_strings:
            function_name = regex.findall(
                r'[A-Z0-9_]+?(?=\()', function_string)[0]

            args_string = regex.findall(
                r'[A-Z0-9_]+(.*)', function_string)[0][1:-1]

            args = regex.findall(
                r"\s*('[^'\\]*'|\"[^\"\\]*\"|\d+(?:\.\d*)?|\w+(?:\(\w*\))?)",
                args_string
            )

            args = tuple([eval(arg) for arg in args])

            value, source = eval(
                function_string,
                {'__builtins__': None},
                {
                    function_name: REGISTERED_INTERNAL_CALCULATOR_PLUGIN_FXNS[
                        function_name
                    ](
                        self,
                        package_heading
                    )
                }
            )
            if not function_args_value_mapping.get(function_name):
                function_args_value_mapping[function_name] = dict()

            function_args_value_mapping[function_name][hash(args)] = value

            def fxn(*args):
                result_mapping = function_args_value_mapping[function_name]
                return result_mapping[hash(args)]

            plugin_locals[function_name] = fxn

            sources.append(
                {
                    'used_function_name': function_name,
                    'type': 'internal plugin',
                    'value': value,
                    'source': source,
                }
            )

        return plugin_locals, sources

    def get_internal_plugin_locals(self, expression, package_heading):
        plugin_locals, sources = self.get_internal_vars_plugin_locals(
            expression,
            package_heading
        )

        fxns_plugin_locals, fxns_source = self.get_internal_fxns_plugin_locals(
            expression,
            package_heading
        )

        plugin_locals.update(fxns_plugin_locals)
        sources += fxns_source

        return plugin_locals, sources

    def get_plugin_locals(self, expression, package_heading):
        plugin_locals = dict()
        sources = list()
        plugin_variables_mapping = self.plugin_variable_to_method_mapping

        rgx = '|'.join(plugin_variables_mapping.keys())

        used_plugin_variables = set(
            regex.findall(rgx, expression)
        )

        if not rgx:
            used_plugin_variables = []

        for used_plugin_variable in list(used_plugin_variables):

            plugin_locals[used_plugin_variable], source = plugin_variables_mapping[
                used_plugin_variable].get('loaded_module').init(
                self,
                package_heading
            )

            sources.append(
                {
                    'used_variable_name': used_plugin_variable,
                    'registered_plugin_name': plugin_variables_mapping[
                        used_plugin_variable].get('registered_plugin_name'),
                    'registered_plugin_version': plugin_variables_mapping[
                        used_plugin_variable].get('registered_plugin_version'),
                    'value': plugin_locals[used_plugin_variable],
                    'source': source,
                }
            )

        return plugin_locals, sources

    @functools.cached_property
    def plugin_variable_to_method_mapping(self):
        from irhrs.payroll.utils.calculator_variable import CalculatorVariable

        mapping = dict()

        PAYROLL_APP_DIR = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        PLUGIN_MODULE_DIR = os.path.join(PAYROLL_APP_DIR, 'plugins')

        plugins = PayrollVariablePlugin.objects.filter(
            organization=self.get_organization()
        )

        for plugin in plugins:
            name = CalculatorVariable.calculator_variable_name_from_heading_name(
                plugin.name)

            module_props_dict = json.loads(plugin.module_props)
            folder_name = module_props_dict.get('checksum')

            MODULE_DIR = os.path.join(
                PLUGIN_MODULE_DIR,
                folder_name,
            )

            PLUGIN_EXEC_PATH = os.path.join(
                MODULE_DIR,
                'plugin.so'
            )

            if not os.path.exists(
                PLUGIN_EXEC_PATH
            ):
                os.mkdir(
                    MODULE_DIR
                )

                with open(PLUGIN_EXEC_PATH, 'wb+') as f:
                    f.write(plugin.module)

            module_props_dict = json.loads(plugin.module_props)
            try:
                # mapping[name] = importlib.import_module(
                #     f'irhrs.payroll.plugins.{folder_name}.plugin'
                # )

                mapping[name] = dict(
                    registered_plugin_name=module_props_dict.get('name'),
                    registered_plugin_version=module_props_dict.get('version'),
                    loaded_module=importlib.import_module(
                        f'irhrs.payroll.plugins.{folder_name}.plugin'
                    )
                )

            except Exception:
                # TODO @wrufesh send notification to user about not able to load installed plugin
                # and need to update it

                build_py_version = module_props_dict.get('buildPythonVersion')
                runtime_py_version = '.'.join(
                    list(map(str, sys.version_info[0:3])))
                raise AssertionError(
                    'Plugin runtime python envrironment is other than install environment.'
                    f'Update module. Build: {build_py_version}, Runtime {runtime_py_version}'
                )
        return mapping

    def evaluate_expression(self, expression, **kwargs):

        return_plugin_source = kwargs.get('return_plugin_source', False)
        package_heading = kwargs.get('package_heading_obj')

        # final place to update variables before execution
        self.update_variables_before_execution(expression)

        # START: Compute future employee variables
        if kwargs.get('variable_adaper_kwargs'):
            variable_adapter_kwargs = kwargs.get('variable_adaper_kwargs')
        else:
            variable_adapter_kwargs = self.get_adapter_kwargs()

        employee_conditional_variable_adapter = self.get_conditional_variable_adapter(
            'EMPLOYEE_',
            **variable_adapter_kwargs
        )

        employee_rule_variable_adapter = self.get_rule_variable_adapter(
            'EMPLOYEE_',
            **variable_adapter_kwargs
        )

        self.employee_global_variables = merge_two_dicts(
            self.employee_global_variables,
            employee_conditional_variable_adapter.generate()
        )

        self.employee_global_variables = merge_two_dicts(
            self.employee_global_variables,
            employee_rule_variable_adapter.generate()
        )
        # START: Compute future employee variables

        current_locals = locals()
        current_locals.update(self.employee_global_variables)

        # Override any variables during evaluation
        local_overrides = kwargs.get('local_overrides')
        if local_overrides:
            current_locals.update(local_overrides)
        # for key in self.employee_global_variables.keys():
        #     locals()[key] = self.employee_global_variables[key]

        plugin_locals, sources = self.get_plugin_locals(
            expression,
            package_heading
        )

        internal_plugin_locals, internal_plugin_sources = self.get_internal_plugin_locals(
            expression,
            package_heading
        )

        current_locals.update(
            plugin_locals
        )

        current_locals.update(
            internal_plugin_locals
        )

        # Expression is cleaned for security purpose
        value = eval(expression, globals(), current_locals)

        if return_plugin_source:
            return value, sources + internal_plugin_sources

        return value

    def unit_amount(self, package_heading_obj, **kwargs):
        """calculate unit amount for package_heading_obj"""

        return_sources = kwargs.get('return_sources', False)

        # sources are the resource locators for plugins variables value
        sources = list()

        kwargs['package_heading_obj'] = package_heading_obj
        amount = 0
        if type(package_heading_obj.rules) == str:
            package_heading_obj.rules = json.loads(package_heading_obj.rules)

        self.__processing_heading = package_heading_obj.heading
        try:
            if len(package_heading_obj.rules) > 1:
                sources = list()
                for rule in package_heading_obj.rules:
                    condition_value, condition_sources = self.evaluate_expression(
                        rule.get('condition'),
                        return_plugin_source=True,
                        **kwargs
                    )

                    sources += condition_sources

                    if condition_value:

                        # record tax condition and rule
                        if package_heading_obj.heading.type == "Tax Deduction":
                            self.payroll.tax_condition = rule.get('condition')
                            self.payroll.tax_rule = rule.get('rule')
                            self.payroll.tds_type = rule.get('tds_type', '')

                        r_amount, r_sources = self.evaluate_expression(
                            rule.get('rule'),
                            return_plugin_source=True,
                            **kwargs
                        )

                        sources += r_sources

                        sources = self.remove_duplicate_sources(sources)

                        amount += r_amount
            elif len(package_heading_obj.rules) == 1:
                rule = package_heading_obj.rules[0]

                # record tax condition and rule
                if package_heading_obj.heading.type == "Tax Deduction":
                    self.payroll.tax_rule = rule.get('rule')
                    self.payroll.tds_type = rule.get('tds_type', '')
                r_amount, sources = self.evaluate_expression(
                    rule.get('rule'),
                    return_plugin_source=True,
                    **kwargs
                )

                if isinstance(r_amount, str):
                    try:
                        r_amount = float(r_amount)
                    except ValueError:
                        r_amount = 0

                amount += r_amount

        except (TypeError, ZeroDivisionError) as err:
            raise InvalidVariableTypeOperation(
                'Invalid formula in package ' + str(err),
                self.employee,
                package_heading_obj
            )

        self.__processing_heading = None

        if return_sources:

            return amount, sources

        return amount

    def remove_duplicate_sources(self, sources):
        res = []
        for i in sources:
            if i not in res:
                res.append(i)
        return res

    def get_working_days_from_organization_calendar(self, from_date, to_date):
        # from_date = self.datework.date_class_to_ad(from_date)
        # to_date = self.datework.date_class_to_ad(to_date)
        include_holiday_offday = self.payroll_config.include_holiday_offday_in_calculation
        if include_holiday_offday:
            # if want to include all days then just count
            return (to_date - from_date).days + 1

        yesterday_or_to_date = self.get_yesterday_or_to_date(to_date)

        if yesterday_or_to_date >= from_date:
            working_days = gwdfoc(
                self.employee, from_date, yesterday_or_to_date, include_holiday_offday
            )
        else:
            working_days = 0

        if self.simulated_from:
            # no timesheets in future so, need to simulate them
            simulate_from = self.get_simulate_from(from_date)
            working_days += get_work_days_count_from_simulated_timesheets(
                self.employee, simulate_from, to_date
            )

        return working_days

    def _get_working_days(self, **slot):

        if type(self.month_days_setting) == int:
            if slot.get('days_count') == slot.get('month_days'):
                return self.month_days_setting, self.month_days_setting
            else:
                # TODO @Ravi: Ratio may also be from organization calendar
                return (
                    self.month_days_setting *
                    (slot.get('days_count') / slot.get('month_days')),
                    self.month_days_setting
                )
        # elif self.month_days_setting == 'DATE_CALENDAR':
        #     return (
        #         slot.get('days_count'),
        #         slot.get('month_days')
        #     )
        elif self.month_days_setting == 'ORGANIZATION_CALENDAR':
            if not self.calculate_tax:
                return (
                    slot.get('days_count'),
                    slot.get('month_days')
                )
            return (
                self.get_working_days_from_organization_calendar(
                    slot.get('start'),
                    slot.get('end')
                ),
                self.get_working_days_from_organization_calendar(
                    slot.get('actual_start'),
                    slot.get('actual_end')
                )
            )

    def get_working_days(self, slot):
        """Returns days count and month days
        :param slot:
        :return: (working_days in a slot, working days in a month)
        """
        # moved definition to support lru_cache

        return self._get_working_days(**slot)

    def get_worked_days_for_daily_heading(
        self,
        slot,
        package_heading_obj,
        deduct_amount_on_leave,
        pay_when_present_holiday_offday,
        deduct_amount_on_remote_work=False
    ):
        from_date = slot.get('start')
        to_date = slot.get('end')
        adjust_previous_payroll_from = slot.get('adjust_payroll_from')
        from_date = adjust_previous_payroll_from or from_date
        yesterday_or_to_date = self.get_yesterday_or_to_date(to_date)

        return get_worked_days_for_daily_heading(
            self.employee,
            from_date,
            yesterday_or_to_date,
            pay_when_present_holiday_offday=pay_when_present_holiday_offday,
            deduct_amount_on_leave=deduct_amount_on_leave,
            deduct_amount_on_remote_work=deduct_amount_on_remote_work
        )

    def _get_worked_days(self, **slot) -> Tuple[int, int]:
        package_heading_obj = slot.pop('package_heading_obj')
        include_non_working_days = slot.pop('include_non_working_days')
        simulate_future_days = slot.pop('simulate_future_days')

        working_days, month_working_days = self.get_working_days(slot)
        logger.debug(
            f"working_days {str(working_days)} month_days {str(month_working_days)}")

        from_date = slot.get('start')
        to_date = slot.get('end')
        adjust_previous_payroll_from = slot.get('adjust_payroll_from')

        count_offday_holiday_as_worked = self.payroll_config.include_holiday_offday_in_calculation

        if (
            not self.calculate_tax or
            (package_heading_obj and not package_heading_obj.absent_days_impact)
        ):
            return working_days, month_working_days

        yesterday_or_to_date = self.get_yesterday_or_to_date(to_date)

        if not simulate_future_days:
            from_date = adjust_previous_payroll_from or from_date
            logger.debug(
                f"calculating daily from {str(from_date)} {str(yesterday_or_to_date)}")

            worked_days = gwd(
                self.employee,
                from_date,
                yesterday_or_to_date,
                include_non_working_days,
                count_offday_holiday_as_worked
            )
            logger.debug(f"worked days {worked_days}")

        else:

            logger.debug(f"slot_info {str(slot)}")

            logger.debug(
                "calculating actual working days from "
                f"{str(from_date)}, {str(yesterday_or_to_date)}")
            # actual worked days
            if yesterday_or_to_date >= from_date:
                worked_days = gwd(
                    self.employee,
                    from_date,
                    yesterday_or_to_date,
                    include_non_working_days,
                    count_offday_holiday_as_worked
                )
            else:
                # no actual worked days
                worked_days = 0
            logger.debug(f"actual_worked_days {worked_days}")

            # previous payroll has adjustments
            if adjust_previous_payroll_from:
                logger.debug("Adjusting")
                logger.debug(f"Absent days from previous {str(adjust_previous_payroll_from)}  "
                             f"{str(from_date - timedelta(days=1))}")
                adjusted_absent_days = get_absent_days(
                    self.employee,
                    adjust_previous_payroll_from,
                    from_date - timedelta(days=1)
                )
                logger.debug("Absent days count " + str(adjusted_absent_days))

                logger.debug("Unpaid leave days " + str(adjust_previous_payroll_from) + " " + str(
                    from_date - timedelta(days=1)))
                adjusted_unpaid_leave_days = get_unpaid_leave_days(
                    self.employee,
                    adjust_previous_payroll_from,
                    from_date - timedelta(days=1)
                )
                logger.debug("unpaid leave count " +
                             str(adjusted_unpaid_leave_days))

                worked_days = worked_days - (
                    adjusted_absent_days + adjusted_unpaid_leave_days
                )
                logger.debug(
                    "worked days after adjusting from previous " + str(worked_days))

            # simulating future days
            if self.simulated_from and self.simulated_from <= to_date:
                simulate_from = self.get_simulate_from(from_date)
                logger.debug("simulating future " +
                             str(simulate_from) + str(to_date))

                if self.payroll_config.include_holiday_offday_in_calculation:
                    # if include holiday/offday in calculation assume all days as worked days
                    future_worked_days_simulated = (
                        to_date - simulate_from).days + 1
                else:
                    future_worked_days_simulated = get_work_days_count_from_simulated_timesheets(
                        self.employee, simulate_from, to_date
                    )
                logger.debug("future days simulated " +
                             str(future_worked_days_simulated))
                worked_days = worked_days + future_worked_days_simulated
                logger.debug(
                    "worked days after adding future days " + str(worked_days))

        return (
            worked_days,
            month_working_days
        )

    def get_worked_days(
        self,
        slot: dict,
        package_heading_obj: Optional[PackageHeading] = None,
        include_non_working_days: Optional[bool] = False,
        simulate_future_days: Optional[bool] = True
    ) -> Tuple[int, int]:
        """Total Worked days in slot

        :param slot: Slot
        :param package_heading_obj: Heading object accessing worked days
        :param include_non_working_days
        :param simulate_future_days: True for Monthly, False for daily

        :return: Worked Days, Month(Slot) Days
        """
        # moved definition to support lru_cache
        return self._get_worked_days(
            **slot,
            package_heading_obj=package_heading_obj,
            include_non_working_days=include_non_working_days,
            simulate_future_days=simulate_future_days
        )

    def get_hours_of_work(self, slot, package_heading_obj):

        hourly_source = package_heading_obj.hourly_heading_source

        if not hourly_source:
            return 0

        adjust_payroll_from = slot.get('adjust_payroll_from')

        if adjust_payroll_from:
            # If we need to adjust payroll from previous payroll
            # then calculate worked hours from previous date, as
            # worked hours will not be simulated future worked
            # hours are considered.
            from_date = adjust_payroll_from
        else:
            from_date = slot.get('start')

        to_date = slot.get('end')
        yesterday_or_to_date = self.get_yesterday_or_to_date(to_date)
        logger.debug("calculating hourly heading from " +
                     str(from_date) + "to" + str(yesterday_or_to_date))

        hours_logged = ghow(self.employee, from_date,
                            yesterday_or_to_date, hourly_source)
        logger.debug("hours logged " + str(hours_logged))
        return hours_logged

    def get_yesterday_or_to_date(self, to_date):
        if self.simulated_from:
            yesterday_or_to_date = min(
                self.simulated_from - timedelta(days=1),
                to_date
            )  # yesterday or to_date which ever is earlier
        else:
            yesterday_or_to_date = to_date
        return yesterday_or_to_date

    def get_simulate_from(self, from_date):
        return max(from_date, self.simulated_from)

    def get_slots(self):
        slots = list()
        fy_datas = self.datework.get_fiscal_year_data_from_date_range(
            self.from_date,
            self.to_date
        )

        for fy_data in fy_datas:
            month_slots = self.datework.get_months_data_from_date_range(
                self.appoint_date,
                *fy_data.get(
                    'date_range'
                )
            )
            for month_slot in month_slots:
                slots.append(month_slot)
        return slots

    def total_taxable_additions(self):
        # Added before tax
        taxable_addition_heading_types = self.init_kwargs.get(
            'taxable_addition_heading_types', ['Extra Addition', 'Addition']
        )
        total_taxable_additions_records = list(filter(
            lambda x: x.heading.type in taxable_addition_heading_types and x.heading.taxable,
            self.payroll.rows))
        return sum(x.amount for x in total_taxable_additions_records)

    def total_non_taxable_deductions(self):
        # Deduced before tax deduction
        taxable_deduction_heading_types = self.init_kwargs.get(
            'taxable_deduction_heading_types', [
                'Deduction', 'Extra Deduction'
            ]
        )
        if self.update_remaining_rebate_row:
            _ = update_monthly_rebate_rows(self.payroll.rows, self.from_date,
                                              self.to_date)
        total_non_taxable_deductions_records = list(filter(
            lambda x: (
                x.heading.type in taxable_deduction_heading_types
                and not x.heading.taxable
            ),
            self.payroll.rows))
        return sum(x.amount for x in total_non_taxable_deductions_records)

    def total_taxable_amount(self):
        return self.total_taxable_additions() - self.total_non_taxable_deductions()

    # START Tax calculation
    def tax_deduction_handler(self, package_heading):

        amount, sources = self.get_tax_amount(package_heading)

        if str(package_heading.heading.id) in self.edited_general_headings.keys():
            self.set_edited_general_headings(package_heading)
            return

        row = self.payroll.update_row(
            ReportRow(
                from_date=self.from_date,
                to_date=self.to_date,
                employee=self.employee,
                package_heading=package_heading,
                amount=amount,
                plugin_sources=sources
            )
        )

        self.set_heading_variable(
            package_heading.heading,
            row.amount
        )

    def get_taxable_amount_from_entry(self, start_date, end_date):
        """Past taxable amount"""
        total_taxable_addition = ReportRowRecord.objects.filter(
            employee_payroll__employee=self.employee,
            heading__type__in=['Extra Addition', 'Addition'],
            heading__taxable=True,
            # from_date__gte=self.datework.date_class_to_ad(start_date),
            # to_date__lte=self.datework.date_class_to_ad(end_date),
            from_date__gte=start_date,
            to_date__lte=end_date,
            employee_payroll__payroll__status='Confirmed'
        ).aggregate(
            total_amount=Coalesce(
                Sum('amount'),
                0.0
            )
        ).get('total_amount')

        total_non_taxable_deduction = ReportRowRecord.objects.filter(
            employee_payroll__employee=self.employee,
            heading__type__in=['Deduction', 'Extra Deduction'],
            heading__taxable=False,
            # from_date__gte=self.datework.date_class_to_ad(start_date),
            # to_date__lte=self.datework.date_class_to_ad(end_date),
            from_date__gte=start_date,
            to_date__lte=end_date,
            employee_payroll__payroll__status='Confirmed'
        ).aggregate(
            total_amount=Coalesce(
                Sum('amount'),
                0.0
            )
        ).get('total_amount')

        """
        query taxable additions and non taxable deductions
        and additions - deductions
        Note: Also look for taxable additions and non_taxable
        deductions in adjustments in between the input date range
        :param start_date:   filter start date
        :param end_date: filter end date
        :return: (amount, upto_last paid_date + 1 ie new start)
        """
        taxable_amount = total_taxable_addition - total_non_taxable_deduction
        return taxable_amount

    def get_paid_tax_from_entry(self, start_date, end_date):
        return ReportRowRecord.objects.filter(
            employee_payroll__employee=self.employee,
            heading__type='Tax Deduction',
            # from_date__gte=self.datework.date_class_to_ad(start_date),
            # to_date__lte=self.datework.date_class_to_ad(end_date),
            from_date__gte=start_date,
            to_date__lte=end_date,
            employee_payroll__payroll__status='Confirmed'
        ).aggregate(
            total_amount=Coalesce(
                Sum('amount'),
                0.0
            )
        ).get('total_amount')

    def _get_taxable_slots_in_fy(self, fy_start_date, fy_end_date):
        """
        gets the working time slots in between the fiscal year
        :param fy_start_date:
        :param fy_end_date:
        :return: list of working slots
        """
        start = fy_start_date
        end = fy_end_date

        if self.dismiss_date:
            if self.dismiss_date < fy_end_date:
                end = self.dismiss_date
        return start, end

    @property
    def annual_gross_salary(self):
        """Annual Gross Salary (Annual Taxable Salary)

        past amount in current fiscal year + current slot taxable amount +
            future taxable amount
        """
        if self.__ags_from_date == self.from_date and self.__ags_to_date == self.to_date:
            return self.__ags
        else:
            self.__ags_from_date = self.from_date
            self.__ags_to_date = self.to_date

            amount = 0
            taxable_slot_in_fy = self.taxable_slot_in_fy

            amount = self.get_taxable_amount_from_entry(
                taxable_slot_in_fy[0],
                taxable_slot_in_fy[1]
            )

            current_slot_taxable_amount = self.total_taxable_amount()

            amount += current_slot_taxable_amount

            user_experience = self.employee.first_date_range_user_experiences(
                self.from_date,
                self.to_date
            )

            if (self.to_date + timedelta(days=1)) < taxable_slot_in_fy[1]:

                taxable_heading_types_config = dict()
                if self.ADJUST_TAX_CHANGE_DUE_TO_EXTRA_ADDITION_DEDUCTION_IN_SAME_MONTH:
                    # if adjusting tax change due to extra addition and deduction in same month
                    # exclude extra addition and extra deduction amounts from future taxable amounts
                    taxable_heading_types_config.update({
                        'taxable_addition_heading_types': ['Addition'],
                        'taxable_deduction_heading_types': ['Deduction']
                    })

                logger.debug("old_amount --> ags" + str(amount))

                future_projected_payroll = PackageSalaryCalculator(
                    user_experience=user_experience,
                    employee=self.employee,
                    datework=self.datework,
                    from_date=self.to_date + timedelta(days=1),
                    to_date=taxable_slot_in_fy[1],
                    salary_package=self.salary_package,
                    appoint_date=self.appoint_date,
                    month_days_setting=self.month_days_setting,
                    package_assigned_date=self.package_assigned_date,
                    calculate_tax=False,
                    calculate_yearly=True,
                    use_slot_days=True,
                    ** taxable_heading_types_config
                )

                rows = update_monthly_rebate_rows(
                    future_projected_payroll.payroll.rows, self.from_date, self.to_date,
                    include_current_month=False, calculate_projected_months=True
                )

                self.payroll.add_future_projected_rows(
                    rows
                )

                amount += future_projected_payroll.total_taxable_amount()

                logger.debug("new_amount --> ags" + str(amount))

            self.payroll.annual_gross_salary = amount

            self.__ags = amount

            return self.__ags

    def get_backdated_extra_income(self):
        taxable_addition_filter = Q(
            heading__type__in=['Addition', 'Extra Addition'],
            heading__taxable=True
        )

        non_taxable_deduction_filter = Q(
            heading__type__in=['Deduction', 'Extra Deduction'],
            heading__taxable=False
        )

        total_previous_current_amount = self.get_backdated_calculations().aggregate(
            taxable_additions_new=Sum(
                'current_amount',
                filter=taxable_addition_filter
            ),
            taxable_additions_old=Sum(
                'previous_amount',
                filter=taxable_addition_filter
            ),
            non_taxable_deductions_new=Sum(
                'current_amount',
                filter=non_taxable_deduction_filter
            ),
            non_taxable_deductions_old=Sum(
                'previous_amount',
                filter=non_taxable_deduction_filter
            )
        )

        def getAggregatedValue(x):
            return total_previous_current_amount.get(x) or 0

        taxable_addition_difference = getAggregatedValue(
            'taxable_additions_new'
        ) - getAggregatedValue(
            'taxable_additions_old'
        )
        non_taxable_deduction_difference = getAggregatedValue(
            'non_taxable_deductions_new'
        ) - getAggregatedValue(
            'non_taxable_deductions_old'
        )

        extra_income = taxable_addition_difference - non_taxable_deduction_difference

        return extra_income

    def get_extra_addition_minus_extra_deduction(self):
        """
        total_taxable_extra_additions - total_non_taxable_extra_deductions
        """

        total_taxable_extra_additions_records = list(filter(
            lambda x: x.heading.type in [
                'Extra Addition'] and x.heading.taxable,
            self.payroll.rows
        ))

        total_taxable_hourly_addition_records = list(filter(
            lambda x: x.heading.type in [
                'Addition'
            ] and x.heading.taxable and x.heading.duration_unit == 'Hourly',
            self.payroll.rows
        ))

        total_taxable_extra_additions = sum(
            x.amount for x in total_taxable_extra_additions_records
        ) + sum(
            x.amount for x in total_taxable_hourly_addition_records
        )

        total_taxable_extra_additions += self.get_backdated_extra_income()

        total_non_taxable_extra_deductions_records = list(filter(
            lambda x: x.heading.type in [
                'Extra Deduction'] and not x.heading.taxable,
            self.payroll.rows
        ))

        total_non_taxable_hourly_deduction_records = list(filter(
            lambda x: x.heading.type in [
                'Deduction'
            ] and not x.heading.taxable and x.heading.duration_unit == 'Hourly',
            self.payroll.rows
        ))

        total_non_taxable_extra_deductions = sum(
            x.amount for x in total_non_taxable_extra_deductions_records
        ) + sum(
            x.amount for x in total_non_taxable_hourly_deduction_records
        )

        return total_taxable_extra_additions - total_non_taxable_extra_deductions

    @property
    def taxable_slot_in_fy(self):
        if (
            self.__taxable_slots_in_fy_from_date == self.from_date and
            self.__taxable_slots_in_fy_to_date == self.to_date
        ):
            return self.__taxable_slots_in_fy

        self.__taxable_slots_in_fy_from_date = self.from_date
        self.__taxable_slots_in_fy_to_date = self.to_date

        fy_data = self.datework.get_fiscal_year_data_from_date_range(
            self.from_date,
            self.to_date
        )[0]
        self.__taxable_slots_in_fy = self._get_taxable_slots_in_fy(
            fy_data.get('fy_slot')[0],
            fy_data.get('fy_slot')[1]
        )
        return self.__taxable_slots_in_fy

    def get_remaining_slots_count(self, slot_start):
        if slot_start > self.taxable_slot_in_fy[1]:
            # if next_slot_start is after end of taxable slot then no slots remaining
            return 0
        return len(
            self.get_slots_from_date_range(
                slot_start,
                self.taxable_slot_in_fy[1]
            )
        )

    @property
    def remaining_slots_count(self):
        if (
            self.__remaining_slots_count_from_date == self.from_date
            and self.__remaining_slots_count_to_date == self.to_date
        ):
            return self.__remaining_slots_count

        self.__remaining_slots_count_from_date = self.from_date
        self.__remaining_slots_count_to_date = self.to_date

        next_slot_start = self.to_date + timedelta(days=1)
        self.__remaining_slots_count = self.get_remaining_slots_count(
            next_slot_start)
        return self.__remaining_slots_count

    def get_paid_tax(self, taxable_slot_in_fy):
        paid_tax = self.get_paid_tax_from_entry(
            taxable_slot_in_fy[0],
            self.to_date
        )
        return paid_tax

    def get_remaining_working_days_in_fy(self, taxable_slot_in_fy, from_date=None):
        from_date = from_date or self.from_date
        remaining_working_days_in_fy_delta = taxable_slot_in_fy[1] - from_date
        remaining_working_days_in_fy = remaining_working_days_in_fy_delta.days + 1
        return remaining_working_days_in_fy

    def get_remaining_months_in_fy(self, to_date=None):
        to_date = to_date or self.to_date
        if to_date == self.to_date:
            # as remaining slots does not include current slot
            return self.remaining_slots_count + 1
        else:
            return self.get_remaining_slots_count(to_date + timedelta(days=1)) + 1

    def get_total_annual_tax(self, tax_deduction_obj, amount):
        self.set_global_var__annual_gross_salary(amount)
        total_tax, sources = self.unit_amount(
            tax_deduction_obj,
            return_sources=True
        )
        return total_tax, sources

    def get_slots_from_date_range(self, start, end):
        slots = list()
        fy_datas = self.datework.get_fiscal_year_data_from_date_range(
            start,
            end
        )

        for fy_data in fy_datas:
            month_slots = self.datework.get_months_data_from_date_range(
                fy_data.get('date_range')[0],
                *fy_data.get(
                    'date_range'
                )
            )
            for month_slot in month_slots:
                slots.append(month_slot)
        return slots

    def get_tax_except_extra(self, annual_tax, annual_gross_salary, tax_deduction_heading):
        """
        tax_not_including_extra
        """
        new_annual_gross_salary = annual_gross_salary - \
            self.get_extra_addition_minus_extra_deduction()

        overrides = {'__ANNUAL_GROSS_SALARY__': new_annual_gross_salary}

        # getting list of dependencies to recalculate
        # only Type2Cnst will be recalculated
        dependencies = tax_deduction_heading.dependencies.all().filter(
            type='Type2Cnst').order_by('order')

        # calculate new value of dependencies
        for dependency in dependencies:
            unit_amount = self.unit_amount(
                dependency, local_overrides=overrides)
            variable_name = f"__{get_variable_name(dependency.heading.name)}__"
            overrides.update({variable_name: unit_amount})

        tax_not_including_extra, sources = self.unit_amount(
            tax_deduction_heading,
            local_overrides=overrides,
            return_sources=True
        )

        return tax_not_including_extra, sources

    def get_tax_amount(self, tax_deduction_heading_object):

        sources = list()
        if self.calculate_tax:
            annual_gross_salary = self.annual_gross_salary

            paid_tax = self.get_paid_tax(self.taxable_slot_in_fy)
            # remaining_working_days_in_fy = self.get_remaining_working_days_in_fy(
            #     self.taxable_slot_in_fy)

            total_annual_tax, sources = self.get_total_annual_tax(
                tax_deduction_heading_object, annual_gross_salary)

            remaining_tax_to_be_paid = total_annual_tax - paid_tax

            self.set_heading_variable(
                tax_deduction_heading_object.heading,
                total_annual_tax,
                '_UNIT_AMOUNT'
            )

            # Below logic seems allright coz partial contract has dismiss date
            total_remaining_slots = self.remaining_slots_count
            tax_amount = remaining_tax_to_be_paid / (total_remaining_slots + 1)

            # Extra addition and deduction include all extra additions or deduction including
            # hourly headings.
            if self.ADJUST_TAX_CHANGE_DUE_TO_EXTRA_ADDITION_DEDUCTION_IN_SAME_MONTH:
                annual_tax_not_including_extra, sources = self.get_tax_except_extra(
                    total_annual_tax,
                    annual_gross_salary,
                    tax_deduction_heading_object
                )
                logger.debug(f"annual tax including extra: {total_annual_tax}")
                logger.debug(
                    f"annual tax not including extra: {annual_tax_not_including_extra}")
                tax_diff = total_annual_tax - annual_tax_not_including_extra
                logger.debug(f"tax_diff: {tax_diff}")
                remaining_tax_to_be_paid = annual_tax_not_including_extra - paid_tax
                logger.debug(
                    f"remaining_to_be_paid: {remaining_tax_to_be_paid}")

                tax_amount = (remaining_tax_to_be_paid /
                              (total_remaining_slots + 1)) + tax_diff
                logger.debug(f"tax amount: {tax_amount}")

            # store in employee payroll
            self.payroll.annual_tax = total_annual_tax
            self.payroll.paid_tax = paid_tax + tax_amount
            self.payroll.tax_to_be_paid = remaining_tax_to_be_paid - tax_amount

            self.set_heading_variable(
                tax_deduction_heading_object.heading,
                tax_amount
            )

            return tax_amount, sources
        else:
            return 0, []

    # END Tax calculation

    @property
    def default_advance_salary_package_deduction_heading(self):
        heading = self.get_advance_salary_heading(self.get_organization())
        current_max_package_heading_order = self.get_current_max_package_heading_order()
        package_heading, _ = PackageHeading.objects.get_or_create(
            package=self.get_salary_package(),
            heading=heading,
            defaults=dict(
                order=current_max_package_heading_order + 1,
                rules='[{"rule": "0"}]',
            )
        )
        self.get_salary_package().package_headings.add(package_heading)
        return package_heading

    @staticmethod
    def get_advance_salary_heading(organization):
        instance, _ = Heading.objects.get_or_create(
            organization=organization,
            name='Advance Salary Deduction',
            type='Type2Cnst',
            payroll_setting_type='Penalty/Deduction',
            defaults=dict(
                rules='[{"rule": "0"}]',  # to fix validation
                order=Heading.get_next_heading_order(organization.slug),
                is_hidden=True,
            )
        )
        return instance

    def get_organization(self):
        organization = self.employee.detail.organization
        return organization

    def get_current_max_package_heading_order(self):
        current_max_package_heading_order = self.get_salary_package().package_headings.aggregate(
            max_heading=Max('order')
        )['max_heading'] or 0
        return current_max_package_heading_order

    def get_salary_package(self):
        return self.salary_package

    @staticmethod
    def get_paid_amount_in_date_range_from_heading(
        heading, employee, from_date, to_date, paid_this_time=0.0
    ):
        actual_paid = ReportRowRecord.objects.filter(
            employee_payroll__employee=employee,
            from_date__gte=from_date,
            to_date__lte=to_date,
            heading=heading,
            employee_payroll__payroll__status='Confirmed'
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0.0
        return actual_paid + paid_this_time

    @property
    def future_package_calculator(self) -> 'PackageSalaryCalculator':
        """Calculator Instance used to get future amount of headings"""
        if (
            self.__package_salary_package == self.salary_package
            and self.__package_salary_from_date == self.from_date
            and self.__package_salary_to_date == self.to_date
        ):
            return self.__package_salary_calculator
        else:
            self.__package_salary_from_date = self.from_date
            self.__package_salary_to_date = self.to_date
            self.__package_salary_package = self.salary_package

            # for calculating annual amount
            if (self.to_date + timedelta(days=1)) < self.taxable_slot_in_fy[1]:
                user_experience = self.employee.first_date_range_user_experiences(
                    self.from_date,
                    self.to_date
                )
                # TODO @wrufesh below code is redundant with tax calculator's future
                # projection calculator
                self.__package_salary_calculator = PackageSalaryCalculator(
                    user_experience=user_experience,
                    employee=self.employee,
                    datework=self.datework,
                    from_date=self.to_date + timedelta(days=1),
                    to_date=self.taxable_slot_in_fy[1],
                    salary_package=self.salary_package,
                    appoint_date=self.appoint_date,
                    month_days_setting=self.month_days_setting,
                    package_assigned_date=self.package_assigned_date,
                    calculate_tax=False,
                    calculate_yearly=True,
                    calculate_annual_amount=False
                )
            else:
                self.__package_salary_calculator = None
        return self.__package_salary_calculator

    @classmethod
    def get_annual_amount_from_heading(
        cls,
        employee,
        heading,
        taxable_slot,
        current_amount,
        future_package_salary_calculator,
    ):
        """
        Calculate
        """

        paid = cls.get_paid_amount_in_date_range_from_heading(
            heading,
            employee,
            from_date=taxable_slot[0],
            to_date=taxable_slot[1],
        )
        paid += current_amount

        remaining_payable = 0
        if future_package_salary_calculator:
            remaining_payable = \
                future_package_salary_calculator.payroll.get_heading_amount_from_heading(
                    heading
                ) or 0

        # --- old way of calculating remaining payable << daily basis >> ------
        # future_fy_slot_days = \
        #     (
        #         taxable_slot[1] - (payroll_to_date + timedelta(days=1))
        #     ).days + 1
        #
        # one_day_amount = current_amount / (
        #     (payroll_to_date - payroll_from_date).days + 1
        # )
        # remaining_payable = one_day_amount * future_fy_slot_days
        # --- end old way ------------------------------------------------------
        return paid + remaining_payable


class PackageSalaryCalculator(EmployeeSalaryCalculator):
    """Calculate package amounts of an employee

    All parameters are same as EmployeesalaryCalculator with some additionals

    :param user_expereience: Current Experience of user
    :param use_slot_days: If True, month days from slot will be used otherwise
        default of 30 will be used
    """
    calculate_package_amount = False
    calculate_backdated_payroll = False

    def __init__(self, user_experience, *args, **kwargs):
        self.__user_experience = user_experience

        # because there may not be an experience in simulated date range or may is incorrect
        def get_current_step(*args, **kwargs):
            return self.__user_experience.current_step

        self.employee_rule_variable_adapter_class = type(
            get_random_class_name(),
            (self.employee_rule_variable_adapter_class,),
            {'get_current_step': get_current_step}
        )

        self.employee_conditional_variable_adapter_class = type(
            get_random_class_name(),
            (self.employee_conditional_variable_adapter_class,),
            {'get_current_step': get_current_step}
        )

        super().__init__(*args, **kwargs)

    def get_working_days_from_organization_calendar(self, from_date, to_date):
        return 30

    def get_working_days(self, slot):
        if self.init_kwargs.get("use_slot_days") and slot:
            return slot.get("days_count", 30), slot.get("month_days", 30)
        return 30, 30

    def get_worked_days(self, slot, *args, **kwargs):
        if self.init_kwargs.get("use_slot_days") and slot:
            return slot.get("days_count", 30), slot.get("month_days", 30)
        return 30, 30

    def get_hours_of_work(self, slot, package_heading_obj):
        return 0

    def set_repayment_heading(self, package_heading, repayment=None):
        super().set_repayment_heading(package_heading)

    def get_worked_days_for_daily_heading(
        self,
        slot,
        package_heading_obj,
        deduct_amount_on_leave,
        pay_when_present_holiday_offday,
        deduct_amount_on_remote_work=False
    ):
        return 30


def calculate_package_rows(
    user_experience_package_slot: UserExperiencePackageSlot,
    effective_date: Optional[date] = None
) -> List[ReportRow]:
    """Calculate package amount of given package slot

    :param user_experience_package_slot: UserExperiencePackageSlot instance
    :param effective_date: Fiscal Year including this date will be used. If not
        passed, default of user_experience_package_slog.active_from_date will be
        used

    :return: Calculatd Rows
    """
    user_experience = user_experience_package_slot.user_experience
    employee = user_experience.user
    datework = FY(user_experience.organization)
    payroll_start_fiscal_year = OrganizationPayrollConfig.objects.filter(
        organization=user_experience.organization
    ).first()

    package = user_experience_package_slot.package
    appoint_date = get_appoint_date(employee, payroll_start_fiscal_year)
    applicable_from = user_experience_package_slot.active_from_date
    month_days_setting = 'ORGANIZATION_CALENDAR'

    if effective_date:
        # if effective date is passed used month of effective date
        applicable_from = effective_date

    # month running of package applicable from
    fiscal_year_month = FiscalYearMonth.objects.filter(
        end_at__gte=applicable_from,
        fiscal_year__organization=user_experience.organization
    ).order_by('end_at').first()

    from_date = fiscal_year_month.start_at
    to_date = fiscal_year_month.end_at

    calculation = PackageSalaryCalculator(
        user_experience=user_experience,
        employee=user_experience.user,
        datework=datework,
        from_date=from_date,
        to_date=to_date,
        salary_package=package,
        appoint_date=appoint_date,
        month_days_setting=month_days_setting,
        package_assigned_date=user_experience_package_slot.active_from_date
    )

    return calculation.payroll.rows


def create_package_rows(user_experience_package_slot: UserExperiencePackageSlot) -> None:
    """Calculate and Store package amounts of given package slot

    Called on update of UserExperiencePackageSlot, this will update
    ReportRowUserExperiencePackage.

    :pram user_expereience_package_slot: UserExpereiencePackageSlot instance
    """
    rows = calculate_package_rows(user_experience_package_slot)

    with transaction.atomic():
        ReportRowUserExperiencePackage.objects.filter(
            package_slot=user_experience_package_slot
        ).delete()

        ReportRowUserExperiencePackage.objects.bulk_create(
            [
                ReportRowUserExperiencePackage(
                    package_slot=user_experience_package_slot,
                    package_heading=row.package_heading,
                    package_amount=row.amount
                )
                for row in rows
            ]
        )


class NoEmployeeSalaryCalculator(EmployeeSalaryCalculator):
    """Calculator to use when we don't have Employee Instance (eg. Offer Letter)

    Use Case us demonstrated at :func:`irhrs.payroll.utils.virtual_user_payroll.calculate_payroll`
    """
    employee_conditional_variable_adapter_class = NoEmployeeConditionalVariableAdapter
    employee_rule_variable_adapter_class = NoEmployeeRuleVariableAdapter
    calculate_package_amount = False
    calculate_backdated_payroll = False

    def __init__(self, employee, *args, **kwargs):

        # Fixed the issue regarding the PreEmployment employee
        # where there will be not be any organization under employee detail
        employee.detail = DummyObject(organization=employee.organization)
        employee.voluntary_rebates = UserVoluntaryRebate.objects.none()
        employee.timesheets = TimeSheet.objects.none()
        super().__init__(employee, *args, **kwargs)

    def get_hours_of_work(self, slot, package_heading_obj):
        hourly_source = package_heading_obj.hourly_heading_source
        if not hourly_source:
            return 0
        if hourly_source == 'Overtime':
            return 0
        return 30 * 8

    def get_advance_salary_deduction_heading(self):
        return None

    def get_working_days(self, slot):
        return 30, 30

    def get_worked_days(self, *args, **kwargs):
        return 30, 30

    def get_worked_days_for_daily_heading(self, *args, **kwargs):
        return 30

    def get_paid_tax_from_entry(self, start_date, end_date):
        return 0

    def get_taxable_amount_from_entry(self, start_date, end_date):
        return 0

    def get_organization(self):
        # employee means pre employment
        return self.employee.organization

    @property
    def previous_payroll(self):
        return None

    @staticmethod
    def get_paid_amount_in_date_range_from_heading(
        heading, employee, from_date, to_date, paid_this_time=0.0
    ):
        return paid_this_time

    def get_rebate_amount(self, taxable_slot_in_fy):
        return 0
