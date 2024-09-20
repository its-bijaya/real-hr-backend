from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.organization.models import EmailNotificationSetting
from irhrs.users.models import UserEmailUnsubscribe
from django.urls import reverse

BIRTHDAY_EMAIL, ANNIVERSARY_EMAIL = 1,2

class TestUserEmailSettingOnHRsAction(RHRSAPITestCase):
    organization_name = "Organization"
    users = [
        ("admin@email.com", "admin", "Male"),
        ("user@email.com", "user", "Female"),
    ]

    @property
    def user_url(self):
        return reverse(
            "api_v1:users:user-email-setting-list",
            kwargs={"user_id": self.user.id}
        )

    @property
    def hr_url(self):
        return reverse(
            "api_v1:organization:email-setting-list",
            kwargs={"organization_slug": self.organization.slug}
        )

    @staticmethod
    def get_payload(send_email=False, allow_unsubscribe=False):
        return {"email_settings": [
            {"email_type": 1, "send_email": send_email, "allow_unsubscribe": allow_unsubscribe},
            {"email_type": 2, "send_email": send_email, "allow_unsubscribe": allow_unsubscribe}
        ]}

    def setUp(self):
        super().setUp()
        self.user = self.created_users[1]

        for email_type in [BIRTHDAY_EMAIL, ANNIVERSARY_EMAIL]:
            EmailNotificationSetting.objects.create(
                organization=self.organization,
                email_type=email_type,
                send_email=False,
                allow_unsubscribe=False
            )
            UserEmailUnsubscribe.objects.create(
                user=self.user,
                email_type=email_type
            )

    def post_email_settings(self, payload):
        self.client.force_login(self.admin)
        response = self.client.post(self.hr_url, payload, format="json")
        self.assertEqual(response.status_code, 201)

    @staticmethod
    def get_email_settings_list_from_response(response):
        email_settings_list = response.json()["results"].values()
        email_settings = []
        for emails in email_settings_list:
            email_settings.extend(emails)
        return email_settings

    def test_send_email_true_and_subscribable_false(self):
        """
        expected output: user's unsubscribed emails should now be zero.
        send_email = True for both emails and allow_unsubscribe is False

        allow_unsubscribe is false so users unsubscribable email should be deleted
        """
        self.assertEqual(self.user.unsubscribed_emails.count(), 2)
        self.post_email_settings(self.get_payload(send_email=True, allow_unsubscribe=False))
        self.assertEqual(self.user.unsubscribed_emails.count(), 0)

        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, 200)
        email_settings = self.get_email_settings_list_from_response(response)

        valid_emails = [
            email for email in email_settings
            if email["send_email"] and not email["allow_unsubscribe"]
        ]
        self.assertEqual(len(valid_emails), 2)

    def test_send_email_true_and_subscribable_true(self):
        """
        expected output:
        send_email = False for both emails since allow_unsubscribe is True
        and both emails have been unsubscribed by user in setUp

        Unsubscribed emails shouldn't be affected. So unsubscribable email count
        should be same before and after the post request.
        """
        self.assertEqual(self.user.unsubscribed_emails.count(), 2)
        self.post_email_settings(self.get_payload(send_email=True, allow_unsubscribe=True))
        self.assertEqual(self.user.unsubscribed_emails.count(), 2)

        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, 200)
        email_settings = self.get_email_settings_list_from_response(response)

        valid_emails = [
            email for email in email_settings
            if not email["send_email"] and email["allow_unsubscribe"]
        ]
        self.assertEqual(len(valid_emails), 2)

    def check_when_send_email_is_false(self):
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, 200)
        email_settings = self.get_email_settings_list_from_response(response)
        self.assertEqual(email_settings, [])

    def test_send_email_false_allow_unsubscribe_false(self):
        """
        expected output:
        both email settings won't be present in json response.
        so email settings when flattened with truthy values should receive empty array.

        allow_unsubscribe is false so users unsubscribable email should be deleted
        """
        self.assertEqual(self.user.unsubscribed_emails.count(), 2)
        self.post_email_settings(
            self.get_payload(
                send_email=False,
                allow_unsubscribe=False
            )
        )
        self.assertEqual(self.user.unsubscribed_emails.count(), 0)
        self.check_when_send_email_is_false()

    def test_send_email_false_allow_unsubscribe_true(self):
        """
        expected output:
        both email settings won't be present in json response.
        so email settings when flattened with truthy values should receive empty array.

        allow_unsubscribe is true so users unsubscribed_emails shouldn't be affected.
        """
        self.assertEqual(self.user.unsubscribed_emails.count(), 2)
        self.post_email_settings(
            self.get_payload(
                send_email=False,
                allow_unsubscribe=True
            )
        )
        self.assertEqual(self.user.unsubscribed_emails.count(), 2)
        self.check_when_send_email_is_false()

