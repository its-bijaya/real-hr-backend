from datetime import timedelta

from irhrs.common.api.tests.common import RHRSAPITestCase
from django.urls import reverse
from irhrs.core.utils.common import get_today, get_tomorrow

from irhrs.users.models import UserLegalInfo, ChangeRequest


class TestUserLegalInfo(RHRSAPITestCase):
    users = [("user@email.com", "hello", "Male")]
    organization_name = "Organization"

    @property
    def payload(self):
        return {
            "pan_number": "123123",
            "cit_number": "32617",
            "pf_number": "4123",
            "ssfid": "78912",
            "citizenship_number": "123123",
            "citizenship_issue_place": "Pokhara",
            "citizenship_issue_date": "2013-12-24",
            "passport_number": "1231231",
            "passport_issue_place": "Kathmandu",
            "passport_issue_date": "2014-12-24"
        }

    @property
    def get_url(self):
        return reverse(
            "api_v1:users:user-legal-info",
            kwargs={"user_id": self.admin.id}
        )

    def setUp(self):
        super().setUp()

    def test_get_user_legal_information(self):
        UserLegalInfo.objects.create(
            user=self.admin,
            **self.payload
        )
        self.client.force_login(self.admin)
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.payload)

    def test_post_user_legal_information_as_hr(self):
        self.client.force_login(self.admin)
        self.assertFalse(UserLegalInfo.objects.exists())
        response = self.client.put(self.get_url + "?as=hr", self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserLegalInfo.objects.exists())
        self.assertTrue(UserLegalInfo.objects.filter(**self.payload).exists())

    def test_bad_date_post_request(self):
        self.client.force_login(self.admin)
        self.assertFalse(UserLegalInfo.objects.exists())
        payload = self.payload
        payload["citizenship_issue_date"] = get_tomorrow().strftime("%Y-%m-%d")
        payload["passport_issue_date"] = get_tomorrow().strftime("%Y-%m-%d")
        response = self.client.put(self.get_url, payload)
        self.assertEqual(response.status_code, 400)
        error = {
            'citizenship_issue_date': ['The date must be a past date.'],
            'passport_issue_date': ['The date must be a past date.']
        }
        self.assertEqual(response.json(), error)

    def test_post_user_legal_information_as_user(self):
        self.client.force_login(self.admin)
        self.assertFalse(ChangeRequest.objects.exists())
        response = self.client.put(self.get_url, self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ChangeRequest.objects.exists())
        self.assertTrue(
            ChangeRequest.objects.filter(
                category='Legal Info',
                status='Pending'
            ).exists()
        )
