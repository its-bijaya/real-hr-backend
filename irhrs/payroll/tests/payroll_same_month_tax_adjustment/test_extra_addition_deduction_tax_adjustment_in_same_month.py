from unittest.mock import patch
from datetime import date
from irhrs.core.utils.common import get_today
from irhrs.payroll.tests.utils import PackageUtil


from irhrs.payroll.models import (
    HH_OVERTIME,
    Payroll,
    CONFIRMED,
    Heading
)


from irhrs.payroll.utils.calculator import (
    EmployeeSalaryCalculator
)
from irhrs.payroll.utils.datework.date_helpers import DateWork

from irhrs.payroll.utils.payroll_behaviour_test_helper import PayrollBehaviourTestBaseClass

class ExtraEarningTaxAdjustmentPackageUtil(PackageUtil):
    RULE_CONFIG = {
        'addition':  {
            'rules': ['2000'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        },
        'deduction': {
            'rules': ['1000'],
            'payroll_setting_type': 'Social Security Fund', 'type': 'Deduction',
            'duration_unit': 'Monthly', 'taxable': False,
            'absent_days_impact': True
        },
        'overtime': {
            'rules': ['100'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Hourly', 'taxable': True, 'absent_days_impact': False,
            'hourly_heading_source': f'{HH_OVERTIME}'
        },
        'extra_addition_one': {
            'rules': ['0'],
            'payroll_setting_type': 'Fringe Benefits', 'type': 'Extra Addition',
            'duration_unit': None, 'taxable': True, 'absent_days_impact': None
        },
        'extra_deduction_two': {
            'rules': ['0'],
            'payroll_setting_type': 'Expense Settlement', 'type': 'Extra Deduction',
            'duration_unit': None, 'taxable': False, 'absent_days_impact': None
        },
        'total_annual_gross_salary': {
            'rules': ['__ANNUAL_GROSS_SALARY__'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
            'duration_unit': 'Monthly', 'taxable': None, 'absent_days_impact': None
        },
        'tax': {
            'rules': ['0.10 * __TOTAL_ANNUAL_GROSS_SALARY__'],
            'payroll_setting_type': 'Salary TDS',
            'type': 'Tax Deduction', 'duration_unit': None,
            'taxable': None,
            'absent_days_impact': None
        }
    }


class TestExtraAdditionDeductionTaxAdjustmentInSameMonth(
    PayrollBehaviourTestBaseClass
):

    organization_name = 'Test'

    user_experience_package_slot_start_date = date(2017, 1, 1)
    user_experience_start_date = date(2017, 1, 1)

    users = [
        dict(
            email='employee@example.com',
            password='password',
            user_experience_start_date=date(2017, 1, 1),
            detail=dict(
                gender='Male',
                joined_date=get_today()
            )
        )
    ]

    def create_packages(self):
        package_util = ExtraEarningTaxAdjustmentPackageUtil(
            organization=self.organization
        )
        package = package_util.create_package()
        return package

    def test_extra_addition_deduction_tax_adjustment_in_same_month(self):

        extra_addition_one_id = Heading.objects.get(
            name='Extra addition one').id
        extra_deduction_two_id = Heading.objects.get(
            name='Extra deduction two').id

        payrolls_inputs = [
            (
                date(2017, 1, 1),
                date(2017, 1, 31),
                0
            ),
            (
                date(2017, 2, 1),
                date(2017, 2, 28),
                5,
                {
                    str(extra_addition_one_id): dict(value=1000),
                    str(extra_deduction_two_id): dict(value=500)
                }
            ),
            (
                date(2017, 3, 1),
                date(2017, 3, 31),
                0
            )
        ]

        expected_tax_amounts = [100, 200, 100]

        payrolls_results = list()

        for payroll_input in payrolls_inputs:
            calculator_employee_payroll_instance = self.get_payroll(
                *payroll_input
            )

            payrolls_results.append(calculator_employee_payroll_instance)

        resulting_tax_amounts = list()

        tax_heading = Heading.objects.get(name='Tax')

        for result in payrolls_results:
            tax_amount = list(filter(
                lambda x: x.heading == tax_heading,
                result.rows
            ))[0].amount

            resulting_tax_amounts.append(tax_amount)

        self.assertEqual(resulting_tax_amounts, expected_tax_amounts)

    @property
    def datework(self):
        return DateWork(
            # set start of fiscal year to jan 1
            fiscal_year_start_month_date=(1, 1)
        )

    def get_payroll(self, from_date, to_date, hours_of_work, extra_headings=dict()):
        working_days = (30, 30)
        worked_days = (30, 30)

        with patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_organization',
            return_value=self.organization
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_hours_of_work',
            return_value=hours_of_work
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_working_days',
            return_value=working_days
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_worked_days',
            return_value=worked_days
        ):

            with self.settings(
                ADJUST_TAX_CHANGE_DUE_TO_EXTRA_ADDITION_DEDUCTION_IN_SAME_MONTH=True
            ):
                calculator = EmployeeSalaryCalculator(
                    employee=self.created_users[0],
                    datework=self.datework,
                    from_date=from_date,
                    to_date=to_date,
                    salary_package=self.user_packages[
                        self.created_users[0].id
                    ],
                    appoint_date=date(2017, 1, 1),
                    simulated_from=None,
                    extra_headings=extra_headings
                )

            payroll = self.create_payroll(from_date, to_date)

            calculator.payroll.record_to_model(payroll)

            return calculator.payroll

    def create_payroll(self, from_date, to_date):
        create_payroll = Payroll.objects.create(
            organization=self.organization,
            from_date=from_date,
            to_date=to_date,
            extra_data={}
        )
        create_payroll.status = CONFIRMED
        create_payroll.save()
        return create_payroll
