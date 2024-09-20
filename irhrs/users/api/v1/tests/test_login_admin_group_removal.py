from irhrs.common.api.tests.common import BaseTestCase as TestCase

from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from irhrs.permission.constants.groups import ADMIN
from irhrs.users.api.v1.tests.factory import UserFactory


class TestLoginAdmin(TestCase):
    client = APIClient()

    @property
    def obtain_access_url(self):
        return reverse(
            'api_v1:jwt:obtain'
        )

    def _test_no_admin_login(self):
        user = UserFactory(
            is_active=True,
            is_blocked=False
        )
        user.set_password('password')
        user.save()
        user.groups.clear()
        response = self.client.post(
            self.obtain_access_url,
            data={
                'username': user.email,
                'password': 'password'
            }
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'User with No Experience and no admin must not get login.'
        )
        self.assertEqual(
            response.json().get('non_field_errors')[0],
            'Unable to login with given credentials.'
        )

    def _test_admin_login(self):
        user = UserFactory(
            is_active=True,
            is_blocked=False
        )
        user.set_password('password')
        user.save()

        user.groups.add(Group.objects.get(name=ADMIN))

        response = self.client.post(
            self.obtain_access_url,
            data={
                'username': user.email,
                'password': 'password'
            }
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'User with No Experience and but is an admin must get login.'
        )
        self.assertIn(
            'access', response.json()
        )
        self.assertIn(
            'refresh', response.json()
        )

    def _test_admin_removal(self):
        user = UserFactory(
            is_active=True,
            is_blocked=False
        )
        user.set_password('password')
        user.save()
        user.groups.add(
            Group.objects.get(name=ADMIN)
        )
        access_key = self.client.post(
            self.obtain_access_url,
            data={
                'username': user.email,
                'password': 'password'
            }
        ).json().get('access')
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + access_key
        )
        resp = self.client.get(
            '/api/v1/users/me/',
        )

        # The user is admin to this point.
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK
        )

        user.groups.clear()
        # The user is no longer an admin at this point.
        resp = self.client.get(
            '/api/v1/users/me/',
        )
        self.assertEqual(
            resp.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
