"""@irhrs_docs"""
import logging
import re

import html5lib
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend

from irhrs.common.models.smtp_server import SMTPServer
from irhrs.common.models.system_email_log import SystemEmailLog
from irhrs.core.constants.common import FAILED, SENT
from django.conf import settings

logger = logging.getLogger(__name__)


def custom_mail(
    subject, message, from_email, recipient_list,
    fail_silently=False, auth_user=None, auth_password=None,
    connection=None, html_message=None
):
    if re.search('<[a-z]+>.*</[a-z]>', message):
        message = '\n'.join(
            html5lib.parseFragment(message).itertext()
        ).replace('\xa0', '\n')

    # from_email is now always defaulted to 'EMAIL_HOST_USER'
    from_email = get_default_email()
    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=fail_silently,
            auth_user=auth_user,
            auth_password=auth_password,
            connection=connection,
            html_message=html_message
        )
        email_status = SENT
    except Exception:
        email_status = FAILED
    logged_emails = set()
    for recipient in get_user_model().objects.filter(email__in=recipient_list):
        SystemEmailLog.objects.create(
            user=recipient,
            subject=subject,
            status=email_status,
            sent_address=recipient.email,
            text_message=message,
            html_message=html_message or ''
        )
        logged_emails.add(recipient.email)

    failed = set(recipient_list) - logged_emails
    # @Ravi refactor this
    if failed:
        logger.warning(
            "Email was sent but users were not found in database: {}".format(
                ','.join(failed)
            )
        )
        return False
    else:
        return True


def get_default_email():
    smtp_server = SMTPServer.objects.first()
    return smtp_server.username if smtp_server else settings.DEFAULT_FROM_EMAIL


class CustomEmailBackend(EmailBackend):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        email_instance = SMTPServer.objects.first()
        if email_instance:
            self.host = email_instance.host
            self.port = email_instance.port
            self.username = email_instance.username
            self.password = email_instance.password
            self.use_tls = email_instance.use_tls
            self.use_ssl = email_instance.use_ssl
            if self.use_ssl and self.use_tls:
                raise ValueError(
                    "EMAIL_USE_TLS/EMAIL_USE_SSL are mutually exclusive, so only set "
                    "one of those settings to True.")
            self.connection = None
