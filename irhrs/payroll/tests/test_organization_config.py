from unittest.mock import patch

from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils import nested_get
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory


class OrganizationPayrollConfigTest(RHRSAPITestCase):
    users = [('hr@email.com', 'secret', 'Male')]
    organization_name = 'Organization'

    def setUp(self):
        super().setUp()

        self.fiscal_year = FiscalYearFactory(organization=self.organization)
        self.url = reverse('api_v1:payroll:payroll-config-detail', kwargs={
            'organization__slug': self.organization.slug
        })

    def test_create_organization_config(self):
        self.client.force_login(user=self.admin)
        data = {
            'start_fiscal_year': self.fiscal_year.id,
            "include_holiday_offday_in_calculation": False,
            "enable_unit_of_work": True,
        }

        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, 200)

        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, 200)

        self.assertEqual(nested_get(get_response.data, 'start_fiscal_year.id'), self.fiscal_year.id)
        self.assertEqual(get_response.data.get('include_holiday_offday_in_calculation'),
                         data.get('include_holiday_offday_in_calculation'))
        self.assertEqual(
            get_response.data.get('enable_unit_of_work'),
            data.get('enable_unit_of_work')
        )

    def test_validate_payroll_already_generated_editing_fiscal_year(self):
        self.client.force_login(user=self.admin)
        data = {
            'start_fiscal_year': self.fiscal_year.id,
            "include_holiday_offday_in_calculation": False,
            "enable_unit_of_work": True,
        }

        with patch(
            'irhrs.payroll.api.v1.serializers.'
            'OrganizationPayrollConfigUpdateSerializer.is_organization_payroll_generated',
            return_value=True
        ):
            response = self.client.patch(self.url, data)
            self.assertEqual(response.status_code, 400)
            self.assertIn('start_fiscal_year', response.data)

            # now try with removing fiscal year, it should be allowed to update
            data.pop('start_fiscal_year')
            response = self.client.patch(self.url, data)
            self.assertEqual(response.status_code, 200)

    def test_adding_fiscal_year_from_different_organization(self):
        self.client.force_login(user=self.admin)
        data = {
            'start_fiscal_year': FiscalYearFactory().id,
            "include_holiday_offday_in_calculation": False,
            "enable_unit_of_work": True,
        }

        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('start_fiscal_year', response.data)

