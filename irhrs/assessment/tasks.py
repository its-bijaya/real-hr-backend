from django.db.models.signals import post_delete
from django.dispatch import receiver

from irhrs.core.constants.organization import ASSESSMENT_ASSIGNED_UNASSIGNED_TO_USER_EMAIL
from irhrs.core.utils.email import send_notification_email
from irhrs.core.utils import email

def send_unassign_assessment_email(user_assessment):
    user = user_assessment.user
    subject = "Assessment was unassigned."
    message = (
        f"{user_assessment.assessment_set.title} assessment which "
        f"was previously assigned to you has been unassigned."
    )
    can_send_email = email.can_send_email(user, ASSESSMENT_ASSIGNED_UNASSIGNED_TO_USER_EMAIL)
    email_already_sent = email.has_sent_email(
            recipient=user,
            notification_text=message,
            subject=subject
    )
    if can_send_email and not email_already_sent:
        send_notification_email(
            recipients=[user.email],
            subject=subject,
            notification_text=message
        )
