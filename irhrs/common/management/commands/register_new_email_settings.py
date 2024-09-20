from django.core.management.base import BaseCommand, CommandError
from irhrs.core.constants.organization import EMAIL_TYPE_CHOICES
from irhrs.organization.models.organization import Organization
from irhrs.organization.models.settings import EmailNotificationSetting


class Command(BaseCommand):
    help = 'Register new email settings for organization with specified organization slug'

    def add_arguments(self, parser):
        parser.add_argument(
            'organization_slug',
            help="""organization slug of the organization for which email is
            to be registered eg: python manage.py register_new_email_settings twitter
            """,
            type=str
        )

    @staticmethod
    def get_new_email_types(organization: Organization) -> set:
        email_settings_type = EmailNotificationSetting.objects.filter(
            organization=organization
        ).values_list('email_type', flat=True)

        new_email_settings_type = (
            {email_type for email_type, _ in EMAIL_TYPE_CHOICES} -  
            set(email_settings_type)
        )
        return new_email_settings_type

    def create_new_emails(self, organization: Organization):
        new_email_settings_type = self.get_new_email_types(organization)
        if not new_email_settings_type:
            self.stdout.write("No new email settings to be registered")
            return 

        new_email_settings = EmailNotificationSetting.objects.bulk_create(
            [
                EmailNotificationSetting(
                    organization=organization,
                    email_type=email_type
                )
                for email_type in new_email_settings_type
            ] 
        )
        self.stdout.write(self.style.SUCCESS(
            f'Successfully registered {len(new_email_settings)} '
            f'new email settings for {organization}'
        ))

    def handle(self, *args, **options):
        organization_slug = options['organization_slug']
        try:
            organization = Organization.objects.get(slug=organization_slug)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization with the slug {organization_slug} does not exist')

        self.create_new_emails(organization)

        

