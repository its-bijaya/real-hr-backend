from django.conf import settings

from irhrs.hris.models.resignation import UserResignation
from irhrs.organization.models import Holiday, Organization
from irhrs.core.utils.common import get_today
from irhrs.core.constants.organization import RESIGNATION_REMINDER_EMAIL
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.constants.payroll import REQUESTED, PENDING, CANCELED
from irhrs.core.utils import email
from irhrs.core.utils.email import send_notification_email
from irhrs.hris.constants import resignation_email_permissions


def send_resignation_no_action_taken_email():
    today = get_today()
    message = (
        "The following resignations are pending:"
    )
    for organization in Organization.objects.all():
        pending_resignations = []
        recipient_objects = [
            user for user in get_users_list_from_permissions(resignation_email_permissions, organization)
        ]
        settings_enabled_recipients = list(
            filter(
                lambda user: email.can_send_email(user, RESIGNATION_REMINDER_EMAIL),
                recipient_objects
            ),
        )
        settings_enabled_recipient_objects = [
            user for user in recipient_objects
        ]
        recipients = [user.email for user in settings_enabled_recipient_objects]
        inaction_threshold = getattr(settings, 'RESIGNATION_REQUEST_INACTION_EMAIL_AFTER_DAYS', 15)

        subject = "Resignations requests require action."
        pending_user_resignations = UserResignation.objects.filter(
            status=REQUESTED,
            employee__detail__organization=organization
        )
        for resignation in pending_user_resignations:
            employee = resignation.employee
            can_send_email = email.can_send_email(employee, RESIGNATION_REMINDER_EMAIL)
            pending_since = (today - resignation.created_at.date()).days
            inaction_threshold_crossed = pending_since >= inaction_threshold
            if (
                    can_send_email and \
                    inaction_threshold_crossed
            ):
                day_or_days = "days" if pending_since >= 1 else "day"
                pending_user = f"<br>{resignation.employee.full_name} (Since {pending_since} {day_or_days}.)"
                pending_resignations.append(pending_user)

        email_body = message + "".join(pending_resignations)

        for recipient in settings_enabled_recipient_objects:
            email_already_sent = email.has_sent_email(
                recipient=recipient, notification_text=email_body, subject=subject
            )

            if pending_resignations and not email_already_sent:
                send_notification_email(
                    recipients=recipients,
                    subject=subject,
                    notification_text=email_body
                )
