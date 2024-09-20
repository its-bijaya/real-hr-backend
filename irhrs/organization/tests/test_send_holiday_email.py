from unittest.mock import patch

from irhrs.common.api.tests.common import BaseTestCase
from django.core import mail
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import HolidayFactory
from irhrs.organization.tasks import send_holiday_email_notification
from irhrs.users.api.v1.tests.factory import UserFactory


class SendHolidayEmailTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.holiday = HolidayFactory(date=get_today())
        self.organization = self.holiday.organization
        self.user1 = UserFactory(_organization=self.organization)
        self.user2 = UserFactory(_organization=self.organization)

    def test_send_holiday_email(self):
        def can_send_email(user, email_type):
            if user == self.user1:
                return True
            else:
                return False

        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            send_holiday_email_notification()
            # Test that one message has been sent.
            self.assertEqual(len(mail.outbox), 1)
            mail_instance = mail.outbox[0]

            self.assertEqual(mail_instance.to, [self.user1.email])
            self.assertEqual(mail_instance.subject, "Holiday Notification")
            self.assertEqual(
                mail_instance.body,
                f"It is to inform you that there has been a holiday announced on"
                f" {self.holiday.date}(today) on the occasion of {self.holiday.name}."
            )
