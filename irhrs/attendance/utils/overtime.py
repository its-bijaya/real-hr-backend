"""@irhrs_docs"""
import logging
import re

from django.conf import settings
from django_q.tasks import async_task

from irhrs.attendance.constants import UNCLAIMED, APPROVED
from irhrs.attendance.tasks.send_notifications import generate_html_message
from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.core.constants.common import OVERTIME_EMAIL
from irhrs.core.constants.organization import OVERTIME_GENERATED_EMAIL
from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.core.utils.custom_mail import custom_mail as send_mail
from irhrs.core.utils.email import send_email_as_per_settings
from irhrs.notification.utils import add_notification
from irhrs.organization.models import NotificationTemplateMap

INFO_EMAIL = getattr(settings, 'INFO_EMAIL', 'noreply@realhrsoft.com')
attendance_logger = logging.getLogger(__name__)


def get_grouped_entries(entries: list):
    grouped = dict()
    for ent in entries:
        usr = ent.user
        if usr in grouped:
            grouped[usr].append(ent)
            continue
        grouped[usr] = [ent]
    return grouped


def generate_overtime_notification(entries=list(), pre_approval=False):
    """
    This function expects all the overtime claim that has been generated.
    The entries are filtered and per user count is generated. Using the
    count, the overtime notification is sent to the user.
    Expected Result: Your 10 overtime entries has been generated. Please claim.
    """
    notifications = []
    for user, entry_group in get_grouped_entries(entries).items():
        count = len(entry_group)
        if entry_group[0].claim.status == UNCLAIMED:
            action_performed = None
        else:
            action_performed = entry_group[0].claim.status.lower()
        if action_performed == APPROVED.lower():
            # We wont send approved notification to user, as it would double notify.
            continue
        if count == 1:
            day = entry_group[0].timesheet.timesheet_for
            if action_performed:
                frontend_url = "/user/attendance/reports/overtime-claims"
                text = f'Your overtime for {day} has been generated and {action_performed}'
            else:
                frontend_url = '/user/attendance/request/overtime-claims'
                text = f'Your overtime for {day} has been generated.'
            notifications.append((user, text, frontend_url))
            continue
        max_day = max([e.timesheet.timesheet_for for e in entry_group])
        min_day = min([e.timesheet.timesheet_for for e in entry_group])
        text = f'Your {count} overtime claims from {min_day} to {max_day} ' \
               f'has been generated'
        frontend_url = '/user/attendance/request/overtime-claims'
        if action_performed:
            frontend_url = "/user/attendance/reports/overtime-claims"
            text = text + action_performed.lower()
        notifications.append((user, text, frontend_url))

    for user, text, frontend_url in notifications:
        add_notification(
            actor=get_system_admin(),
            text=text,
            recipient=user,
            action=user,
            url=frontend_url
        )
        send_email_as_per_settings(
            recipients=user,
            subject="Overtime Generated",
            email_text=text,
            email_type=OVERTIME_GENERATED_EMAIL
        )


def get_template_content(template):
    content = template.contents.filter(
        status='Default'
    ).values_list(
        'content', flat=True
    ).first() or ''
    render_string = re.sub('[ ]{2,}', '', content)
    return render_string


def send_overtime_email(entries=list()):
    emails_to_send = []
    for user, entry_group in get_grouped_entries(entries).items():
        attendance_logger.debug(
            f'Testing overtime remainder flag for {user}'
        )
        flag = nested_getattr(
            user, 'attendance_setting.overtime_remainder_email'
        )
        if not flag:
            attendance_logger.debug(
                'Flag is disabled'
            )
            continue
        attendance_logger.debug(
            'Flag is enabled'
        )
        template = NotificationTemplateMap.objects.filter(
            organization=user.detail.organization,
            template__type=OVERTIME_EMAIL,
            is_active=True
        ).first()
        attendance_logger.debug(
            f'Finding the overtime template for {user}'
        )
        if not template:
            attendance_logger.debug(
                'Template was not found.'
            )
            continue
        attendance_logger.debug(
            f'Selected template is {template}'
        )
        entries_count = len(entry_group)
        overtime_generated = sum([
            entry.overtime_detail.total_seconds for entry in entry_group
        ])
        if entries_count == 1:
            replace_with = entries[0].timesheet.timesheet_for.strftime(
                '%Y-%m-%d'
            )
        else:
            max_day = max([e.timesheet.timesheet_for for e in entry_group])
            min_day = min([e.timesheet.timesheet_for for e in entry_group])
            replace_with = min_day.strftime(
                '%Y-%m-%d'
            ) + ' till ' + max_day.strftime('%Y-%m-%d')
        replacables = {
            '{{user}}': user.full_name,
            '{{ot_hours}}': humanize_interval(overtime_generated),
            '{{contact_info}}': INFO_EMAIL,
            '{{date}}': replace_with,
        }
        subject = 'Overtime Generated for ' + replace_with
        render_string = get_template_content(template.template)
        if not render_string:
            logging.warning(f"Empty overtime notification Content, "
                            f"{user.full_name}")
            continue
        for pattern, replace in replacables.items():
            render_string = re.sub(pattern, replace, render_string)
        emails_to_send.append((user, subject, render_string))
    for user, subject, message in emails_to_send:
        try:
            async_task(
                send_mail, subject, message, get_system_admin().email,
                [user.email],
                html_message=generate_html_message({
                    'title': subject,
                    'subtitle': subject,
                    'message': message
                })
            )
            attendance_logger.info(
                f'Sent Overtime Notification to {user.full_name}'
            )
        except Exception as e:
            attendance_logger.exception(str(e))
