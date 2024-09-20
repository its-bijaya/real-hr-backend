from unittest.mock import patch

from datetime import date

from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils import nested_get
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory

from irhrs.payroll.models import (
    Heading,
    MonthlyTaxReportSetting,
    HH_OVERTIME
)

from irhrs.payroll.models.payslip_report_setting import (
    EMPLOYMENT_INCOME,
    LESS_ALLOWABLE_DEDUCTION
)

from irhrs.payroll.tests.utils import PackageUtil

from rest_framework.test import APIClient

from rest_framework import status

from irhrs.payroll.tests.factory import ConfirmedPayrollFactory

from irhrs.organization.models import (
    FiscalYear,
    FiscalYearMonth
)


class PayslipWithYearlyProjetion(PackageUtil):
    RULE_CONFIG = {
        'addition':  {
            'rules': ['10000'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        },

        'yearly_addition':  {
            'rules': ['100'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Yearly', 'taxable': True,
            'absent_days_impact': False
        },

        'overtime': {
            'rules': ['0'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Hourly', 'taxable': True, 'absent_days_impact': False,
            'hourly_heading_source': f'{HH_OVERTIME}'
        },

        'daily_allowance': {
            'rules': ['0'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Daily', 'taxable': True, 'deduct_amount_on_leave': False,
            'pay_when_present_holiday_offday': False, 'absent_days_impact': False,
            'deduct_amount_on_remote_work': False
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
        'type_one':  {
            'rules': ['0'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Type1Cnst',
            'duration_unit': 'Monthly'
        },
        'type_two':  {
            'rules': ['0'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst'
        }

    }


class MonthlyTaxReportSettingTest(RHRSAPITestCase):
    users = [('hr@email.com', 'secret', 'Male')]
    organization_name = 'Organization'

    def setup_payroll(self):
        self.employee = self.created_users[0]
        self.package = self.create_package()

        fiscal_year = FiscalYear.objects.create(
            organization=self.organization,
            name="Test Fiscal Year",
            start_at=date(2017, 1, 1),
            end_at=date(2017, 12, 31),
            applicable_from=date(2017, 1, 1),
            applicable_to=date(2017, 12, 31)
        )

        fiscal_year_month_slots = [
            dict(
                start=date(2017, 1, 1),
                end=date(2017, 1, 31)
            ),
            dict(
                start=date(2017, 2, 1),
                end=date(2017, 2, 28)
            ),
            dict(
                start=date(2017, 3, 1),
                end=date(2017, 3, 31)
            ),
            dict(
                start=date(2017, 4, 1),
                end=date(2017, 4, 30)
            ),
            dict(
                start=date(2017, 5, 1),
                end=date(2017, 5, 31)
            ),
            dict(
                start=date(2017, 6, 1),
                end=date(2017, 6, 30)
            ),
            dict(
                start=date(2017, 7, 1),
                end=date(2017, 7, 31)
            ),
            dict(
                start=date(2017, 8, 1),
                end=date(2017, 8, 31)
            ),
            dict(
                start=date(2017, 9, 1),
                end=date(2017, 9, 30)
            ),
            dict(
                start=date(2017, 10, 1),
                end=date(2017, 10, 31)
            ),
            dict(
                start=date(2017, 11, 1),
                end=date(2017, 11, 30)
            ),
            dict(
                start=date(2017, 12, 1),
                end=date(2017, 12, 31)
            )
        ]

        fy_months_args = [
            FiscalYearMonth(
                fiscal_year=fiscal_year,
                month_index=i + 1,
                display_name=f"Month-{i + 1}",
                start_at=fiscal_year_month_slots[i].get('start'),
                end_at=fiscal_year_month_slots[i].get('end')
            ) for i in range(12)
        ]

        FiscalYearMonth.objects.bulk_create(fy_months_args)


        created_payrolls = [
            ConfirmedPayrollFactory(
                organization=self.organization,
                from_date=date_range.get('start'),
                to_date=date_range.get('end'),
                employee_payrolls__employee=self.employee,
                employee_payrolls__package=self.package,
                employee_payrolls__report_rows_from_date=date_range.get('start'),
                employee_payrolls__report_rows_to_date=date_range.get('end'),
                employee_payrolls__report_rows_headings=self.headings
            ) for date_range in fiscal_year_month_slots[:3]
        ]

        self.report_url = reverse(
            'api_v1:payroll:payslip-monthly-tax-report',
            kwargs={
                'payroll_id': created_payrolls[-1].id,
                'user_id': self.employee.id
            }
        )

    def create_package(self):
        package_util = PayslipWithYearlyProjetion(
            organization=self.organization
        )

        package = package_util.create_package()

        self.headings = package_util.get_headings()

        return package

    def setUp(self):
        super().setUp()
        # TODO @wrufesh test api permission as well
        self.client.force_login(user=self.admin)
        self.url = reverse(
            'api_v1:payroll:tax-report-settings-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

        self.setup_payroll()

        self.created_headings_ids = [
            heading.id for heading in self.headings
        ]

    def test_monthly_tax_report_setting(self):
        patch_data_1 = dict(
            category=EMPLOYMENT_INCOME,
            headings=[
                dict(
                    heading=heading_id,
                    is_highlighted=True
                ) for heading_id in self.created_headings_ids[:3]
            ]
        )

        patch_data_2 = dict(
            category=LESS_ALLOWABLE_DEDUCTION,
            headings=[
                dict(
                    heading=heading_id,
                    is_highlighted=True
                ) for heading_id in self.created_headings_ids[3:6]
            ]
        )
        patch_data_3 = dict(
            category=EMPLOYMENT_INCOME,
            headings=[
                dict(
                    heading=heading_id,
                    is_highlighted=True
                ) for heading_id in self.created_headings_ids[6:8]
            ]
        )

        res = self.client.post(
            self.url,
            {'settings': [patch_data_1, patch_data_2]},
            format='json'
        )

        self.assertEquals(res.status_code, status.HTTP_200_OK)

        res = self.client.post(
            self.url,
            {'settings': [patch_data_1, patch_data_3, patch_data_2]},
            format='json'
        )

        self.assertEquals(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.client.get(self.report_url)

        self.assertEquals(res.status_code, status.HTTP_200_OK)

        # Test when no settings configured

        MonthlyTaxReportSetting.objects.all().delete()

        res = self.client.get(self.report_url)

        self.assertEquals(res.status_code, status.HTTP_400_BAD_REQUEST)
