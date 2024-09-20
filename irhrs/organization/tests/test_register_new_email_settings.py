from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.common.management.commands.register_new_email_settings import Command
from django.core.management import call_command
from irhrs.core.constants.organization import EMAIL_TYPE_CHOICES
from irhrs.organization.models.settings import EmailNotificationSetting


class TestNewRegisteredEmails(RHRSAPITestCase):
    email_types = [email_type for email_type, _ in EMAIL_TYPE_CHOICES if email_type] 
    organization_name = "Organization"
    users = [("admin@email.com", "admin", "Male")]

    def setUp(self):
        super().setUp()
        EmailNotificationSetting.objects.bulk_create(
            [
                EmailNotificationSetting(
                    organization=self.organization, 
                    email_type=email_type,
                    send_email=True,
                    allow_unsubscribe=False,
                )
                for email_type in self.email_types
            ]
        )

    def test_new_registered_emails_with_no_new_email_type_choices(self):
        self.assertFalse(Command.get_new_email_types(self.organization))

    def test_new_registered_emails(self):
        deleted_email = EmailNotificationSetting.objects.last()
        deleted_email.delete()
        call_command('register_new_email_settings', self.organization.slug, '--no-color')
        self.assertTrue(
            EmailNotificationSetting.objects.filter(
                email_type=deleted_email.email_type
            ).exists()
        )

