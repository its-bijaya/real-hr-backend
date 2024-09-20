from typing import Iterable, Union
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.template.loader import render_to_string

from irhrs.common.models import SystemEmailLog
from irhrs.core.utils.custom_mail import custom_mail
from irhrs.organization.models import Organization
from irhrs.leave.models import settings

User = get_user_model()


def is_email_setting_enabled_in_org(organization: Organization, email_type: int) -> bool:
    """check whether email setting is enabled or not in a organization"""
    enabled_in_organization = organization.email_settings.filter(
        email_type=email_type, send_email=True).exists()

    return enabled_in_organization


def can_send_email(user: User, email_type: int, organization: Organization = None) -> bool:
    """check notification setting to check whether send email or not"""
    if not user.is_active:
        return False
    if not organization:
        organization = user.detail.organization
    enabled_in_organization = organization.email_settings.filter(
        email_type=email_type, send_email=True).exists()
    unsubscribed = user.unsubscribed_emails.filter(email_type=email_type).exists()
    return enabled_in_organization and not unsubscribed


def send_notification_email(recipients, notification_text, subject="RealHRSoft Notification"):
    html_message = render_to_string(
        'notifications/notification_base.html',
        context={
            'message': notification_text
        }
    )
    info_email = getattr(settings, 'INFO_EMAIL', 'noreply@realhrsoft.com')

    custom_mail(
        subject=subject,
        message=notification_text,
        html_message=html_message,
        from_email=info_email,
        recipient_list=recipients
    )


def has_sent_email(recipient, notification_text, subject=None):
    fil = {
        'user': recipient,
        'text_message': notification_text
    }
    if subject:
        fil['subject'] = subject

    return SystemEmailLog.objects.filter(**fil).exists()


def send_email_as_per_settings(
    recipients: Union[User, Iterable[User]],
    subject: str,
    email_text: str,
    email_type: int,
    allow_duplicates: bool = True
) -> None:
    """send_email_as_per_setting

    :param recipients: User instance/queryset/list of id
    :param subject : Email Subject text
    :param email_text : Email body text
    :param email_type : type of email to be sent
    :param allow_duplicates : if true: can send duplicate email else cannot send.

    This method sends email.

    Cases for successful mail:
    - if allow duplicate is true else checks for duplicate email if duplicate cannot send mail
    - can_send_email true
    - email_recipients is true

    :return None when there is no recipient(s)

    """
    if not recipients:
        # if no recipients found do nothing.
        return
    if not (isinstance(recipients, (list, QuerySet))):
        recipients = [recipients]

    email_recipients = list()
    for recipient in recipients:
        if not allow_duplicates:
            duplicate_exists = has_sent_email(
                recipient=recipient,
                notification_text=email_text,
                subject=subject
            )
            if duplicate_exists:
                continue

        check_if_can_send_email = can_send_email(
            recipient,
            email_type
        )
        if check_if_can_send_email:
            email_recipients.append(recipient.email)
    if email_recipients:
        send_notification_email(
            recipients=email_recipients,
            subject=subject,
            notification_text=email_text
        )
