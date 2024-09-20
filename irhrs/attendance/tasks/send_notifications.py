import re
from datetime import timedelta, datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Avg, Q, F, DurationField, Sum, TimeField
from django.db.models.functions import Coalesce, Extract, Cast
from django.forms import FloatField
from django.template.loader import render_to_string
from django.utils import timezone
from django_q.tasks import async_task

from irhrs.attendance.constants import LATE_IN, WORKDAY, NO_LEAVE, SECOND_HALF, FIRST_HALF
from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.core.constants.common import ABSENT_EMAIL, LATE_IN_EMAIL, WEEKLY_ATTENDANCE_REPORT_EMAIL
from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.core.utils.custom_mail import custom_mail as send_mail
from irhrs.notification.utils import notify_organization
from irhrs.organization.models import NotificationTemplateMap
from irhrs.permission.constants.permissions import (
    ORGANIZATION_PERMISSION, ORGANIZATION_SETTINGS_PERMISSION, ATTENDANCE_PERMISSION
)
from ..api.v1.reports.serializers.individual_attendance_report import \
    IndividualAttendanceOverviewSerializer
from ..models import TimeSheet, TimeSheetEntry
from ..utils import attendance_logger
from ..utils.get_lost_hours_as_per_shift import get_lost_hours_for_date_range
from ...core.utils.common import get_today

User = get_user_model()

INFO_EMAIL = getattr(settings, 'INFO_EMAIL', 'noreply@realhrsoft.com')


def generate_showcase_duration_string(duration):
    if not duration:
        return ''
    rel = relativedelta(seconds=duration.total_seconds())
    final = list()
    for preference in ['hours', 'minutes', 'seconds']:
        actual = int(getattr(rel, preference))
        if actual:
            final.append(f'{actual} {preference}')
    return ' and '.join(final[:2])


def generate_notification_content(
    template, full_name='User', date='', ot_hours='',
    expected_punch_in='', actual_punch_in='',
    late_duration=None,
    contact_info=INFO_EMAIL
):
    replacables = {
        '{{user}}': full_name,
        '{{date}}': date,
        '{{ot_hours}}': ot_hours,
        '{{contact_info}}': contact_info,
        '{{expected_punch_in}}': expected_punch_in,
        '{{actual_punch_in}}': actual_punch_in,
        '{{late_duration}}': generate_showcase_duration_string(late_duration)
    }
    render_string = get_template_content(template)
    for pattern, replace in replacables.items():
        render_string = re.sub(pattern, replace, render_string)
    return render_string


def get_template_content(template):
    content = template.contents.filter(
        status='Default'
    ).values_list(
        'content', flat=True
    ).first() or ''
    render_string = re.sub('[ ]{2,}', '', content)
    return render_string


def generate_html_message(context):
    message = context.get('message', '')
    context.update({
        'message': message.replace('\n', '<br>')
    })
    return render_to_string(
        'notifications/notification_base.html',
        context=context
    )


def send_late_in_notification_email(timesheet):
    user = timesheet.timesheet_user
    date = timesheet.timesheet_for
    late_in_entry = timesheet.timesheet_entries.filter(
        category=LATE_IN,
        is_deleted=False
    ).first()
    if not late_in_entry:
        return
    notification_enabled = user.attendance_setting.late_in_notification_email
    if not notification_enabled:
        return
    template_map = NotificationTemplateMap.objects.active().filter(
        organization=nested_getattr(user, 'detail.organization'),
        template__type=LATE_IN_EMAIL
    ).first()
    if template_map:
        actual_punch_in = timesheet.punch_in.astimezone().time().replace(
            microsecond=0
        )  # remove scenario:  but you arrived at 15:53:26.628316
        expected_punch_in = timesheet.work_time.start_time
        late_duration = timesheet.punch_in_delta
        subject = f'Late In for {date}'
        message = generate_notification_content(
            template=template_map.template,
            full_name=user.full_name,
            date=date.strftime('%Y-%m-%d'),
            actual_punch_in=str(actual_punch_in),
            expected_punch_in=str(expected_punch_in),
            late_duration=late_duration
        )
        html_message = generate_html_message({
            'title': subject,
            'subtitle': subject,
            'message': message
        })
        try:
            async_task(
                send_mail, subject, message, get_system_admin().email,
                [user.email], html_message=html_message)
            attendance_logger.info(
                f'Sent Late In Notification to {user.full_name}'
            )
        except Exception as e:
            attendance_logger.exception(str(e))
    else:
        org = user.detail.organization
        notify_organization(
            text=f'Failed to send Late In Notification for {user.full_name} for '
                 f'{timesheet.timesheet_for} as no template is assigned for {org}.',
            action=timesheet,
            organization=org,
            url=f'/admin/{org.slug}/organization/settings/template-mapping',
            permissions=[
                ORGANIZATION_PERMISSION,
                ORGANIZATION_SETTINGS_PERMISSION
            ]
        )


def send_absent_notification(timesheet):
    is_present = timesheet.is_present
    if is_present:
        return
    template_map = NotificationTemplateMap.objects.active().filter(
        organization=nested_getattr(
            timesheet.timesheet_user, 'detail.organization'
        ),
        template__type=ABSENT_EMAIL
    ).first()
    if template_map:
        subject = f'Absent for {timesheet.timesheet_for}'
        message = generate_notification_content(
            template=template_map.template,
            full_name=timesheet.timesheet_user.full_name,
            date=timesheet.timesheet_for.strftime('%Y-%m-%d')
        )
        try:
            async_task(
                send_mail, subject, message, INFO_EMAIL,
                [timesheet.timesheet_user.email],
                html_message=generate_html_message({
                    'title': subject,
                    'subtitle': subject,
                    'message': message
                }))
            attendance_logger.info(
                'Sent Late In Notification to '
                f'{timesheet.timesheet_user.full_name}'
            )
        except Exception as e:
            attendance_logger.exception(str(e))
    else:
        org = timesheet.timesheet_user.detail.organization
        notify_organization(
            text=f"Failed to send absent notification to "
                 f"{timesheet.timesheet_user} for {timesheet.timesheet_for} "
                 f"as no active template was found.",
            action=timesheet,
            organization=org,
            url=f'/admin/{org.slug}/organization/settings/template-mapping',
            permissions=[
                ORGANIZATION_PERMISSION,
                ORGANIZATION_SETTINGS_PERMISSION
            ]
        )


def send_populate_timesheet_notifications(success, kwargs):
    permission_list = [
        ATTENDANCE_PERMISSION
    ]
    user = kwargs['user']
    org = user.detail.organization
    start_date = kwargs['start_date']
    end_date = kwargs['end_date']
    if not success:
        text = "Task for timesheet generation of {} for dates: " \
               "{} to {} has failed.".format(user,
                                             start_date,
                                             end_date, )
    else:
        text = "Task for timesheet generation of {} for dates: " \
               "{} to {} has been completed.".format(user,
                                                     start_date,
                                                     end_date)
    notify_organization(
        text=text,
        action=user,
        url=f'/admin/{org.slug}/attendance/reports/calendar',
        organization=user.detail.organization,
        permissions=permission_list
    )


def generate_weekly_attendance_report_content(
    template,
    user,
):
    weekly_aggregates, daily_attendance_details = get_weekly_user_report(user)
    date = get_today()
    average_in = humanize_interval(weekly_aggregates['average_in'])
    average_out = humanize_interval(weekly_aggregates['average_out'])
    punctuality = weekly_aggregates['punctuality']
    total_worked_hours = weekly_aggregates['total_worked_hours']
    total_working_hours = weekly_aggregates['total_working_hours']
    overtime = weekly_aggregates['overtime']
    detailed_weekly_attendance_table = generate_table(user)
    email_hints = {
        '{{user}}': user.full_name,
        '{{date}}': date,
        '{{contact_info}}': INFO_EMAIL,
        '{{average_in}}': average_in,
        '{{average_out}}': average_out,
        '{{punctuality}}': punctuality,
        '{{total_worked_hours}}': total_worked_hours,
        '{{total_working_hours}}': total_working_hours,
        '{{overtime}}': overtime,
        '{{detailed_weekly_attendance_table}}': detailed_weekly_attendance_table,
    }
    render_string = get_template_content(template)
    for pattern, replace in email_hints.items():
        render_string = re.sub(pattern, str(replace), render_string)
    return render_string


def convert_to_hours(duration):
    if not duration:
        return '0'
    if not isinstance(duration, int):
        duration = duration.seconds + duration.days * 86400
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    return '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)


def get_weekly_user_report(user):
    to_date = timezone.now().date() - timedelta(days=1)
    one_week_before = to_date - timedelta(days=6)
    timesheets = TimeSheet.objects.filter(
        timesheet_user=user, timesheet_for__range=[one_week_before, to_date]
    ).order_by('timesheet_for')

    TIMESHEET_COEFFICIENTS = {
        1: 'Workday',
        2: 'Offday',
        3: 'Holiday',
    }
    daily_attendance_details = []
    total_lost_hours = 0
    for timesheet in timesheets:
        day_name = timesheet.timesheet_for.strftime("%A")
        days = timesheet.coefficient
        day_type = TIMESHEET_COEFFICIENTS[days]
        total_lost_hours = get_lost_hours_for_date_range(
            timesheet.timesheet_user_id, timesheet.timesheet_user.detail.organization,
            one_week_before, to_date, calculate_unpaid_breaks=True,
            calculate_lost_hour_in_absent_days=True
        )
        attendances = timesheet.timesheet_entries.filter(
            entry_type__in=['Punch In', 'Punch Out'], is_deleted=False).values_list('category', flat=True)

        if not day_type == 'Workday' and not attendances:
            daily_attendance_details.append({
                'day_name': day_name,
                'date': timesheet.timesheet_for.strftime("%d %B"),
                'day_type': day_type,
            })
        else:
            punch_status = list(attendances)
            daily_attendance_details.append({
                'day_name': day_name,
                'date': timesheet.timesheet_for.strftime("%d %B"),
                'punch_in': timesheet.punch_in.astimezone().strftime(
                    '%H:%M:%S') if timesheet.punch_in else None,
                'punch_out': timesheet.punch_out.astimezone().strftime(
                    '%H:%M:%S') if timesheet.punch_out else None,
                'worked_hours': timesheet.worked_hours,
                'punctuality': timesheet.punctuality,
                'unpaid_break_hours': timesheet.unpaid_break_hours,
                'leave_coefficient': timesheet.leave_coefficient,
                'status': sorted(punch_status, key=lambda x: x[-1]),
            })
    timesheets_filter = {
        'coefficient': WORKDAY,
        'timesheet_for__range': [one_week_before, to_date],
        'leave_coefficient__in': [
            NO_LEAVE, FIRST_HALF, SECOND_HALF
        ]
    }
    weekly_aggregates = timesheets.annotate(
        expected_work_hours=F('expected_punch_out') - F(
            'expected_punch_in'),
        punch_in_time=Cast(
            F('punch_in'), TimeField()
        ),
        punch_out_time=Cast(
            F('punch_out'), TimeField()
        ),
    ).aggregate(
        average_in=Coalesce(
            Avg(Extract('punch_in', 'Hour')), 0.0
        ) * 60 * 60 + Coalesce(
            Avg(Extract('punch_in', 'Minute')), 0.0
        ) * 60 + Coalesce(
            Avg(Extract('punch_in', 'Second')), 0.0
        ),
        average_out=Coalesce(
            Avg(Extract('punch_out', 'Hour')), 0.0
        ) * 60 * 60 + Coalesce(
            Avg(Extract('punch_out', 'Minute')), 0.0
        ) * 60 + Coalesce(
            Avg(Extract('punch_out', 'Second')), 0.0
        ),
        punctuality=Avg(
            Coalesce(F('punctuality'), 0.0),
            filter=Q(
                **timesheets_filter,
                work_shift__isnull=False
            ),
        ),
        total_worked_hours=Sum(
            'worked_hours',
            filter=Q(**timesheets_filter),
            output_field=DurationField()
        ),
        total_working_hours=Sum(
            'expected_work_hours',
            filter=Q(**timesheets_filter),
            output_field=DurationField()
        ),
        overtime=Sum(
            F('overtime__overtime_detail__claimed_overtime'),
            filter=Q(**timesheets_filter),
            output_field=DurationField()
        ),
    )
    weekly_aggregates['punctuality'] = round(weekly_aggregates['punctuality'], 2) if \
    weekly_aggregates['punctuality'] else 0
    weekly_aggregates['sub_punctuality'] = 100 - weekly_aggregates['punctuality']
    weekly_aggregates['total_worked_hours'] = convert_to_hours(
        weekly_aggregates['total_worked_hours'])
    weekly_aggregates['total_working_hours'] = convert_to_hours(
        weekly_aggregates['total_working_hours'])
    weekly_aggregates['total_lost_hours'] = convert_to_hours(int(total_lost_hours))
    return weekly_aggregates, daily_attendance_details


def generate_table(user):
    aggregate_result, table_data = get_weekly_user_report(user)
    detailed_weekly_attendance_table = render_to_string(
        'notifications/weekly_attendance.html',
        context={
            "aggregate_result": aggregate_result,
            'table_data': table_data,
        }
    )
    return detailed_weekly_attendance_table


def generate_weekly_attendance_report_html_message(user, context):
    message = context.get('message', '')
    aggregate_result, table_data = get_weekly_user_report(user)
    context.update({
        'message': message
    })
    return render_to_string(
        'notifications/notification_base.html',
        context={
            "table_data": table_data,
            "message": message,
        }
    )


def send_weekly_attendance_report_email():
    users = User.objects.filter(
        attendance_setting__weekly_attendance_report_email=True
    )

    for user in users:
        template_map = NotificationTemplateMap.objects.active().filter(
            organization=nested_getattr(user, 'detail.organization'),
            template__type=WEEKLY_ATTENDANCE_REPORT_EMAIL
        ).first()
        to_date = get_today() - timedelta(days=1)
        from_date = to_date - timedelta(days=6)
        if template_map:
            subject = f'Weekly Attendance Report from {from_date} to {to_date}.'
            message = generate_weekly_attendance_report_content(
                template_map.template,
                user,
            )

            html_message = generate_weekly_attendance_report_html_message(
                user,
                {
                    'title': subject,
                    'subtitle': subject,
                    'message': message,
                })

            send_mail(
                subject, message, get_system_admin().email,
                [user.email], html_message=html_message
            )
            attendance_logger.info(
                f'Sent Weekly Attendance Report to {user.full_name}'
            )
        else:
            org = user.detail.organization
            notify_organization(
                text=f"Couldn't send weekly attendance report email for {user}.",
                action=user,
                organization=org,
                url=f'/admin/{org.slug}/organization/settings/template-mapping',
                permissions=[
                    ORGANIZATION_PERMISSION,
                    ORGANIZATION_SETTINGS_PERMISSION
                ]
            )
