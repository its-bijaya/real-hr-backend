from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.core import mail
from django.test import override_settings
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.hris.tasks.resignation import send_resignation_no_action_taken_email
from irhrs.users.models import UserSupervisor
from irhrs.hris.api.v1.tests.factory import (
    ResignationApprovalSettingFactory,
    UserResignationFactory
)


def can_send_email(user, email_type):
    return True


class TestResignationEmail(RHRSTestCaseWithExperience):
    users = [("test@example.com", "secretThingIsHere", "Male", "Manager"),
             ("testone@example.com", "secretThingIsHere", "Female", "Programmer"),
             ("testtwo@example.com", "secretThingIsHere", "Female", "Programmer"),
             ]
    organization_name = "Organization"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123

    def setUp(self) -> None:
        super().setUp()
        self.user1 = self.created_users[1]
        ResignationApprovalSettingFactory(
            organization=self.organization,
            employee=self.user1
        )
        UserSupervisor.objects.create(
            authority_order=1,
            user=self.user1,
            supervisor=self.admin
        )

    @property
    def send_resignation_request_url(self):
        url = reverse(
            'api_v1:hris:user-resignation-list',
            kwargs={'organization_slug': self.organization.slug}
        )
        return url

    @property
    def send_resignation_data(self):
        payload = {
            "release_date": get_today() + timedelta(days=2),
            "reason": "I am retiring",
            "remarks": "yahooooooo"
        }
        return payload

    def test_send_resignation_request_email(self):
        self.client.force_login(self.user1)

        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.post(
                self.send_resignation_request_url,
                data=self.send_resignation_data,
                format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        mail_instance = mail.outbox[0]

        self.assertEqual(mail_instance.to, [self.admin.email])
        self.assertEqual(mail_instance.subject, "New resignation request.")
        self.assertEqual(
            mail_instance.body,
            f"{self.user1.full_name} sent resignation request."
        )

    def deny_resignation_request_url(self, kwargs):
        url = reverse(
            'api_v1:hris:user-resignation-deny',
            kwargs=kwargs
        )
        return url

    @property
    def resignation_deny_data(self):
        payload = {
            "remarks": "byee"
        }
        return payload

    def test_send_resignation_approved_denied_email(self):
        user_resignation = UserResignationFactory(
            employee=self.user1,
            recipient=self.admin,
        )
        kwargs = {
            'organization_slug': self.organization.slug,
            'pk': user_resignation.id
        }
        deny_url = self.deny_resignation_request_url(kwargs) + "?as=hr"
        self.client.force_login(self.admin)
        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.post(
                deny_url,
                data=self.resignation_deny_data,
                format="json"
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        mail_instance = mail.outbox[0]

        self.assertEqual(mail_instance.to, [self.created_users[1].email])
        self.assertEqual(mail_instance.subject, "Resignation request denied.")
        self.assertEqual(
            mail_instance.body,
            f"{self.admin.full_name} has denied your resignation request."
        )

    @override_settings(RESIGNATION_REQUEST_INACTION_EMAIL_AFTER_DAYS=2)
    def test_send_resignation_no_action_taken_email(self):
        user_resignation = UserResignationFactory(
            employee=self.user1,
            recipient=self.admin,
        )
        user_resignation.created_at = get_today(with_time=True) - timedelta(days=5)
        user_resignation.save()

        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            send_resignation_no_action_taken_email()

            self.assertEqual(len(mail.outbox), 1)
            mail_instance = mail.outbox[0]

            self.assertEqual(mail_instance.to, [self.admin.email])
            self.assertEqual(mail_instance.subject, "Resignations requests require action.")
            self.assertEqual(
                mail_instance.body,
                "The following resignations are pending:<br>"
                f"{self.user1.full_name} (Since 5 days.)"
            )
