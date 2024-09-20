"""@irhrs_docs"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Subquery, Exists, DateField, OuterRef
from django.db.models.functions import Cast, Right
from django.utils import timezone
from datetime import timedelta as td
from rest_framework.exceptions import ValidationError

from irhrs.attendance.constants import (
    SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY,
    SATURDAY, REQUESTED, FORWARDED, DECLINED, APPROVED, CONFIRMED,
    WORKDAY, FULL_LEAVE, CANCELLED, UNCLAIMED)
from irhrs.common.models.system_email_log import SystemEmailLog
from irhrs.core.utils.common import get_today, validate_permissions

from irhrs.permission.constants.permissions import ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION, \
    ATTENDANCE_CREDIT_HOUR_REQUEST_PERMISSION
from irhrs.users.models import UserSupervisor

USER = get_user_model()


# copied from utils/leave_request due to circular dependency
def get_appropriate_recipient(user, level=1):
    if level == 1:
        # The supervisor isn't taken from user.first_level_supervisor due to implementation changes.
        # sup = getattr(user, 'first_level_supervisor', None)
        return UserSupervisor.objects.filter(
            user=user,
            authority_order=1
        ).first()
    else:
        return user.supervisors.filter(authority_order=level).first()


# copied from utils/leave_request due to circular dependency
def get_authority(user, supervisor):
    obj = user.supervisors.filter(supervisor=supervisor).first()
    return obj.authority_order if obj else None


def get_weekday(timestamp=None):
    # This method is used for mapping between our week days stored in database'
    # Sunday -> 1
    #  ..........
    # Saturday --> 7
    timestamp = timestamp or timezone.now()
    return [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY][
        timestamp.weekday()]


def get_overtime_recipient(overtime, status, old_status = None):
    """
    Gets appropriate recipient for the OT requests.
    :param overtime:
    :return:
    """
    user = overtime.overtime_entry.user
    current_recipient = overtime.recipient
    # The supervisor isn't taken from user.first_level_supervisor due to implementation changes.
    # sup = getattr(user, 'first_level_supervisor', None)
    sup = UserSupervisor.objects.filter(
        user=user,
        authority_order=1
    ).first()
    if old_status == UNCLAIMED:
        current_recipient = sup.supervisor if sup else None
    current_level = get_authority(user, current_recipient) or 0
    recipient = {
        REQUESTED: sup,
        FORWARDED: get_appropriate_recipient(user, current_level + 1),
        DECLINED: current_recipient,
        APPROVED: current_recipient,
        CONFIRMED: current_recipient
    }
    rec = recipient.get(status)
    if isinstance(rec, UserSupervisor):
        return getattr(rec, 'supervisor')
    return rec


def validate_appropriate_actor(user, overtime, attrs, mode="user"):
    actor = user
    status = attrs.get('status')
    if validate_permissions(
        user.get_hrs_permissions(
            # The permission is given to the organization of the user.
            overtime.overtime_entry.user.detail.organization
        ),
        ATTENDANCE_PERMISSION,
        ATTENDANCE_OVERTIME_CLAIM_PERMISSION
    ):
        if status in [APPROVED, DECLINED, CONFIRMED]:
            return
    if mode == "supervisor" and overtime.status == UNCLAIMED and actor == overtime.recipient.first_level_supervisor:
        return
    if actor != overtime.recipient:
        # could be case of declined requests.
        if status == REQUESTED and actor == overtime.overtime_entry.user:
            return
        raise ValidationError(
            f"You cannot act on this request as you are not the appropriate "
            f"recipient."
        )
    # Add action permission
    qs = overtime.overtime_entry.user.supervisors.filter(
        supervisor=actor
    )
    authority_order = {
        FORWARDED: qs.filter(forward=True).exists(),
        DECLINED: qs.filter(deny=True).exists(),
        APPROVED: qs.filter(approve=True).exists()
    }
    if not authority_order.get(status):
        raise ValidationError(
            f"You do not have {status} permission assigned."
        )


def send_absent_notification(date_str=None):
    """
    Task to Send Absent Notifications to the user.
    the sent emails and test logic {{3}} hours after shift end.
    :return:
    """
    from irhrs.attendance.tasks.overtime import OvertimeTimesheet
    from irhrs.attendance.tasks.send_notifications import send_absent_notification as se
    from dateutil.parser import parse
    if not date_str:
        forced_date = get_today()
    else:
        try:
            forced_date = parse(date_str)
        except ValueError:
            forced_date = get_today()
    now = timezone.now().astimezone()
    users_with_enabled_notifications = USER.objects.filter(
        attendance_setting__absent_notification_email=True
    ).values_list('pk', flat=True)
    from irhrs.attendance.models import TimeSheet
    absent_timesheets = TimeSheet.objects.filter(
        is_present=False,
        coefficient=WORKDAY,
        timesheet_for=forced_date,
        timesheet_user__in=Subquery(users_with_enabled_notifications)
    ).exclude(
        leave_coefficient=FULL_LEAVE
    ).annotate(
        absent_notification_sent=Exists(
            SystemEmailLog.objects.filter(
                subject__startswith='Absent for'
            ).annotate(
                absent_date=Cast(Right('subject', 10), DateField())
            ).filter(
                sent_address=OuterRef('timesheet_user__email'),
                absent_date=OuterRef('timesheet_for')
            )
        )
    ).filter(
        absent_notification_sent=False
    ).select_related(
        'timesheet_user'
    )
    processed_timesheets = map(
        lambda x: OvertimeTimesheet(x), absent_timesheets
    )
    wait = getattr(settings, 'ABSENT_DEEMING_WAIT_TIME', 3)
    filtered_timesheets = filter(
        lambda x: x.shift_end and (
                x.shift_end + td(hours=wait)
        ) <= now,
        processed_timesheets
    )
    for timesheet in map(lambda x: x.timesheet, filtered_timesheets):
        se(timesheet)


def get_pre_approval_recipient(user, status=REQUESTED, old_recipient=None):
    """
    :param user: The user who sent the Pre Approval Request.
    :param status: The new status being set to Pre Approval Request.
    :param old_recipient: The user who is the recipient of the Pre Approval Request.
    :return : Returns the new recipient.
    :rtype: User
    :seealso: get_overtime_recipient

    Gets appropriate recipient for Pre Approval Model.
    Current Implementation is levels defined in UserSupervisor.
    If at some point in time, the logic changes to Explicitly defined users,
    Just return the appropriate recipient using the model dedicated to store PreApproval
    authorities.
    """
    sup = UserSupervisor.objects.filter(
        user=user,
        authority_order=1
    ).first()
    current_level = get_authority(user, old_recipient) or 0
    recipient = {
        REQUESTED: sup,
        FORWARDED: get_appropriate_recipient(user, current_level + 1),
        DECLINED: old_recipient,
        APPROVED: old_recipient,
        CONFIRMED: old_recipient,
        CANCELLED: user,
    }
    rec = recipient.get(status)
    if isinstance(rec, UserSupervisor):
        return getattr(rec, 'supervisor')
    return rec


def validate_appropriate_pre_approval_actor(user, pre_approval, status, permissions):
    """
    If actor does not have authority to perform, raise ValidationError.
    :seealso: validate_appropriate_actor
    """
    actor = user
    if status == CANCELLED:
        if actor != pre_approval.sender:
            raise ValidationError(
                f"Only the sender can cancel the request."
            )
        return
    if validate_permissions(
        user.get_hrs_permissions(
            # The permission is given to the organization of the user.
            pre_approval.sender.detail.organization
        ),
        *permissions
    ):
        if status in [APPROVED, DECLINED, CONFIRMED]:
            return
    if actor != pre_approval.recipient:
        raise ValidationError(
            f"You cannot act on this request as you are not the appropriate "
            f"recipient."
        )
    # Add action permission
    qs = pre_approval.sender.supervisors.filter(supervisor=actor)
    authority_order = {
        FORWARDED: qs.filter(forward=True).exists(),
        DECLINED: qs.filter(deny=True).exists(),
        APPROVED: qs.filter(approve=True).exists()
    }
    if not authority_order.get(status):
        raise ValidationError(
            f"You do not have {status} permission assigned."
        )


WEEK_START_DAY = getattr(settings, 'WEEK_START_DAY')


def get_week_range(dt):
    """
    Returns the start and end date of week, the date falls in.
    Define Week Start in WEEK_START_DAY
    Example:
    If week starts on Sunday:
        2020-06-07 Sun 2020-06-07 2020-06-13
        2020-06-08 Mon 2020-06-07 2020-06-13
        2020-06-09 Tue 2020-06-07 2020-06-13
        2020-06-10 Wed 2020-06-07 2020-06-13
        2020-06-11 Thu 2020-06-07 2020-06-13
        2020-06-12 Fri 2020-06-07 2020-06-13
        2020-06-13 Sat 2020-06-07 2020-06-13
    If week starts on Wednesday
        2020-06-07 Sun 2020-06-03 2020-06-09
        2020-06-08 Mon 2020-06-03 2020-06-09
        2020-06-09 Tue 2020-06-03 2020-06-09
        2020-06-10 Wed 2020-06-10 2020-06-16
        2020-06-11 Thu 2020-06-10 2020-06-16
        2020-06-12 Fri 2020-06-10 2020-06-16
        2020-06-13 Sat 2020-06-10 2020-06-16
    :param dt: date to find closure week for.
    :returns: returns the week the date falls in.
    """

    def end(x):
        if x <= dt:
            return x, x+timezone.timedelta(days=6)
        return x-timezone.timedelta(days=7), x-timezone.timedelta(days=1)

    if get_weekday(dt) == WEEK_START_DAY:
        return end(dt)
    if get_weekday(dt) > WEEK_START_DAY:
        days_to_reduce = get_weekday(dt) - WEEK_START_DAY
        return end(dt - timezone.timedelta(days=days_to_reduce))
    if get_weekday(dt) < WEEK_START_DAY:
        date_to_add = WEEK_START_DAY - get_weekday(dt)
        return end(dt + timezone.timedelta(days=date_to_add))
