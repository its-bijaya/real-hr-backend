from os import path
from django.urls import reverse
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.payroll.constants import YEARLY, MONTHLY
from irhrs.payroll.tests.factory import RebateSettingFactory
from rest_framework import status


class TestUserVoluntaryRebateRequestAmount(RHRSAPITestCase):
    organization_name = "aayu"

    users = [
        ("admin@gmail.com", "admin", "Female"),
        ("user@gmail.com", "usser", "Female")
    ]

    def setUp(self):
        super().setUp()
        self.fiscal_year = FiscalYearFactory(organization=self.organization)
        self.rebate = RebateSettingFactory(organization=self.organization)

        self.url = reverse(
            "api_v1:payroll:payroll-user-voluntary-rebates-list",
            kwargs={
                "organization_slug": self.organization.slug
            }
        ) + f"?as=hr"
        self.payload = {
            "rebate": self.rebate.id,
            "fiscal_year": self.fiscal_year.id,
            "user": self.created_users[1].id,
            "amount": 0,
            "description": "Yearly rebate request",
            "remarks": "Request rebate",
            "duration_unit": YEARLY,
            "title": "New request"
        }
        self.user_url = reverse(
            "api_v1:payroll:payroll-user-voluntary-rebates-new-create-request",
            kwargs={
                "organization_slug": self.organization.slug
            }
        )
        self.user_payload = {
            "rebate": self.rebate.id,
            "fiscal_year": self.fiscal_year.id,
            "amount": -5000,
            "description": "New request",
            "duration_unit": YEARLY,
            "title": "Negative request"
        }

    def test_rebate_amount_request_as_hr(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, self.payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get('non_field_errors'), ["Amount should be greater than Zero."]
        )
    
    def test_rebate_amount_limit_exceeeded_as_hr(self):
        self.client.force_login(self.admin)
        self.payload['amount'] = 25000
        response = self.client.post(self.url, self.payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get('non_field_errors'), ["Rebate amount limit exceeded."]
        )
    
    def test_rebate_amount_request_as_user(self):
        self.client.force_login(self.created_users[1])
        response = self.client.post(self.user_url, self.user_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.json().get("non_field_errors"), ["Amount should be greater than Zero."]
        )
    
    def test_rebate_amount_limit_exceeded_as_hr(self):
        self.client.force_login(self.created_users[1])
        self.user_payload["amount"] = 25250
        response = self.client.post(self.user_url, self.user_payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get("non_field_errors"), ["Rebate amount limit exceeded."]
        )
    
    def test_yearly_rebate_request_as_hr(self):
        self.client.force_login(self.admin)
        self.payload["amount"] = 2000
        response = self.client.post(self.url, self.payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.json()['status'], "Requested"
        )
        self.assertEqual(
            response.json()['amount'], 2000.0
        )
    
    def test_yearly_rebate_request_as_user(self):
        self.client.force_login(self.created_users[1])
        self.user_payload["amount"] = 4545
        response = self.client.post(self.user_url, self.user_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            response.json()['status'], "Requested"
        )
        self.assertEqual(
            response.json()["amount"], 4545.0
        )
