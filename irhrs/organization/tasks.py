from irhrs.core.constants.organization import HOLIDAY_EMAIL
from irhrs.core.utils.common import get_today
from irhrs.core.utils import email
from irhrs.core.utils.email import send_notification_email
from irhrs.organization.models import Holiday


def send_holiday_email_notification():
    today = get_today()
    for holiday in Holiday.objects.filter(date=today):
        recipients = []
        subject = "Holiday Notification"
        message = (
            f"It is to inform you that there has been a holiday announced on {today}(today)"
            f" on the occasion of {holiday.name}."
        )
        for user in holiday.applicable_users:

            if email.can_send_email(user, HOLIDAY_EMAIL) and not email.has_sent_email(
                recipient=user, notification_text=message, subject=subject
            ):
                recipients.append(user.email)

        if recipients:
            send_notification_email(
                recipients=recipients,
                subject=subject,
                notification_text=message
            )
