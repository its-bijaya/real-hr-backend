from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.constants.organization import BIRTHDAY_EMAIL, ANNIVERSARY_EMAIL, HOLIDAY_EMAIL
from irhrs.organization.models import EmailNotificationSetting
from irhrs.users.models import UserEmailUnsubscribe


class UserNotificationSettingTestCase(RHRSAPITestCase):
    users = (
        ('admin@email.com', 'passwd', 'Male'),
        ('userone@email.com', 'passwd', 'Male'),
        ('usertwo@email.com', 'passwd', 'Male')
    )
    organization_name = 'Organization'

    def setUp(self):
        super().setUp()
        EmailNotificationSetting.objects.create(
            organization=self.organization,
            email_type=BIRTHDAY_EMAIL,
            send_email=True,
            allow_unsubscribe=True
        )
        EmailNotificationSetting.objects.create(
            organization=self.organization,
            email_type=ANNIVERSARY_EMAIL,
            send_email=True,
            allow_unsubscribe=False
        )
        EmailNotificationSetting.objects.create(
            organization=self.organization,
            email_type=HOLIDAY_EMAIL,
            send_email=False,
            allow_unsubscribe=True
        )

    def test_list(self):
        url = reverse(
            'api_v1:users:user-email-setting-list',
            kwargs={
                'user_id': self.created_users[1].id
            }
        )

        for case, user in [
            ("admin", self.admin),
            ("user", self.created_users[1]),
            ("outsider", self.created_users[2])
        ]:
            with self.atomicSubTest(msg=case):
                self.client.force_login(user)

                response = self.client.get(url)
                if case == "outsider":
                    self.assertEqual(response.status_code, 403, response.data)
                    continue

                self.assertEqual(response.status_code, 200, response.data)
                # 2 as send_email=false in org will not be visible

                self.assertEqual(response.data.get('results').get('hris')[0]['email_type'], BIRTHDAY_EMAIL)
                self.assertTrue(response.data.get('results').get('hris')[0]['send_email'])
                self.assertEqual(response.data.get('results').get('hris')[1]['email_type'], ANNIVERSARY_EMAIL)
                self.assertTrue(response.data.get('results').get('hris')[1]['send_email'])

                # lets unsubscribe from one
                UserEmailUnsubscribe.objects.create(user=self.created_users[1], email_type=BIRTHDAY_EMAIL)

                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, response.data)

                self.assertEqual(response.data.get('results').get('hris')[0]['email_type'], BIRTHDAY_EMAIL)
                self.assertFalse(response.data.get('results').get('hris')[0]['send_email'])
                self.assertEqual(response.data.get('results').get('hris')[1]['email_type'], ANNIVERSARY_EMAIL)
                self.assertTrue(response.data.get('results').get('hris')[1]['send_email'])

    def test_valid_unsubscribe(self):
        payload = {
            "email_settings": [
                {
                    "email_type": BIRTHDAY_EMAIL,
                    "send_email": False,
                }
            ]
        }

        url = reverse(
            'api_v1:users:user-email-setting-list',
            kwargs={
                'user_id': self.created_users[1].id
            }
        )

        for case, user in [
            ("admin", self.admin),
            ("user", self.created_users[1]),
            ("outsider", self.created_users[2])
        ]:
            with self.atomicSubTest(msg=case):

                self.client.force_login(user)

                response = self.client.post(url, payload, format='json')
                if case == "outsider":
                    self.assertEqual(response.status_code, 403)
                else:
                    self.assertEqual(response.status_code, 201, response.data)

                    self.assertTrue(
                        UserEmailUnsubscribe.objects.filter(
                            user=self.created_users[1],
                            email_type=BIRTHDAY_EMAIL
                        ).exists()
                    )

    def test_try_to_unsubscribe_whose_can_unsubscribe_is_false(self):
        self.client.force_login(self.admin)
        payload = {
            "email_settings": [{
                "email_type": ANNIVERSARY_EMAIL,
                "send_email": False,
            }]
        }

        url = reverse('api_v1:users:user-email-setting-list', kwargs={
                'user_id': self.created_users[1].id
        })

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(
            response.data['email_settings'][0],
            {'send_email': ['You are not allowed to unsubscribe this email.']}
        )

    def try_to_unsubscribe_whose_send_email_is_disabled_in_organization(self):
        self.client.force_login(self.admin)
        payload = {
            "email_settings": [{
                "email_type": HOLIDAY_EMAIL,
                "send_email": False,
            }]
        }

        url = reverse('api_v1:users:user-email-setting-list', kwargs={
            'user_id': self.created_users[1].id
        })

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(
            response.data['email_settings'][0],
            {'send_email': ['Invalid email type.']}
        )
