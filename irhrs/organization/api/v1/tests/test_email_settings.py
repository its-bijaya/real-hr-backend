from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.constants.organization import BIRTHDAY_EMAIL, ANNIVERSARY_EMAIL, EMAIL_TYPE_CHOICES
from irhrs.organization.models import EmailNotificationSetting


class OrganizationEmailSettingTestCase(RHRSAPITestCase):
    users = (
        ('admin@email.com', 'passwd', 'Male'),
    )
    organization_name = 'Organization'

    def test_email_settings_bulk_update(self):
        payload = {
            "email_settings": [
                {
                    "email_type": BIRTHDAY_EMAIL,
                    "send_email": True,
                    "allow_unsubscribe": False
                }
            ]
        }
        url = reverse(
            'api_v1:organization:email-setting-list',
            kwargs={'organization_slug': self.organization.slug}
        )

        self.client.force_login(self.admin)
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)

        self.assertTrue(
            EmailNotificationSetting.objects.filter(
                organization=self.organization,
                email_type=BIRTHDAY_EMAIL,
                send_email=True,
                allow_unsubscribe=False
            ).exists(),
            EmailNotificationSetting.objects.all()
        )

        # setting them to false
        payload = {
            "email_settings": [
                {
                    "email_type": BIRTHDAY_EMAIL,
                    "send_email": False,
                    "allow_unsubscribe": True
                }
            ]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)

        self.assertTrue(
            EmailNotificationSetting.objects.filter(
                organization=self.organization,
                email_type=BIRTHDAY_EMAIL,
                send_email=False,
                allow_unsubscribe=True
            ).exists(),
            EmailNotificationSetting.objects.all()
        )

    def test_list(self):
        EmailNotificationSetting.objects.create(
            organization=self.organization,
            email_type=BIRTHDAY_EMAIL,
            send_email=True,
            allow_unsubscribe=False
        )
        EmailNotificationSetting.objects.create(
            organization=self.organization,
            email_type=ANNIVERSARY_EMAIL,
            send_email=False,
            allow_unsubscribe=False
        )
        url = reverse(
            'api_v1:organization:email-setting-list',
            kwargs={'organization_slug': self.organization.slug}
        )

        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)

        self.assertEqual(
            response.data.get('results').get('hris')[0].get('email_type'),
            BIRTHDAY_EMAIL
        )
        self.assertTrue(
            response.data.get('results').get('hris')[0].get('send_email'),
        )
        self.assertFalse(
            response.data.get('results').get('hris')[0].get('allow_unsubscribe'),
        )

        self.assertEqual(
            response.data.get('results').get('hris')[1].get('email_type'),
            ANNIVERSARY_EMAIL
        )
        self.assertFalse(
            response.data.get('results').get('hris')[1].get('send_email')
        )
        self.assertFalse(
            response.data.get('results').get('hris')[0].get('allow_unsubscribe'),
        )

    def test_reset(self):
        url = reverse(
            'api_v1:organization:email-setting-list',
            kwargs={'organization_slug': self.organization.slug}
        )
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)

        reset_url = reverse(
            'api_v1:organization:email-setting-reset',
            kwargs={'organization_slug': self.organization.slug}
        )
        response = self.client.post(reset_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        hris_count = len(response.data.get('results').get('hris'))
        event_count = len(response.data.get('results').get('event'))
        training_count = len(response.data.get('results').get('training'))
        assessment_count = len(response.data.get('results').get('assessment'))
        expense_management_count = len(response.data.get('results').get('expense_management'))
        attendance_count = len(response.data.get('results').get('attendance'))
        payroll_count = len(response.data.get('results').get('payroll'))


        self.assertEqual(
            hris_count,
            7
        )
        self.assertEqual(
            event_count,
            3
        )
        self.assertEqual(
            training_count,
            5
        )
        self.assertEqual(
            assessment_count,
            2
        )
        self.assertEqual(
            expense_management_count,
            6
        )
        self.assertEqual(
            attendance_count,
            16
        )
        self.assertEqual(
            payroll_count,
            10
        )
        self.assertEqual(
            hris_count + event_count + training_count +
            assessment_count + expense_management_count +
            + attendance_count + payroll_count,
            len(EMAIL_TYPE_CHOICES)
        )
