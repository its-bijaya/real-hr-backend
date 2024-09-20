from datetime import timedelta

from rest_framework import status
from django.urls import reverse

from irhrs.core.utils.common import get_today
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.payroll.tests.test_payroll_reports import PayrollReportMixin
from irhrs.payroll.tests.factory import OverviewConfigFactory
from irhrs.payroll.models import SSFReportSetting, Heading, \
    DisbursementReportSetting

class TestPaySlip(PayrollReportMixin, RHRSAPITestCase):

    organization_name = 'Test'
    users = [('admin@example.com', 'password', 'Male')]

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )
        self.package = self.create_packages()
        self.cash_in_hand_heading = self.package.package_headings.filter(
            heading__name = "Cash in hand"
        ).first().heading
        self.employee_payroll = self.create_employee_payroll()

    def payslip_url(self, instance):
        return reverse(
            'api_v1:payroll:payslip-detail',
            kwargs = {
                'payroll_id': instance.id,
                'user_id': self.created_users[0].id
            }
        )

    def test_cash_in_hand_in_payslip_works(self):
        self.overview_config = OverviewConfigFactory(
            organization = self.organization,
            cash_in_hand = self.cash_in_hand_heading
        )
        response = self.client.get(self.payslip_url(self.employee_payroll.payroll))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()['masked_values']['cash_in_hand'],
            self.employee_payroll.report_rows.get(heading=self.cash_in_hand_heading).amount
        )

    def test_cash_in_hand_in_payslip_does_not_break(self):
        self.overview_config = OverviewConfigFactory(
            organization = self.organization,
            cash_in_hand = None
        )
        response = self.client.get(self.payslip_url(self.employee_payroll.payroll))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()['masked_values']['cash_in_hand'],
            None
        )
