from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import LeaveRequestFactory


class TestLeaveByMonth(RHRSTestCaseWithExperience):
    users = [
        ('admin@email.com', 'password', 'Female', 'HR'),
        ('normal@email.com', 'password', 'Male', 'Developer')
    ]
    organization_name = 'Google'

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.leave_request = LeaveRequestFactory(
            user=self.created_users[1],
            recipient=self.admin,
            start="2021-11-01",
            end="2021-11-01",
            balance=1,
            status="Approved"
        )

    def test_leave_by_month(self):
        url = reverse(
            'api_v1:leave:by-month-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        ) + f"?year=2021"
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        expected_result = {
            '0': 0.0,
            '1': 0.0,
            '2': 0.0,
            '3': 0.0,
            '4': 0.0,
            '5': 0.0,
            '6': 0.0,
            '7': 0.0,
            '8': 0.0,
            '9': 0.0,
            '10': 1.0,
            '11': 0.0
        }
        expected_leave_for_gender = {
            'male': 1.0,
            'female': 0.0,
            'other': 0.0
        }
        self.assertEqual(
            expected_result,
            response.json().get('results')
        )

        response.json().pop('results')
        self.assertEqual(
            expected_leave_for_gender,
            response.json()
        )

        url = reverse(
            'api_v1:leave:on-leave-users-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        ) + "?month=10&year=2021"

        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('results')[0].get('num_leaves'),
            1
        )
        self.assertEqual(
            response.json().get('results')[0].get('count_leaves'),
            1
        )
