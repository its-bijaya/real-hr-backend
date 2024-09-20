from datetime import timedelta


from irhrs.core.utils.common import get_today
from irhrs.payroll.utils.virtual_user_payroll import calculate_payroll
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.hris.api.v1.tests.factory import PreEmployementFactory
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.payroll.tests.factory import OrganizationPayrollConfigFactory
from irhrs.payroll.tests.test_payroll_reports import PayrollReportMixin
from irhrs.payroll.models import \
    DisbursementReportSetting

class TestNoEmployeeSalaryCalculator(PayrollReportMixin, RHRSAPITestCase):

    organization_name = 'Test'
    users = [('admin@example.com', 'password', 'Male')]

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )
        self.package = self.create_packages()
        self.virtual_employee = PreEmployementFactory(
            organization=self.organization,
            date_of_join=get_today() + timedelta(days=2),
            payroll=self.package
        )
        self.fiscal_year = FiscalYearFactory(
            organization=self.organization,
            start_at=get_today() - timedelta(days=1),
            end_at=get_today() + timedelta(days=365),
            applicable_from=get_today() - timedelta(days=1),
            applicable_to=get_today() + timedelta(days=360)
        )
        self.organization_payroll_config = OrganizationPayrollConfigFactory(
            start_fiscal_year=self.fiscal_year,
            organization=self.organization,
        )

    def test_no_employee_salary_calculator_returns_correct_result(self):
        calculation = calculate_payroll(self.virtual_employee)
        tax = list(
            filter(lambda x: x['package_name'] == 'Tax', calculation)
        )[0]['amount']
        cash_in_hand = list(
            filter(lambda x: x['package_name'] == 'Cash in hand', calculation)
        )[0]['amount']
        self.assertEqual(tax, 2300)
        self.assertEqual(cash_in_hand, 20700)
