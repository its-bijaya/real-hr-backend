from irhrs.core.utils.custom_mail import custom_mail as send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from irhrs.notification.utils import add_notification
from irhrs.task.constants import EMAIL, REMINDER_SENT, REMINDER_FAILED, \
    NOTIFICATION
from ..models.task import TaskReminder

FRONTEND_URL = getattr(settings, 'FRONTEND_URL')
DEFAULT_SERVER_FROM_EMAIL = getattr(settings, 'INFO_EMAIL',
                                    'admin@realhrsoft.com')


def _get_frontend_url(task_id, with_frontend_base=True):
    frontend_url = FRONTEND_URL[:-1] if FRONTEND_URL[
                                            -1] == '/' else FRONTEND_URL
    relative_path = f"/user/task/my/{task_id}/detail"
    url = frontend_url + relative_path if with_frontend_base else relative_path
    return url


def _send_reminder_email(data):
    context = {
        "full_name": data.user.first_name,
        "email": data.user.email,
        "task_link": _get_frontend_url(data.task_id),
        'task_title': data.task.title,
        "greeting": 'You' if data.created_by_id == data.user_id else data.created_by.full_name
    }
    message = render_to_string('task/task_reminder.txt', context)

    html_message = render_to_string(
        'task/task_reminder.html', context)
    subject = "RealHRSoft Task Reminder | {} ".format(data.task.title)

    mail = send_mail(subject, message, DEFAULT_SERVER_FROM_EMAIL,
                     [data.user.email],
                     html_message=html_message)
    if mail:
        data.sent_on = timezone.now()
        data.status = REMINDER_SENT
        data.extra_data = "Sent Email"
        data.save(update_fields=['sent_on', 'status', 'extra_data'])
    else:
        data.extra_data = "Couldnt send email [SMTP Error]"
        data.status = REMINDER_FAILED
        data.save(update_fields=['status', 'extra_data'])


def _send_reminder_notification(data):
    add_notification(
        text=f"Task Reminder for {data.task.title}",
        recipient=data.user,
        action=data.task,
        url=_get_frontend_url(data.task_id, with_frontend_base=False)
    )
    data.sent_on = timezone.now()
    data.status = REMINDER_SENT
    data.extra_data = "Sent Notification"
    data.save(update_fields=['sent_on', 'status', 'extra_data'])


def task_reminder():
    users = TaskReminder.objects.filter(
        remind_on__range=[timezone.now() - timezone.timedelta(minutes=2),
                          timezone.now() + timezone.timedelta(
                              minutes=4)], sent_on__isnull=True,
        ).select_related('user', 'task')
    for data in users:
        if data.method == EMAIL:
            _send_reminder_email(data)
        elif data.method == NOTIFICATION:
            _send_reminder_notification(data)
        else:
            pass
