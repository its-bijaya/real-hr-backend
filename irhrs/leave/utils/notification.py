"""@irhrs_docs"""
import logging
import re

from django.conf import settings
from django_q.tasks import async_task

from irhrs.attendance.tasks.send_notifications import generate_html_message
from irhrs.core.constants.common import LEAVE_EMAIL
from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.core.utils.custom_mail import custom_mail as send_mail
from irhrs.leave.constants.model_constants import DENIED, APPROVED
from irhrs.notification.utils import notify_organization
from irhrs.organization.models import NotificationTemplateMap
from irhrs.permission.constants.permissions import ORGANIZATION_SETTINGS_PERMISSION, ORGANIZATION_PERMISSION

INFO_EMAIL = getattr(settings, 'INFO_EMAIL', 'noreply@realhrsoft.com')


def generate_leave_notification_content(leave_request, choice=LEAVE_EMAIL):
    valid_choices = [LEAVE_EMAIL]
    if choice not in valid_choices:
        return
    replace_data = {
        '{{user}}': leave_request.user.full_name,
        '{{start_date}}': leave_request.start.astimezone(
        ).strftime('%Y-%m-%d %I:%M %p'),
        '{{end_date}}': leave_request.end.astimezone(
        ).strftime('%Y-%m-%d %I:%M %p'),
        '{{status}}': leave_request.status,
        '{{contact_info}}': INFO_EMAIL,
        '{{actor}}': getattr(leave_request.modified_by, 'full_name', ''),
        '{{recipient}}': leave_request.recipient.full_name,
    }
    template_map = NotificationTemplateMap.objects.filter(
        organization=nested_getattr(
            leave_request.user,
            'detail.organization'
        ),
        template__type=LEAVE_EMAIL,
        is_active=True,
        active_status__contains=[leave_request.status],
    ).first()
    if not template_map:
        return
    message = get_leave_template_content(template_map, leave_request)
    for r in re.findall('\{\{[A-Za-z0-9 _]+\}\}', message):
        message = message.replace(
            r,
            str(replace_data.get(r, ''))
        )
    return message


def get_leave_template_content(template_map, leave_request):
    message = template_map.template.contents.filter(
        status=leave_request.status
    ).values_list('content', flat=True).first() or ''
    return message


def generate_email_recipients_for_leave(leave_request):
    """
    Generate to and bcc list from the given leave request.
    :param leave_request: Leave Request whose notification is to be sent.
    :return: to and cc mailing addresses
    """
    # for now, sending to the recipient and cc'ing the respective user.
    return leave_request.recipient.email, leave_request.user.email


def is_valid_to_send_leave_notification(leave_request):
    return (
        leave_request.leave_rule.leave_type.email_notification
        and leave_request.user.email_setting.filter(
            leave=True
        ).exists()
    )


def send_leave_notification(leave_request):
    if not is_valid_to_send_leave_notification(leave_request):
        return
    logger = logging.getLogger(__name__)
    content = generate_leave_notification_content(
        leave_request, LEAVE_EMAIL
    )
    if content:
        subject = f'Leave {leave_request.status}'
        async_task(
            send_mail,
            subject,
            content,
            get_system_admin().email,
            generate_email_recipients_for_leave(leave_request),
            html_message=generate_html_message({
                'title': subject,
                'subtitle': subject,
                'message': content
            })
        )
        logger.info(
            f"Sent Leave {leave_request.status} notification to "
            f"{leave_request.user.full_name}"
        )
    else:
        org = leave_request.user.detail.organization
        notify_organization(
            text=f"Failed to send leave {leave_request.status} notification to "
                 f"{leave_request.user.full_name} as no template was found.",
            action=leave_request,
            organization=org,
            url=f'/admin/{org.slug}/organization/settings/template-mapping',
            permissions=[
                ORGANIZATION_PERMISSION,
                ORGANIZATION_SETTINGS_PERMISSION
            ]
        )
