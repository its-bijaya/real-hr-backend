import re

from django.conf import settings
from django.core.management import BaseCommand

from irhrs.common.models import NotificationTemplate, NotificationTemplateContent
from irhrs.core.constants.common import OVERTIME_EMAIL, ABSENT_EMAIL, \
    LATE_IN_EMAIL, LEAVE_EMAIL, WEEKLY_ATTENDANCE_REPORT_EMAIL
from irhrs.organization.models import NotificationTemplateMap, Organization


class Command(BaseCommand):
    help = "Initial Data for Notification templates"

    late_email = """Dear {{user}},

        Your Punch In for {{date}} has been recorded as late by {{late_duration}}.

        Your shift starts at {{expected_punch_in}} but you arrived at {{actual_punch_in}}.

        Regards,

        Human Resources Department
        """

    absent_email = """Dear {{user}},

        Your Attendance for {{date}} has been recorded as absent.

        Regards,

        Human Resources Department
        """

    weekly_attendance_report_email = """Dear {{user}},

            Your Weekly Attendance from {{date}} has been recorded as below.

            Regards,

            Human Resources Department
            """

    overtime_email = """Dear {{user}},

        Your overtime claim for date {{date}} has been generated as {{ot_hours}} hours.

        Claim your OT before it expires.

        Regards,

        Human Resources Department
        """

    leave_email_range = """Dear {{user}},

        Your leave from {{start_date}} till {{end_date}} has been {{status}}.

        Regards,

        Human Resources Department

        """

    def handle(self, *args, **options):
        if 'irhrs.attendance' not in settings.INSTALLED_APPS:
            print('Failed to seed Data as Module is not installed.')
            exit(0)

        seeder_templates = [
            {
                'name': 'Late In Email',
                'type': LATE_IN_EMAIL,
                'content': self.late_email,
                'description': ''
            },
            {
                'name': 'Absent Email',
                'type': ABSENT_EMAIL,
                'content': self.absent_email,
                'description': ''
            },
            {
                'name': 'Weekly Attendance Report Email',
                'type': WEEKLY_ATTENDANCE_REPORT_EMAIL,
                'content': self.weekly_attendance_report_email,
                'description': ''
            },
            {
                'name': 'Overtime Email',
                'type': OVERTIME_EMAIL,
                'content': self.overtime_email,
                'description': ''
            },
            {
                'name': 'Leave Email',
                'type': LEAVE_EMAIL,
                'content': self.leave_email_range,
                'description': ''
            }
        ]
        for template_content in seeder_templates:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Generating Template for "
                    f"{template_content.get('name')}")
            )
            content = template_content.pop('content', '')
            content = re.sub(
                '\n',
                '<br/>',
                re.sub(
                    ' {2,}',
                    ' ',
                    content
                )
            )
            template, created = NotificationTemplate.objects.get_or_create(
                **template_content,
            )
            if created:
                notification_content = NotificationTemplateContent.objects.create(template=template,content=content)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created Template for {template_content.get('name')}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Template for {template_content.get('name')} exists."
                    )
                )
        templates = list()
        for org in Organization.objects.all():
            predefined_template_names = (
                (LATE_IN_EMAIL, 'Late In Email',),
                (ABSENT_EMAIL, 'Absent Email',),
                (OVERTIME_EMAIL, 'Overtime Email',),
                (LEAVE_EMAIL, 'Leave Email'),
                (WEEKLY_ATTENDANCE_REPORT_EMAIL, 'Weekly Attendance Report Email'),
            )
            for notification_for, selection in predefined_template_names:
                templates = NotificationTemplate.objects.filter(
                    name=selection,
                    type=notification_for
                )
                for template in templates:
                    _, created = NotificationTemplateMap.objects.get_or_create(
                        organization=org,
                        template=template
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Mapped template for {template.name}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed map for {template.name} as already exists."
                            )
                        )
