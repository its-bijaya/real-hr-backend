import json
from unittest.mock import patch
from django.forms.utils import pretty_name
from datetime import date
from django.urls import reverse
from irhrs.core.utils.common import get_today, DummyObject
from django.utils import timezone
from irhrs.payroll.tests.utils import PackageUtil
from irhrs.organization.models import (
    Organization, OrganizationDivision,
    UserOrganization, EmploymentJobTitle
)

from irhrs.payroll.api.v1.serializers import HeadingSerializer

from irhrs.organization.models import (
    FiscalYear,
    FiscalYearMonth
)
from irhrs.payroll.models import (
    HH_OVERTIME,
    Payroll,
    COMPLETED,
    CONFIRMED,
    SSFReportSetting,
    Heading,
    DisbursementReportSetting,
    UserExperiencePackageSlot,
    OrganizationPayrollConfig
)
from django.contrib.auth.models import Group
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.tests.utils import (
    FakeManager,
    FakeModel
)
from irhrs.payroll.utils.calculator import (
    EmployeeSalaryCalculator
)
from irhrs.payroll.utils.datework.date_helpers import DateWork
from irhrs.users.models import User, UserDetail
from irhrs.users.utils import get_default_date_of_birth

from irhrs.permission.constants.groups import ADMIN

from irhrs.users.models.experience import UserExperience

from irhrs.payroll.utils.payroll_behaviour_test_helper import PayrollBehaviourTestBaseClass

from irhrs.payroll.tests.factory import BackdatedCalculationFactory


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


class TestBackdatedIncomeAdjustmentInSameMonth(
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

    payroll_mocked_settings = dict(
        ADJUST_TAX_CHANGE_DUE_TO_EXTRA_ADDITION_DEDUCTION_IN_SAME_MONTH=True
    )

    def create_packages(self):
        package_util = ExtraEarningTaxAdjustmentPackageUtil(
            organization=self.organization
        )

        self.headings = package_util.get_headings()

        package = package_util.create_package()
        return package

    def test_adjust_backdated_income_in_upcoming_payroll(self):

        for heading in self.headings:
            mocked_values = {
                'Addition': 2000,
                'Deduction': 1000
            }

            BackdatedCalculationFactory(
                heading=heading,
                package_slot=UserExperiencePackageSlot.objects.get(
                    user_experience__user=self.created_users[0]
                ),
                previous_amount=0,
                current_amount=mocked_values.get(heading.name, 0)
            )

            payrolls_inputs = [
                (
                    date(2017, 1, 1),
                    date(2017, 1, 31)
                ),
                (
                    date(2017, 2, 1),
                    date(2017, 2, 28)
                ),
                (
                    date(2017, 3, 1),
                    date(2017, 3, 31)
                )
            ]

        expected_tax_amounts = [200, 100, 100]

        payrolls_results = list()

        for payroll_input in payrolls_inputs:
            with self.settings(
                ADJUST_TAX_CHANGE_DUE_TO_EXTRA_ADDITION_DEDUCTION_IN_SAME_MONTH=True
            ):
                _, calculator = self.get_payroll(
                    *payroll_input, self.created_users[0]
                )

            payrolls_results.append(calculator.payroll)

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
