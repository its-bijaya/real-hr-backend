from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import LeaveRequestFactory


class TestLeaveByAge(RHRSTestCaseWithExperience):
    users = [
        ("admin@email.com", "pass", "Female", "HR"),
        ("normal@email.com", "normal", "Female", "Intern"),
        ("developer@gmail.com", "password", "Male", "Developer"),
    ]
    organization_name = "Aayu"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.leave_request1 = LeaveRequestFactory(
            user=self.created_users[1],
            recipient=self.admin,
            start="2021-10-01",
            end="2021-10-01",
            balance=1,
            status="Approved",

        )
        user1_detail = self.created_users[1].detail
        user1_detail.date_of_birth = get_today() - timezone.timedelta(days=365 * 20)
        user1_detail.save()

        self.leave_request2 = LeaveRequestFactory(
            user=self.created_users[2],
            recipient=self.admin,
            start="2021-10-01",
            end="2021-10-01",
            balance=1,
            status="Approved",
        )
        user2_detail = self.created_users[2].detail
        user2_detail.date_of_birth = get_today() - timezone.timedelta(days=365 * 55)
        user2_detail.save()
       
    def test_leave_report_by_age(self):
        url1 = (
            reverse(
                "api_v1:leave:on-leave-users-list",
                kwargs={"organization_slug": self.organization.slug},
            )
            + "?age_group=18-25"
        )

        response = self.client.get(url1, format="json")
        
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )

        self.assertEqual(
            response.json().get('count'), 1
        )

        self.assertEqual(
            response.json().get("results")[0].get("count_leaves"), 1
        )

        self.assertEqual(
            response.json().get("results")[0].get("full_name"), 
            self.created_users[1].full_name
        )

        url2 = (
            reverse(
                "api_v1:leave:on-leave-users-list",
                kwargs={
                    'organization_slug': self.organization.slug
                },
            ) + "?age_group=50-60"
        )

        response = self.client.get(url2, format='json')
        
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )

        self.assertEqual(
            response.json().get('count'), 1
        )

        self.assertEqual(
            response.json().get("results")[0].get("count_leaves"), 1
        )

        self.assertEqual(
            response.json().get('results')[0].get('full_name'),
            self.created_users[2].full_name
        )
