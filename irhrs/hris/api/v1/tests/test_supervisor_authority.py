from django.contrib.auth import get_user_model
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from django.urls import reverse
from irhrs.users.api.v1.tests.factory import UserFactory

USER = get_user_model()


class TestSupervisorAction(RHRSTestCaseWithExperience):
    users = [
        ('test@example.com', 'helloSecretWorld', 'Male', 'Programmer'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )
        self.user = UserFactory()
        self.supervisor1 = UserFactory()
        self.supervisor2 = UserFactory()
        self.supervisor3 = UserFactory()

    @property
    def url(self):
        return reverse(
            'api_v1:hris:user-supervisor-assign-list'
        )

    def payload(self):
        return {
            "user": self.user.id,
            "supervisors": [
                {
                    "user": self.user.id,
                    "supervisor": self.supervisor1.id,
                    "authority_order": 1,
                    "approve": True,
                    "forward": False,
                    "deny": False
                }
            ],
            "has_supervisor": True
        }

    def bad_payload(self):
        return {
            "user": self.user.id,
            "supervisors": [
                {
                    "user": self.user.id,
                    "supervisor": self.supervisor1.id,
                    "authority_order": 1,
                    "approve": True,
                    "forward": False
                }
            ],
            "has_supervisor": True
        }

    # Test Scenario:
    # 1. If valid data are provided, user should be assigned with Supervisor
    # 2. If approve/forward/deny field is not sent, user should not be assigned with Supervisor

    # Write test cases for other test scenario if needed.

    def test_assign_supervisors(self):
        url = self.url + '?organization_slug={}'.format(self.organization.slug)
        response = self.client.post(
            url,
            self.payload(),
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            str(response.json())
        )

        bad_response = self.client.post(
            url,
            self.bad_payload(),
            format='json'
        )
        self.assertEqual(
            bad_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            str(response.json())
        )
        self.assertEqual(
            bad_response.json().get('deny'),
            ['This field may not be blank.']
        )

class TestBulkSupervisorAssign(RHRSTestCaseWithExperience):
    organization_name = "Google"
    users = [
        ('test@example.com', 'helloSecretWorld', 'Male', 'Programmer'),
        ("user@example.com", "user", "Male", "intern"),
        ("hello@example.com", "hello", "Female", "intern"),
        ("anish@example.com", "first", "Male", "manager"),
    ]

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def bulk_url(self):
        return reverse(
            'api_v1:hris:user-supervisor-assign-bulk-assign'
        )
    
    def payload(self):
        return {
            'user': [user.id for user in self.created_users[1:]],
            'ignore_first_level_authority_change':False,
            'ignore_second_level_authority_change':False,
            'ignore_third_level_authority_change':False,
            "supervisors": [
                {
                    "supervisor": self.created_users[0].id,
                    "authority_order": 1,
                    "approve": True,
                    "forward": False,
                    "deny": False
                }
            ],
            "has_supervisor": True
        }
    def bad_payload(self):
        return {
            'user': [user.id for user in self.created_users[1:4]],
            'ignore_first_level_authority_change':False,
            'ignore_second_level_authority_change':False,
            'ignore_third_level_authority_change':False,
             "supervisors": [
                {
                    "supervisor": self.created_users[0].id,
                    "authority_order": 1,
                    "approve": True,
                    "forward": False
                }
            ],
            "has_supervisor": True
        }
    
    def test_bulk_assign_supervisors(self):
        url = self.bulk_url() + '?organization_slug={}'.format(self.organization.slug)
        response = self.client.post(
            url,
            self.payload(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.json(),
            'Supervisor assigned successfully.'
        )

        bad_response = self.client.post(
            url,
            self.bad_payload(),
            format = 'json'
        )
        self.assertEqual(
            bad_response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            bad_response.json()[0].get('deny'),
            ['This field may not be blank.']
        )
