import functools
from typing import Callable
from unittest.mock import patch
from datetime import date

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today, DummyObject
from irhrs.core.tests.utils import FakeManager, FakeModel
from irhrs.payroll.tests.utils import PackageUtil, SimplePackageUtil
from irhrs.payroll.utils.calculator import EmployeeSalaryCalculator
from irhrs.payroll.utils.datework.date_helpers import DateWork


class FakeHeading(DummyObject):
    pass


class FakePackageHeading(FakeModel):
    def __init__(self, **kwargs):
        self.heading = FakeHeading()
        super().__init__(**kwargs)


class FakeSalaryPackage(DummyObject):

    @property
    def package_headings(self):
        return FakeManager(faked_class=FakePackageHeading)


class FakeUserExperience(FakeModel):
    pass


class FakeUserContact(FakeModel):
    pass


class FakeEmployee(FakeModel):

    def first_date_range_user_experiences(self, start_date, end_date):
        return FakeUserExperience(current_step=1)

    @property
    def detail(self):
        return FakeEmployeeDetail(
            user=self,
            gender=getattr(self, 'd_gender', 'Male'),
            joined_date=getattr(self, 'd_joined_date', get_today()),
            organization=getattr(self, 'd_organization', None),
            nationality=getattr(self, 'd_nationality', None)
        )

    @property
    def payroll_increments(self):
        return FakeManager(faked_class=FakePayrollIncrements, return_count=0)

    @property
    def contacts(self):
        return FakeManager(FakeUserContact)


class FakePayrollIncrements(FakeModel):
    pass


class FakeEmployeeDetail(FakeModel):
    pass


class FakeOrganizationPayrollConfig(FakeModel):
    pass


class TestCalculator(RHRSAPITestCase):

    organization_name = 'Test'
    users = [('admin@example.com', 'password', 'Male')]

    @property
    def _round_2(self):
        return functools.partial(round, ndigits=2)

    @property
    def datework(self):
        return DateWork(
            fiscal_year_start_month_date=(1, 1)  # set start of fiscal year to jan 1
        )

    @property
    def jan_1(self):
        return date(year=get_today().year, month=1, day=1)

    @property
    def jan_15(self):
        return date(year=get_today().year, month=1, day=15)

    @property
    def jan_16(self):
        return date(year=get_today().year, month=1, day=16)

    @property
    def jan_31(self):
        return date(year=get_today().year, month=1, day=31)


    def get_payroll_config(self, **kwargs):
        return FakeOrganizationPayrollConfig(**kwargs)

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
        paid_tax=0,
        get_worked_days_fn : Callable =None
    ):

        with patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_organization',
            return_value=self.organization
        ), patch(
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
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_taxable_amount_from_entry',
            return_value=previous_taxable_amount
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_paid_tax',
            return_value=paid_tax
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

    def test_general_package(self):
        """
        Case: All days present, Full salary of a month
        """
        payroll_config = self.get_payroll_config()
        employee = FakeEmployee(
            marital_status="Single",
            d_organization=self.organization,
            d_nationality="Nepalese"
        )
        year = get_today().year
        from_date = date(year, 1, 1)
        to_date = date(year, 1, 31)
        appoint_date = from_date

        previous_taxable_amount = 0
        rebate_amount = 0
        paid_tax = 0

        package_util = PackageUtil(organization=self.organization)

        basic_salary = 10000
        allowance = 15000
        total_addition = basic_salary + allowance
        pf = 0.10 * basic_salary
        ssf = 0.10 * basic_salary
        total_deduction = pf + ssf
        total_salary = total_addition - total_deduction

        annual_taxable = (total_salary * 12)
        annual_tax = 0.1 * annual_taxable
        this_month_tax = annual_tax / 12

        working_days = (30, 30)  # working days in month, in slot
        worked_days = (30, 30)  # actual_worked_days, working_days in month

        expected_result = {
            '__BASIC_SALARY__': basic_salary,
            '__ALLOWANCE__': allowance,
            '__TOTAL_ADDITION__': total_addition,
            '__PF__': pf,
            '__SSF__': ssf,
            '__TOTAL_DEDUCTION__': total_deduction,
            '__TOTAL_SALARY__': total_salary,
            '__TAX__': this_month_tax
        }

        package = package_util.create_package()
        payroll = self.get_payroll(
            employee,
            appoint_date,
            payroll_config,
            from_date,
            to_date,
            package,
            working_days,
            worked_days,
            previous_taxable_amount,
            rebate_amount,
            paid_tax
        )

        for heading_variable, expected_value in expected_result.items():
            value = payroll.get_heading_amount_from_variable(heading_variable)
            self.assertEqual(
                value,
                expected_value,
                f"{heading_variable} not as expected."
            )

    def test_monthly_addition_deduction(self):
        """
        Case: 20 days present out of 30 days
        """
        payroll_config = self.get_payroll_config()
        employee = FakeEmployee(
            marital_status="Single",
            d_organization=self.organization,
            d_nationality="Nepalese"
        )
        year = get_today().year
        from_date = date(year, 1, 1)
        to_date = date(year, 1, 31)
        appoint_date = from_date

        working_days = (30, 30)  # working days in month, in slot
        worked_days = (20, 30)  # actual_worked_days, month working days

        package_util = PackageUtil(organization=self.organization)
        package = package_util.create_package()

        payroll = self.get_payroll(
            employee,
            appoint_date,
            payroll_config,
            from_date,
            to_date,
            package,
            working_days,
            worked_days
        )

        basic_salary = 10000
        allowance = 15000
        total_addition = round((basic_salary + allowance) * (20/30), 2)
        pf = round((0.10 * basic_salary) * (20/30), 2)
        ssf = round((0.10 * basic_salary) * (20/30), 2)
        total_deduction = round(pf + ssf, 2)
        total_salary = round(total_addition - total_deduction, 2)

        expected_result = {
            '__BASIC_SALARY__': basic_salary,
            '__ALLOWANCE__': allowance,
            '__TOTAL_ADDITION__': total_addition,
            '__PF__': pf,
            '__SSF__': ssf,
            '__TOTAL_DEDUCTION__': total_deduction,
            '__TOTAL_SALARY__': total_salary
        }

        for heading_variable, expected_value in expected_result.items():
            value = payroll.get_heading_amount_from_variable(heading_variable)
            self.assertEqual(
                value,
                expected_value,
            )

    def test_payroll_generation_with_multiple_package_with_addition_and_deduction_only(self):
        payroll_config = self.get_payroll_config()
        employee = FakeEmployee(
            marital_status="Single",
            d_organization=self.organization,
            d_nationality="Nepalese"
        )

        appoint_date = self.jan_1
        from_date = self.jan_1
        to_date = self.jan_31

        package_1 = SimplePackageUtil(
            organization=self.organization,
            addition=10000,
            deduction=500
        ).create_package()

        package_2 = SimplePackageUtil(
            organization=self.organization,
            addition=20000,
            deduction=600
        ).create_package()

        # package slots
        salary_package = [
            {
                "package": package_1,
                "from_date": self.jan_1,
                "to_date": self.jan_15,
                "applicable_from": self.jan_1
            },
            {
                "package": package_2,
                "from_date": self.jan_16,
                "to_date": self.jan_31,
                "applicable_from": self.jan_1
            }
        ]

        slot_days = 31

        worked_days_first = 15
        expected_addition_first = 10000 * (worked_days_first / slot_days)
        expected_deduction_first = 500 * (worked_days_first / slot_days)

        worked_days_second = 16
        expected_addition_second = 20000 * (worked_days_second/slot_days)
        expected_deduction_second = 600 * (worked_days_second/slot_days)

        expected_addition_of_the_month = self._round_2(
            self._round_2(expected_addition_first) + self._round_2(expected_addition_second)
        )
        expected_deduction_of_the_month = self._round_2(
            self._round_2(expected_deduction_first) + self._round_2(expected_deduction_second)
        )

        ags = (expected_addition_of_the_month - expected_deduction_of_the_month) + \
              (20000 - 600) * 11
        annual_tax = 0.1 * ags
        monthly_tax = self._round_2(annual_tax / 12)

        def get_worked_days(*args, **kwargs):
            s = args[0]
            if s.from_date == self.jan_1 and s.to_date == self.jan_15:
                return worked_days_first, slot_days
            else:
                return worked_days_second, slot_days

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

        self.assertEqual(
            payroll.get_heading_amount_from_variable('__ADDITION__'),
            expected_addition_of_the_month,
            f"addition {payroll.get_heading_amount_from_variable('__ADDITION__'),}"
        )
        self.assertEqual(
            payroll.get_heading_amount_from_variable('__DEDUCTION__'),
            expected_deduction_of_the_month,
            f"deduction {payroll.get_heading_amount_from_variable('__DEDUCTION__'),}"
        )

        self.assertEqual(
            payroll.get_heading_amount_from_variable('__TAX__'),
            monthly_tax,
            "TAX"
        )

    def test_payroll_generation_with_multiple_package_with_type1_constants_used_in_addition(self):
        payroll_config = self.get_payroll_config()
        employee = FakeEmployee(
            marital_status="Single",
            d_organization=self.organization,
            d_nationality="Nepalese"
        )

        appoint_date = self.jan_1
        from_date = self.jan_1
        to_date = self.jan_31

        util = PackageUtil(
            organization=self.organization,
            basic_salary_rule=['5000'],
            allowance_rule=['0']
        )
        package_1 = util.create_package()

        util.basic_salary_rule = ['10000']
        util.allowance_rule = ['20000']
        package_2 = util.create_package()

        total_addition_1 = 5000
        pf_1 = 0.10*5000
        ssf_1 = 0.10*5000

        total_addition_2 = 10000 + 20000
        pf_2 = 0.10*10000
        ssf_2 = 0.10*10000

        expected_total_addition = self._round_2(total_addition_1 * 15/31) +\
            self._round_2(total_addition_2 * 16/31)
        expected_pf = self._round_2(pf_1 * 15/31) + self._round_2(pf_2 * 16/31)
        expected_ssf = self._round_2(ssf_1 * 15/31) + self._round_2(ssf_2 * 16/31)
        expected_total_deduction = self._round_2(expected_pf + expected_ssf)

        # package slots
        salary_package = [
            {
                "package": package_1,
                "from_date": self.jan_1,
                "to_date": self.jan_15,
                "applicable_from": self.jan_1
            },
            {
                "package": package_2,
                "from_date": self.jan_16,
                "to_date": self.jan_31,
                "applicable_from": self.jan_1
            }
        ]

        slot_days = 31

        def get_worked_days(*args, **kwargs):
            s = args[0]
            if s.from_date == self.jan_1 and s.to_date == self.jan_15:
                return 15, slot_days
            else:
                return 16, slot_days

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

        self.assertEqual(
            payroll.get_heading_amount_from_variable('__TOTAL_ADDITION__'),
            expected_total_addition,
            f"total addition {payroll.get_heading_amount_from_variable('__TOTAL_ADDITION__'),}"
        )
        self.assertEqual(
            payroll.get_heading_amount_from_variable('__PF__'),
            expected_pf,
        )
        self.assertEqual(
            payroll.get_heading_amount_from_variable('__SSF__'),
            expected_ssf
        )

        self.assertEqual(
            payroll.get_heading_amount_from_variable('__TOTAL_DEDUCTION__'),
            expected_total_deduction
        )
