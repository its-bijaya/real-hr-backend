from datetime import timedelta

from django.urls import reverse
from rest_framework import status

from irhrs.payroll.tests.utils import PackageUtil
from irhrs.payroll.models import PackageHeading, Package, Heading
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.payroll.tests.factory import OrganizationPayrollConfigFactory
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory


class PackageUtilWithExtraAddition(PackageUtil):
    RULE_CONFIG = {
        'allowance': {'rules': ['15000'], 'payroll_setting_type': 'Salary Structure',
                      'type': 'Type1Cnst', 'duration_unit': 'Monthly', 'taxable': None,
                      'absent_days_impact': None},
        'extra_addition_allowance': {'rules': ['__ALLOWANCE__ + 2000'],
                                     'payroll_setting_type': 'Fringe Benefits', 'type': 'Extra Addition',
                                     'duration_unit': 'Monthly', 'taxable': True},
        'extra_addition_allowance_one': {'rules': ['__ALLOWANCE__ + 2000'],
                                     'payroll_setting_type': 'Fringe Benefits', 'type': 'Extra Addition',
                                     'duration_unit': 'Monthly', 'taxable': True},
        'taxable_tax_deduction': {'rules': ['2000'], 'payroll_setting_type': 'Salary TDS',
                                  'type': 'Tax Deduction', 'duration_unit': None, 'taxable': None,
                                  'absent_days_impact': None},
    }


class PackageOrderTest(RHRSTestCaseWithExperience):
    users = [('hr@email.com', 'secret', 'Male', 'Programmer')]
    organization_name = 'Organization'

    def setUp(self):
        super().setUp()
        self.fiscal_year = FiscalYearFactory(organization=self.organization,
                                             applicable_from=get_today() - timedelta(days=60))
        self.client.force_login(self.admin)
        package_util = PackageUtilWithExtraAddition(organization=self.organization)
        self.package = package_util.create_package()
        OrganizationPayrollConfigFactory(
            start_fiscal_year=self.fiscal_year,
            organization=self.organization
        )
        self.today = get_today()

    @property
    def switch_package_heading_order_url(self):
        return reverse(
            "api_v1:payroll:packageheading-switch-order"
        ) + f'?as=hr&package__organization__slug={self.organization.slug}'

    @property
    def switch_heading_order_url(self):
        return reverse(
            "api_v1:payroll:heading-switch-order"
        ) + f'?organization__slug={self.organization.slug}'

    def test_taxable_after_tax_deduction_on_package_heading_throws_error(self):
        extra_addition_taxable_heading = PackageHeading.objects.filter(
            taxable=True,
            type="Extra Addition"
        ).first()
        taxable_deduction_heading = PackageHeading.objects.filter(
            type="Tax Deduction"
        ).first()


        payload = {
            "from_obj_order": extra_addition_taxable_heading.order,
            "to_obj_order": taxable_deduction_heading.order,
            "organization__slug": self.organization.slug,
            "package_id": extra_addition_taxable_heading.package.id
        }
        res = self.client.post(
            self.switch_package_heading_order_url,
            payload
        )
        self.assertEqual(
            res.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(res.json().get("success"), False)


    def test_taxable_after_tax_deduction_on_heading_throws_error(self):
        extra_addition_taxable_heading = Heading.objects.filter(
            taxable=True,
            type="Extra Addition"
        ).first()
        taxable_deduction_heading = Heading.objects.filter(
            type="Tax Deduction"
        ).first()

        payload = {
            "from_obj_order": extra_addition_taxable_heading.order,
            "to_obj_order": taxable_deduction_heading.order,
            "organization__slug": self.organization.slug,
        }
        res = self.client.post(
            self.switch_heading_order_url,
            payload
        )
        self.assertEqual(
            res.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(res.json().get("detail"), 'Sorting is not successful.')
