from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status


from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models import UserExperience

User = get_user_model()


class TestSupervisorAction(RHRSTestCaseWithExperience):
    users = [
        ('test@example.com', 'helloSecretWorld', 'Male', 'Programmer'),
        ('userone@example.com', 'helloSecretWorld', 'Female', 'Programmer'),
        ('usertwo@example.com', 'helloSecretWorld', 'Male', 'Programmer'),
        ('userthreee@example.com', 'helloSecretWorld', 'Female', 'Programmer'),
        ('userfour@example.com', 'helloSecretWorld', 'Male', 'UI/UX'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )

    @property
    def url(self):
        return reverse(
            'api_v1:hris:email-setting-list',
            kwargs={'organization_slug': self.organization.slug}
        )

    @property
    def post_url(self):
        return reverse(
            'api_v1:hris:email-setting-create-setting',
            kwargs={'organization_slug': self.organization.slug}
        )

    def payload(self):
        return {
            "user": [
                self.created_users[0].id, self.created_users[1].id, self.created_users[2].id,
                self.created_users[3].id, self.created_users[4].id
            ],
            "leave": True
        }

    def test_email_setting(self):
        response = self.client.post(
            self.post_url,
            data={
                "user": [],
                "leave": False
            }
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('user'),
            []
        )
        response = self.client.post(
            self.post_url,
            self.payload(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        expected_result = [
            self.created_users[0].id, self.created_users[1].id, self.created_users[2].id,
            self.created_users[3].id, self.created_users[4].id
        ]
        self.assertEqual(
            set(response.json().get('user')),
            set(expected_result)
        )

        UserExperience.objects.filter(user=self.created_users[4]).first().delete()
        response = self.client.post(
            self.post_url,
            self.payload(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json().get('user'),
            [f'Invalid pk "{self.created_users[4].id}" - object does not exist.']
        )

        response = self.client.get(
            self.url,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), 4)


