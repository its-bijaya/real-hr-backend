import functools
from irhrs.core.utils.common import get_today

from django.test.utils import tag
from django.utils import timezone
from irhrs.users.api.v1.tests.factory import UserExperienceFactory, UserFactory
from typing import Callable
from unittest.mock import patch
from datetime import date

from irhrs.common.api.tests.common import BaseTestCase
from irhrs.payroll.tests.utils import PackageUtil
from irhrs.payroll.utils.calculator import EmployeeSalaryCalculator
from irhrs.payroll.utils.datework.date_helpers import DateWork
from irhrs.organization.api.v1.tests.factory import OrganizationFactory


@tag("profiling")
class TestCalculator(BaseTestCase):

    @property
    def _round_2(self):
        return functools.partial(round, ndigits=2)

    @property
    def datework(self):
        return DateWork(
            # set start of fiscal year to jan 1
            fiscal_year_start_month_date=(1, 1)
        )

    @property
    def jan_1(self):
        return date(year=get_today().year, month=1, day=1)

    @property
    def jan_31(self):
        return date(year=get_today().year, month=1, day=31)

    def get_payroll_config(self, **kwargs):
        return None

    def get_payroll(
        self,
        employee,
        appoint_date,
        payroll_config,
        from_date,
        to_date,
        package,
        working_days,
        worked_days=(0, 30),
        previous_taxable_amount=0,
        rebate_amount=0,
        paid_tax=0,
        get_worked_days_fn: Callable = None
    ):

        with patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.previous_payroll',
            return_value=None
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.payroll_config',
            return_value=payroll_config
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_working_days',
            return_value=working_days
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_worked_days',
            **(
                {'new': get_worked_days_fn}
                if get_worked_days_fn
                else {'return_value': worked_days}
            )
            # ), patch(
            #     'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_taxable_amount_from_entry',
            #     return_value=previous_taxable_amount
            # ), patch(
            #     'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_rebate_amount',
            #     return_value=rebate_amount
            # ), patch(
            #     'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_paid_tax',
            #     return_value=paid_tax
        ):
            calculator = EmployeeSalaryCalculator(
                employee=employee,
                datework=self.datework,
                from_date=from_date,
                to_date=to_date,
                salary_package=package,
                appoint_date=appoint_date,
                simulated_from=None
            )
            return calculator.payroll

    def test_payroll_generation(self):

        execution_speeds = []
        org = OrganizationFactory()
        users = [UserFactory(_organization=org) for _ in range(10)]

        for user in users:
            UserExperienceFactory(
                user=user, is_current=True,
                start_date=self.jan_1, end_date=self.jan_31
            )

        for employee in users:
            # -- Profiling
            start_time = timezone.now()
            # initial_queries = len(connection.queries)

            payroll_config = self.get_payroll_config()

            appoint_date = self.jan_1
            from_date = self.jan_1
            to_date = self.jan_31

            package_1 = PackageUtil(org).create_package()
            # package slots
            salary_package = [
                {
                    "package": package_1,
                    "from_date": self.jan_1,
                    "to_date": self.jan_31,
                    "applicable_from": self.jan_1
                }
            ]

            slot_days = 31
            worked_days = 28

            def get_worked_days(*args, **kwargs):
                # s = args[0]
                return worked_days, slot_days

            payroll = self.get_payroll(
                employee,
                appoint_date,
                payroll_config,
                from_date,
                to_date,
                salary_package,
                (slot_days, slot_days),
                get_worked_days_fn=get_worked_days
            )
            # Sanity Checks

            self.assertEqual(
                self._round_2(payroll.get_heading_amount_from_variable("BASIC_SALARY")),
                10000.00
            )

            self.assertEqual(
                self._round_2(payroll.get_heading_amount_from_variable("ALLOWANCE")),
                15000.00
            )

            self.assertEqual(
                self._round_2(payroll.get_heading_amount_from_variable("TOTAL_ADDITION")),
                22580.65
            )

            self.assertEqual(
                self._round_2(payroll.get_heading_amount_from_variable("PF")),
                903.23
            )

            self.assertEqual(
                self._round_2(payroll.get_heading_amount_from_variable("SSF")),
                903.23
            )

            self.assertEqual(
                self._round_2(payroll.get_heading_amount_from_variable("TOTAL_DEDUCTION")),
                1806.46
            )

            self.assertEqual(
                self._round_2(payroll.get_heading_amount_from_variable("TOTAL_SALARY")),
                20774.19
            )

            self.assertEqual(
                self._round_2(payroll.get_heading_amount_from_variable(
                    "TOTAL_ANNUAL_GROSS_SALARY"
                )), 273774.19
            )

            self.assertEqual(
                self._round_2(payroll.get_heading_amount_from_variable("TAX")),
                2281.45
            )

            self.assertEqual(
                self._round_2(payroll.get_heading_amount_from_variable("CASH_IN_HAND")),
                18492.74
            )
            execution_speeds.append(
                self._round_2((timezone.now() - start_time).total_seconds() * 100)
            )

        print(
            'Payroll Calculator Execution times: ',
            execution_speeds
        )
