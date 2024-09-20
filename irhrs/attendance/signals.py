import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from irhrs.attendance.constants import APPROVED, DELETE, FORWARDED, REQUESTED, \
    CONFIRMED, DECLINED, UNCLAIMED, CANCELLED, GENERATED
from irhrs.attendance.models import AttendanceAdjustmentHistory,\
    OvertimeClaimHistory, TimeSheet, IndividualAttendanceSetting, CreditHourRequestHistory, \
    TimeSheetReportRequestHistory, WorkShiftLegend, WorkShift
from irhrs.attendance.models.credit_hours import CreditHourDeleteRequestHistory
from irhrs.attendance.models.pre_approval import PreApprovalOvertimeHistory
from irhrs.attendance.models.travel_attendance import TravelAttendanceRequestHistory, \
    TravelAttendanceDeleteRequestHistory
from irhrs.attendance.tasks.credit_hours import perform_credit_hour_recalibration
from irhrs.attendance.tasks.overtime import generate_adjusted_overtime
from irhrs.core.constants.common import ADJUSTMENT_REQUEST_NOTIFICATION, \
    OVERTIME_CLAIM_NOTIFICATION, TRAVEL_ATTENDANCE_NOTIFICATION, \
    TRAVEL_ATTENDANCE_DELETE_NOTIFICATION, OVERTIME_PRE_APPROVAL, CREDIT_HOUR_PRE_APPROVAL, \
    CREDIT_HOUR_PRE_APPROVAL_DELETE, TIMESHEET_REPORT
from irhrs.core.constants.organization import (
    ACTION_ON_CREDIT_HOUR_EMAIL, CREDIT_HOUR_APPROVAL_REQUESTED_FORWARDED_EMAIL, 
    CREDIT_HOUR_DELETE_REQUEST_IS_REQUESTED_FORWARDED_EMAIL, 
    CREDIT_HOUR_DELETE_REQUEST_IS_APPROVED_DECLINED_EMAIL,
    OVERTIME_CLAIM_APPROVED_DENIED_CONFIRMED, OVERTIME_CLAIM_REQUEST, OVERTIME_RECALIBRATE_EMAIL
)
from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.utils.email import send_email_as_per_settings
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.permission.constants.permissions import ATTENDANCE_PERMISSION, \
    ATTENDANCE_OVERTIME_CLAIM_PERMISSION, ATTENDANCE_TRAVEL_PERMISSION, \
    ATTENDANCE_CREDIT_HOUR_PERMISSION, ATTENDANCE_TIMESHEET_REPORT_PERMISSION
from irhrs.permission.constants.permissions.attendance import \
    ATTENDANCE_CREDIT_HOUR_REQUEST_PERMISSION

from irhrs.core.constants.organization import (
    ATTENDANCE_ADJUSTMENT_REQUEST_EMAIL,
    ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_BY_SUPERVISOR_EMAIL,
    ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_DELETED_BY_HR_EMAIL,
    TRAVEL_ATTENDANCE_REQUEST_EMAIL,
    TRAVEL_ATTENDANCE_IS_APPROVED_DECLINED,
)

ADJUSTMENT, OFFLINE_ATTENDANCE, LEAVE_DELETION = 1, 2, 3
ACTION_TYPES = {
    ADJUSTMENT: 'adjustment approval ',
    OFFLINE_ATTENDANCE: 'offline attendance ',
    LEAVE_DELETION: 'approval of leave deletion ',
}
logger = logging.getLogger(__name__)

email_attendance = {
    REQUESTED: ATTENDANCE_ADJUSTMENT_REQUEST_EMAIL,
    FORWARDED: ATTENDANCE_ADJUSTMENT_REQUEST_EMAIL,
    APPROVED: ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_BY_SUPERVISOR_EMAIL,
    DECLINED: ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_BY_SUPERVISOR_EMAIL
}

email_travel_attendance = {
    REQUESTED: TRAVEL_ATTENDANCE_REQUEST_EMAIL,
    FORWARDED: TRAVEL_ATTENDANCE_REQUEST_EMAIL,
    APPROVED: TRAVEL_ATTENDANCE_IS_APPROVED_DECLINED,
    DECLINED: TRAVEL_ATTENDANCE_IS_APPROVED_DECLINED
}


def get_supervisor_adjustments_url():
    return '/user/supervisor/attendance/requests/adjustments'


def get_user_adjustments_url():
    return '/user/attendance/reports/adjustment'


def recalibrate_overtime(timesheet, actor, action_type=None):
    adjustment_test = generate_adjusted_overtime(timesheet)
    if adjustment_test != 'Exists':
        return False, "Overtime Does Not exist!"
    overtime = nested_getattr(timesheet, 'overtime.claim')
    if not overtime:
        return False, "Overtime Does Not Exist!"
    ot_date = timesheet.timesheet_for
    remark = f're-calibrated for {ot_date} '
    if actor:
        if action_type:
            remark += f'after {ACTION_TYPES.get(action_type, action_type)}'
        else:
            remark += 'after action'
        remark += f' by {actor}'
    recalibrated, message = overtime.recalibrate(remarks=remark.title())
    if not recalibrated:
        return False, message
    overtime_claim_frontend = '/user/attendance/request/overtime-claims'
    recipient = timesheet.timesheet_user
    ws_remark = f'Your overtime claim has been ' + remark
    add_notification(
        actor=get_system_admin(),
        text=ws_remark,
        recipient=recipient,
        action=timesheet,
        url=overtime_claim_frontend
    )
    subject = "Overtime Re-calibrated"
    email_text = (
        f"Overtime for {ot_date} has been re-calibrated."
    )
    send_email_as_per_settings(recipient, subject, email_text, OVERTIME_RECALIBRATE_EMAIL)
    return True, "Calibration Succeeded."


def recalibrate_over_background(ts_id, actor_id, action_type):
    try:
        return recalibrate_overtime(
            TimeSheet.objects.get(pk=ts_id),
            get_user_model().objects.get(pk=actor_id),
            action_type
        )
    except (TimeSheet.DoesNotExist, get_user_model().DoesNotExist) as e:
        logger.warning(
            f"TimeSheet {ts_id} with Actor {actor_id} for action {action_type}"
            f"has failed. with {e}"
        )
        return {
            'status': 'Failed',
            'timesheet_id': ts_id,
            'actor_id': actor_id,
            'action_type': action_type,
            'exception': str(e)
        }


def perform_overtime_credit_hour_recalibration(timesheet, actor, action_type=None):
    # Test if this goes to credit hour or overtime.
    if getattr(timesheet, 'overtime', None):
        recalibrate_overtime(timesheet, actor=actor, action_type=action_type)
    elif timesheet.credit_entries.filter(
        credit_setting__require_prior_approval=True,
        credit_setting__reduce_credit_if_actual_credit_lt_approved_credit=True,
        status=APPROVED,
    ).exists():
        recalibrate_credit_hour_when_timesheet_is_updated(
            timesheet, actor=actor, action_type=action_type
        )


@receiver(post_save, sender=AttendanceAdjustmentHistory)
def create_overtime_recalibration_notification(
    sender, instance, created, **kwargs
):
    adjustment = instance.adjustment
    status = adjustment.status
    timesheet = adjustment.timesheet
    if status != APPROVED:
        return
    performer = instance.action_performed_by
    perform_overtime_credit_hour_recalibration(timesheet, performer, action_type=ADJUSTMENT)


@receiver(post_save, sender=AttendanceAdjustmentHistory)
def create_attendance_adjustment_notification(sender, instance, created, **kwargs):
    """ sends notification and email to corresponding user/s

    :param instance: AttendanceAdjustmentHistory instance
    :param instance.action_performed: possible adjustment actions
    ('Requested', 'Forwarded', 'Approved', 'Declined',
     'Cancel' )
    :param instance.adjustment.action: ('add', 'update', 'delete')

    !!!(as of 2022-01-12), the cancel action has not been implemented

    The receivers of email can be either user, supervisor or hr/s
    depending on the adjustment.

    For a given attendance entry, the action performed can be either requested(by
    user), forwarded(by supervisor), approved or declined (by hr and
    supervisor)

    Any attendance entry can be either added(default), updated, or deleted


    1. If the adjustment is requested, the action has to be informed to supervisor
        and hr(if we enable hr notification via shadow notification (True) )
    2. If the adjustment is forwarded, the request has to be informed to only supervisor
    3. If the adjustment is acted upon(approved or declined), the request has to
       be informed to user,and hr(if supervisor acted upon the request)

    Also, the actor who acts on adjustment should not be receiving message.
    """
    actor = instance.action_performed_by
    adjustment = instance.adjustment
    action = adjustment.action
    recipient = adjustment.receiver
    timesheet = adjustment.timesheet
    url = get_supervisor_adjustments_url()

    delete_text = DELETE + " " if action == DELETE else ""

    if action == DELETE:
        subject = "Attendance entry delete request"
    else:
        subject = f"Attendance entry adjustment {instance.action_performed.lower()}"

    if instance.action_performed == REQUESTED:
        if action == DELETE:
            notification_text = (
                f"{adjustment.sender} has sent attendance"
                f" entry delete request for {timesheet.timesheet_for}."
            )
        else:
            notification_text = (
                f"{actor.full_name} requested "
                f"attendance entry adjustment {delete_text}"
                f"for {timesheet.timesheet_for}."
            )

    elif instance.action_performed == FORWARDED:
        notification_text = (
            f"{actor.full_name} forwarded {adjustment.sender}'s "
            f"attendance entry adjustment {delete_text}request "
            f"for {timesheet.timesheet_for}."
        )

    else:
        url = get_user_adjustments_url()
        recipient = adjustment.sender
        notification_text = (
            f"{actor.full_name} has {instance.action_performed.lower()} "
            f"your adjust attendance entry {delete_text}request for"
            f" {timesheet.timesheet_for}."
        )

    if instance.action_performed in [REQUESTED, FORWARDED]:
        interactive_kwargs = dict(
            is_interactive=True,
            interactive_type=ADJUSTMENT_REQUEST_NOTIFICATION,
            interactive_data={
                "adjustment_request_id": adjustment.id,
                "organization": {
                    "name": adjustment.sender.detail.organization.name,
                    "slug": adjustment.sender.detail.organization.slug,
                }
            }
        )
    else:
        interactive_kwargs = dict()

    hr_recipients = []
    if (
        settings.SHADOW_NOTIFY_ORGANIZATION_ATTENDANCE_ADJUSTMENT
        or recipient == get_system_admin()
    ):
        status = instance.action_performed.lower()
        pronoun = f"{timesheet.timesheet_user}'s"

        request = "request "
        if instance.action_performed == REQUESTED:
            pronoun = "their"
            request = ""

        hr_notification_text = (
            f"{actor.full_name} has {status} {pronoun} "
            f"attendance entry adjustment {delete_text}"
            f"{request}for {timesheet.timesheet_for}."
        )

        if action == DELETE and instance.action_performed == REQUESTED:
            hr_notification_text = (
                f"{adjustment.sender.full_name} has sent their attendance"
                f" entry delete request for {timesheet.timesheet_for}."
            )

        organization = adjustment.sender.detail.organization
        hr_url = f"/admin/{organization.slug}/attendance/requests/adjustments"
        permissions = [ATTENDANCE_PERMISSION]
        notify_organization(
            text=hr_notification_text,
            organization=organization,
            actor=actor,
            action=adjustment,
            url=hr_url,
            permissions=permissions,
            # **interactive_kwargs
        )

        hrs = get_users_list_from_permissions(
            permissions, organization=organization
        )

        hr_recipients = [hr for hr in hrs if hr != actor]
        if hr_recipients and instance.action_performed != FORWARDED:
            send_email_as_per_settings(
                hr_recipients,
                subject,
                hr_notification_text,
                ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_DELETED_BY_HR_EMAIL
            )

    def send_to_recipient(user):
        if user in [get_system_admin(), actor]:
            return False

        if user in hr_recipients:
            return instance.action_performed == FORWARDED

        return True

    if send_to_recipient(recipient):
        add_notification(
            text=notification_text,
            actor=actor,
            action=adjustment,
            recipient=recipient,
            url=url,
            **interactive_kwargs,
        )
        send_email_as_per_settings(
            recipient,
            subject,
            notification_text,
            email_type=email_attendance.get(instance.action_performed, 404)
        )


@receiver(post_save, sender=OvertimeClaimHistory)
def create_overtime_notification(sender, instance, created, **kwargs):
    if instance.action_performed == UNCLAIMED:
        return
    actor = instance.action_performed_by
    overtime = instance.overtime
    recipient = overtime.recipient
    user = overtime.overtime_entry.user
    date = overtime.overtime_entry.timesheet.timesheet_for

    url = {
        APPROVED: '/user/attendance/reports/overtime-claims',
        FORWARDED: '/user/supervisor/attendance/requests/overtime-claims',
        CONFIRMED: '/user/attendance/reports/overtime-claims',
        DECLINED: '/user/attendance/reports/overtime-claims',
        REQUESTED: '/user/supervisor/attendance/requests/overtime-claims'
    }.get(instance.action_performed)

    if instance.action_performed == REQUESTED:
        subject = "Overtime claim Request"
        if actor == get_system_admin():
            notification_text = f"{actor.full_name} sent overtime request " \
                                f"on behalf of {user.full_name} for {date}."
        else:
            notification_text = f"{actor.full_name} sent overtime request " \
                                f"for {date}."

    elif instance.action_performed == FORWARDED:
        notification_text = f"{actor.full_name} forwarded " \
                            f"{user.full_name}'s" \
                            f" overtime for {date}."
        subject = "Overtime claim Forwarded"
    else:
        recipient = user
        notification_text = f"{actor.full_name} has " \
                            f"{instance.action_performed} your " \
                            f"overtime request for {date}."
        subject = f"Overtime {instance.action_performed}"

    # notify organization here
    if instance.action_performed == APPROVED:
        text = f"{actor.full_name} has " \
               f"approved {user.full_name}'s " \
               f"overtime request for {date}."
        organization = user.detail.organization
        hr_url = f'/admin/{organization.slug}/attendance/requests/overtime-claim/?status=Approved'
        notify_organization(
            text=text,
            organization=organization,
            actor=actor,
            action=overtime,
            url=hr_url,
            permissions=[
                ATTENDANCE_PERMISSION,
                ATTENDANCE_OVERTIME_CLAIM_PERMISSION
            ]
        )
        hrs = get_users_list_from_permissions([
            ATTENDANCE_PERMISSION,
            ATTENDANCE_OVERTIME_CLAIM_PERMISSION
        ],
            organization
        )
        subject = "Overtime claim request has been approved"

    if instance.action_performed in [REQUESTED, FORWARDED]:
        interactive_kwargs = dict(
            is_interactive=True,
            interactive_type=OVERTIME_CLAIM_NOTIFICATION,
            interactive_data={
                "overtime_claim_id": overtime.id,
                "organization": {
                    "name": overtime.overtime_entry.user.detail.organization.name,
                    "slug": overtime.overtime_entry.user.detail.organization.slug
                }
            }
        )
    else:
        interactive_kwargs = dict()

    if recipient == get_system_admin() or settings.SHADOW_NOTIFY_ORGANIZATION_OVERTIME:
        hr_notification_text = " ".join(
            map(str, (
                actor.full_name,
                'has',
                instance.action_performed.lower(),
                (
                    'their' if instance.action_performed == REQUESTED
                    else f"{user.full_name}'s"
                ),
                f'system generated overtime for {date}',

            ))
        )
        organization = user.detail.organization
        hr_url = (
            f'/admin/{organization.slug}/attendance/requests/'
            f'overtime-claim/?status={instance.action_performed}'
        )
        notify_organization(
            text=hr_notification_text,
            organization=organization,
            actor=actor,
            action=overtime,
            url=hr_url,
            permissions=[
                ATTENDANCE_PERMISSION,
                ATTENDANCE_OVERTIME_CLAIM_PERMISSION
            ]
        )
        # **interactive_kwargs
        hrs = get_users_list_from_permissions(
            permission_list=[
                ATTENDANCE_PERMISSION,
                ATTENDANCE_OVERTIME_CLAIM_PERMISSION
            ],
            organization=organization
        )
        send_email_as_per_settings(
            recipients=hrs,
            subject=subject,
            email_text=hr_notification_text,
            email_type=OVERTIME_CLAIM_REQUEST,
            allow_duplicates=True
        )

    if recipient != get_system_admin():
        add_notification(
            text=notification_text,
            actor=actor,
            action=overtime,
            recipient=recipient,
            url=url,
            **interactive_kwargs
        )
        send_email_as_per_settings(
            recipients=recipient,
            subject=subject,
            email_text=notification_text,
            email_type=OVERTIME_CLAIM_APPROVED_DENIED_CONFIRMED
        )


@receiver(post_save, sender=get_user_model())
def create_attendance_setting(sender, instance, created, **kwargs):
    if created:
        IndividualAttendanceSetting.objects.create(
            user=instance,
        )


@receiver(post_save, sender=TravelAttendanceRequestHistory)
def create_travel_attendance_request_notification(sender, instance, created, **kwargs):
    last_action_by = instance.created_by
    travel_request = instance.travel_attendance
    possessive_verb = {
        REQUESTED: 'a ',
        FORWARDED: '',
        DECLINED: 'your ',
        APPROVED: 'your ',
        CANCELLED: 'their ',
    }
    status = travel_request.status
    if 0 < travel_request.balance < 1:
        leave_range = f"half day travel request for {travel_request.start}"
    elif travel_request.balance > 1:
        leave_range = f"travel request from {travel_request.start} to {travel_request.end}"
    else:
        leave_range = f"travel request for {travel_request.start}"
    action_text = status.lower()

    if status == FORWARDED:
        action_text += f" {travel_request.user}'s"

    text = f"{last_action_by} has " \
           f"{action_text} " \
           f"{possessive_verb.get(status)}" \
           f"{leave_range}."
    supervisor_url = '/user/supervisor/attendance/requests/travel-attendance'
    self_url = '/user/attendance/request/travel-attendance'
    url = {
        REQUESTED: supervisor_url,
        FORWARDED: supervisor_url,
        DECLINED: self_url,
        APPROVED: self_url
    }.get(status)

    if status in [APPROVED, DECLINED]:
        recipient = travel_request.user
    else:
        recipient = travel_request.recipient

    if status in [REQUESTED, FORWARDED]:
        interactive_kwargs = dict(
            is_interactive=True,
            interactive_type=TRAVEL_ATTENDANCE_NOTIFICATION,
            interactive_data={
                "travel_request_id": travel_request.id,
                "organization": {
                    "name": travel_request.user.detail.organization.name,
                    "slug": travel_request.user.detail.organization.slug
                }
            }
        )
    else:
        interactive_kwargs = dict()

    subject = {
        REQUESTED: "Travel Attendance Request",
        FORWARDED: "Travel Attendance Request",
        APPROVED: "Travel Attendance Request Approved",
        DECLINED: "Travel Attendance Request Declined"
    }.get(status)

    email_type = email_travel_attendance.get(status)

    if recipient != get_system_admin():
        add_notification(
            actor=last_action_by,
            text=text,
            recipient=recipient,
            action=travel_request,
            url=url,
            **interactive_kwargs
        )

        if subject:
            send_email_as_per_settings(
                recipients=recipient,
                subject=subject,
                email_text=text,
                email_type=email_type
            )

    if settings.SHADOW_NOTIFY_ORGANIZATION_TRAVEL_ATTENDANCE or recipient == get_system_admin():
        hr_notification_text = (
            f"{last_action_by} has {status.lower()} "
            f"their {leave_range}."
        )

        if status != REQUESTED:
            hr_notification_text = hr_notification_text.replace(
                "their",
                f"{travel_request.user}'s"
            )

        organization = travel_request.user.detail.organization
        notify_organization(
            text=hr_notification_text,
            action=travel_request,
            organization=organization,
            actor=last_action_by,
            url=f'/admin/{organization.slug}/attendance/request/travel-attendance',
            permissions=[
                ATTENDANCE_PERMISSION,
                ATTENDANCE_TRAVEL_PERMISSION
            ],
            # **interactive_kwargs
        )
        if status in [REQUESTED, APPROVED, DECLINED]:
            send_email_as_per_settings(
                recipients=get_users_list_from_permissions(
                    organization=organization,
                    permission_list=[
                        ATTENDANCE_PERMISSION,
                        ATTENDANCE_TRAVEL_PERMISSION
                    ],
                    exclude_users=[last_action_by.id, recipient.id]
                ),
                subject=subject,
                email_text=hr_notification_text,
                email_type=email_type
            )


@receiver(post_save, sender=TravelAttendanceDeleteRequestHistory)
def send_email_for_travel_attendance_delete_request(sender, instance, created, **kwargs):
    """ send email for travel attendance delete request

    We have three types of users involved on travel delete request.

    * requester - one sending the travel delete request.
    * actor - one who acts on the request
    * recipient - one who should receive the email notification.

    We are sending two emails, one for recipient, and one for hr

    1. first email is for recipient
    2. second email is for hrs obtained via get_users_list_from_permissions

    constraints:
    * if recipient is system_admin, the action should be notified to hrs only
      regardless of the status.
    * if recipient is not system_admin, then shadow notification should be
      enabled and status shouldn't be FORWARDED, only then email should be
      sent to hr
    """
    delete_request = instance.delete_request
    status = delete_request.status
    if status == CANCELLED:
        return

    actor = instance.created_by
    requester = delete_request.travel_attendance.user

    if status in [APPROVED, DECLINED]:
        recipient = requester
    else:
        recipient = delete_request.recipient

    subject = {
        REQUESTED: "Travel Attendance Delete Request",
        FORWARDED: "Travel Attendance Delete Request",
        APPROVED: "Travel Attendance Delete Request Approved",
        DECLINED: "Travel Attendance Delete Request Declined"
    }.get(status)

    email_text = {
        REQUESTED: f"{requester} has sent travel attendance delete request.",
        FORWARDED: f"{requester} has sent travel attendance delete request.",
        APPROVED: f"Your travel attendance delete request has been approved by {actor}.",
        DECLINED: f"Your travel attendance delete request has been declined by {actor}.",
    }.get(status)

    hrs = get_users_list_from_permissions(
        organization=requester.detail.organization,
        permission_list=[
            ATTENDANCE_PERMISSION,
            ATTENDANCE_TRAVEL_PERMISSION
        ],
        exclude_users=[actor.id, recipient.id]
    )

    email_type = email_travel_attendance.get(status)

    if recipient != get_system_admin():
        send_email_as_per_settings(
            recipients=recipient,
            subject=subject,
            email_text=email_text,
            email_type=email_type
        )

    send_to_hr = False
    if recipient == get_system_admin():
        send_to_hr = True
    elif settings.SHADOW_NOTIFY_ORGANIZATION_TRAVEL_ATTENDANCE and status != FORWARDED:
        send_to_hr = True

    if not send_to_hr:
        return

    if status in [APPROVED, DECLINED]:
        email_text = email_text.replace("Your", f"{requester}'s")

    send_email_as_per_settings(
        recipients=hrs,
        subject=subject,
        email_text=email_text,
        email_type=email_type
    )


@receiver(post_save, sender=TravelAttendanceDeleteRequestHistory)
def create_travel_attendance_delete_request_notification(sender, instance, created, **kwargs):
    last_action_by = instance.created_by
    delete_request = instance.delete_request
    possessive_verb = {
        REQUESTED: 'a',
        FORWARDED: '',
        DECLINED: 'your',
        APPROVED: 'your',
        CANCELLED: 'their',
    }
    days_count = delete_request.deleted_days.count()
    leave_range = (
        "travel attendance delete request for "
        f"{days_count} day(s)."
    )
    action_text = delete_request.status.lower()

    if delete_request.status == FORWARDED:
        action_text += f" {delete_request.travel_attendance.user}'s "

    text = f"{last_action_by} has " \
           f"{action_text} " \
           f"{possessive_verb.get(delete_request.status)} " \
           f"{leave_range}"
    supervisor_url = '/user/supervisor/attendance/requests/travel-attendance-delete-request'
    self_url = '/user/attendance/reports/travel-attendance-delete-history'
    url = {
        REQUESTED: supervisor_url,
        FORWARDED: supervisor_url,
        DECLINED: self_url,
        APPROVED: self_url
    }.get(delete_request.status)

    if delete_request.status in [APPROVED, DECLINED]:
        recipient = delete_request.travel_attendance.user
    else:
        recipient = delete_request.recipient

    if delete_request.status in [REQUESTED, FORWARDED]:
        interactive_kwargs = dict(
            is_interactive=True,
            interactive_type=TRAVEL_ATTENDANCE_DELETE_NOTIFICATION,
            interactive_data={
                "delete_request_id": delete_request.id,
                "organization": {
                    "name": delete_request.travel_attendance.user.detail.organization.name,
                    "slug": delete_request.travel_attendance.user.detail.organization.slug
                }
            }
        )
    else:
        interactive_kwargs = dict()

    if not recipient == get_system_admin():
        add_notification(
            actor=last_action_by,
            text=text,
            recipient=recipient,
            action=delete_request,
            url=url,
            **interactive_kwargs
        )
    if settings.SHADOW_NOTIFY_ORGANIZATION_TRAVEL_ATTENDANCE or recipient == get_system_admin():
        hr_notification_text = " ".join(
            map(str, (
                last_action_by.full_name,
                'has',
                delete_request.status.lower(),
                (
                    'their' if delete_request.status == REQUESTED
                    else f"{delete_request.travel_attendance.user.full_name}'s"
                ),
                leave_range
            ))
        )
        organization = delete_request.travel_attendance.user.detail.organization
        notify_organization(
            text=hr_notification_text,
            action=delete_request,
            organization=organization,
            actor=last_action_by,
            url=f'/admin/{organization.slug}/attendance/request/travel-attendance-delete-request',
            permissions=[
                ATTENDANCE_PERMISSION,
                ATTENDANCE_TRAVEL_PERMISSION
            ]
            # **interactive_kwargs
        )


@receiver(post_save, sender=PreApprovalOvertimeHistory)
def create_pre_approval_request_notification(sender, instance, created, **kwargs):
    actor = instance.action_performed_by
    pre_approval = instance.pre_approval
    recipient = pre_approval.recipient
    user = pre_approval.sender
    date = pre_approval.overtime_date
    url = {
        REQUESTED: '/user/supervisor/attendance/requests/pre-approval-overtime',
        APPROVED: '/user/attendance/request/pre-approval-overtime',
        FORWARDED: '/user/supervisor/attendance/requests/pre-approval-overtime',
        DECLINED: '/user/attendance/request/pre-approval-overtime',
    }.get(instance.action_performed)

    if instance.action_performed == REQUESTED:
        notification_text = f"{actor.full_name} sent overtime approval request for {date}."

    elif instance.action_performed == FORWARDED:
        notification_text = f"{actor.full_name} forwarded " \
                            f"{user.full_name}'s" \
                            f" overtime for {date}."
    else:
        recipient = user
        notification_text = f"{actor.full_name} has " \
                            f"{instance.action_performed} your " \
                            f" overtime approval request for {date}."

    # notify organization here
    if instance.action_performed in [REQUESTED, FORWARDED]:
        interactive_kwargs = dict(
            is_interactive=True,
            interactive_type=OVERTIME_PRE_APPROVAL,
            interactive_data={
                "overtime_claim_id": pre_approval.id,
                "organization": {
                    "name": pre_approval.sender.detail.organization.name,
                    "slug": pre_approval.sender.detail.organization.slug
                }
            }
        )
    else:
        interactive_kwargs = dict()

    if recipient == get_system_admin() or settings.SHADOW_NOTIFY_ORGANIZATION_OVERTIME:
        hr_notification_text = " ".join(
            map(str, (
                actor.full_name,
                'has',
                instance.action_performed.lower(),
                (
                    'their' if instance.action_performed == REQUESTED
                    else f"{user.full_name}'s"
                ),
                'overtime request for',
                date
            ))
        )
        organization = user.detail.organization
        hr_url = (
            f'/admin/{organization.slug}/attendance/request/'
            f'overtime-request/?status={instance.action_performed}'
        )
        notify_organization(
            text=hr_notification_text,
            organization=organization,
            actor=actor,
            action=pre_approval,
            url=hr_url,
            permissions=[
                ATTENDANCE_PERMISSION,
                ATTENDANCE_OVERTIME_CLAIM_PERMISSION
            ],
            # **interactive_kwargs
        )
    if recipient != get_system_admin():
        add_notification(
            text=notification_text,
            actor=actor,
            action=pre_approval,
            recipient=recipient,
            url=url,
            **interactive_kwargs
        )


@receiver(post_save, sender=CreditHourRequestHistory)
def create_credit_hour_pre_approval_request_notification(sender, instance, created, **kwargs):
    actor = instance.action_performed_by
    credit_hour = instance.credit_hour
    recipient = credit_hour.recipient
    user = credit_hour.sender
    date = credit_hour.credit_hour_date
    subject = "Credit hour request"
    email_type = CREDIT_HOUR_APPROVAL_REQUESTED_FORWARDED_EMAIL
    url = {
        REQUESTED: '/user/supervisor/attendance/requests/credit-hour',
        APPROVED: '/user/attendance/request/credit-hour',
        FORWARDED: '/user/supervisor/attendance/requests/credit-hour',
        DECLINED: '/user/attendance/request/credit-hour',
    }.get(instance.action_performed)

    if instance.action_performed == REQUESTED:
        notification_text = f"{actor.full_name} sent credit hour request for {date}."

    elif instance.action_performed == FORWARDED:
        notification_text = f"{actor.full_name} forwarded " \
                            f"{user.full_name}'s" \
                            f" credit hour request for {date}."

    else:
        email_type = ACTION_ON_CREDIT_HOUR_EMAIL
        recipient = user
        subject = f"Credit hour request has been {instance.action_performed.lower()}"
        notification_text = f"{actor.full_name} has " \
                            f"{instance.action_performed.lower()} your" \
                            f" credit hour request for {date}."

    # notify organization here
    if instance.action_performed in [REQUESTED, FORWARDED]:
        interactive_kwargs = dict(
            is_interactive=True,
            interactive_type=CREDIT_HOUR_PRE_APPROVAL,
            interactive_data={
                "credit_hour_id": credit_hour.id,
                "organization": {
                    "name": credit_hour.sender.detail.organization.name,
                    "slug": credit_hour.sender.detail.organization.slug
                }
            }
        )
    else:
        interactive_kwargs = dict()

    if recipient == get_system_admin() or settings.SHADOW_NOTIFY_ORGANIZATION_CREDIT_REQUEST:
        hr_notification_text = " ".join(
            map(str, (
                actor.full_name,
                'has',
                instance.action_performed.lower(),
                (
                    'their' if instance.action_performed == REQUESTED
                    else f"{user.full_name}'s"
                ),
                'credit hour request for',
                f"{date}."
            ))
        )

        organization = user.detail.organization
        hr_url = (
            f"/admin/{organization.slug}/attendance/request/"
            f"credit-hour/?status={instance.action_performed}"
        )
        notify_organization(
            text=hr_notification_text,
            organization=organization,
            actor=actor,
            action=credit_hour,
            url=hr_url,
            permissions=[
                ATTENDANCE_PERMISSION,
                ATTENDANCE_CREDIT_HOUR_PERMISSION
            ],
            # **interactive_kwargs
        )

        # credit hour request to person having permission
        if instance.action_performed != FORWARDED:
            permissions_list = [ATTENDANCE_PERMISSION, ATTENDANCE_CREDIT_HOUR_REQUEST_PERMISSION]
            recipient_list = get_users_list_from_permissions(permissions_list, organization)
            if actor not in recipient_list:
                # sends email to persons in recipient list not to person performing the action
                send_email_as_per_settings(
                    recipient_list,
                    subject,
                    hr_notification_text,
                    email_type
                )

    if recipient != get_system_admin():
        add_notification(
            text=notification_text,
            actor=actor,
            action=credit_hour,
            recipient=recipient,
            url=url,
            **interactive_kwargs
        )

        if recipient != actor:
            send_email_as_per_settings(
                recipient,
                subject,
                notification_text,
                email_type
            )


@receiver(post_save, sender=TimeSheetReportRequestHistory)
def send_notification_on_action_timesheet_report_requests(sender, instance, created, **kwargs):
    request = instance.request
    month_name = request.month_name
    actor = instance.actor

    normal_url = '/user/attendance/request/timesheet'
    supervisor_url = '/user/supervisor/attendance/requests/timesheet'
    hr_url = f'/admin/{request.user.detail.organization.slug}/attendance/request/timesheet'

    action_url_text_map = {
        GENERATED: (
            f"Timesheet report for {month_name} has been generated.",
            normal_url,
            request.user
        ),
        REQUESTED: (
            f"{actor.full_name} has requested approval of timesheet report of {month_name}.",
            supervisor_url,
            request.recipient
        ),
        FORWARDED: (
            f"{actor.full_name} has forwarded approval for {request.user.full_name}'s "
            f"timesheet report of {month_name}.",
            supervisor_url,
            request.recipient
        ),
        APPROVED: (
            f"{actor.full_name} has approved {request.user.full_name}'s "
            f"timesheet report of {month_name} and awaits confirmation.",
            hr_url,
            None
        ),
        DECLINED: (
            f"{actor.full_name} has declined approval of timesheet report of {month_name}.",
            normal_url,
            request.user
        ),
        CONFIRMED: (
            f"{actor.full_name} has confirmed timesheet report of {month_name}.",
            normal_url,
            request.user
        ),
    }

    interactive_data = dict(
        is_interactive=True,
        interactive_type=TIMESHEET_REPORT,
        interactive_data={
            'timesheet_report_id': request.id,
            'organization': {
                'name': request.user.detail.organization.name,
                'slug': request.user.detail.organization.slug,
            }
        }
    )
    text, url, recipient = action_url_text_map[instance.action]
    if url == hr_url or recipient == get_system_admin():
        notify_organization(
            text,
            action=instance,
            actor=instance.actor,
            organization=request.user.detail.organization,
            permissions=[ATTENDANCE_PERMISSION, ATTENDANCE_TIMESHEET_REPORT_PERMISSION],
            url=hr_url
        )
    else:
        add_notification(
            text=text,
            action=instance,
            actor=instance.actor,
            recipient=recipient,
            url=url,
            **interactive_data
        )

    if instance.action in [REQUESTED, DECLINED]:
        if instance.action == DECLINED:
            text = text + f' for {request.user.full_name}.'
        notify_organization(
            text,
            action=instance,
            actor=instance.actor,
            organization=request.user.detail.organization,
            permissions=[ATTENDANCE_PERMISSION, ATTENDANCE_TIMESHEET_REPORT_PERMISSION],
            url=hr_url
        )


def recalibrate_credit_hour_when_timesheet_is_updated(timesheet, actor, action_type) -> None:
    """
    Recalibrate only if credit hour requires prior approval
    and reduce logic is true.
    :param timesheet: Timesheet to which update was performed.
    :param actor: Who approved the changes to timesheet.
    :param action_type: Reason for the changes, Offline-Attendance/Adjustment, etc.
    """
    credit_timesheet_entry = timesheet.credit_entries.filter(
        credit_setting__require_prior_approval=True,
        credit_setting__reduce_credit_if_actual_credit_lt_approved_credit=True,
        status=APPROVED,
    ).first()
    if not credit_timesheet_entry:
        return
    performed = perform_credit_hour_recalibration(credit_timesheet_entry)
    if not performed:
        return
    remark = f're-calibrated for {timesheet.timesheet_for} '
    if actor:
        if action_type:
            remark += f'after {ACTION_TYPES.get(action_type, action_type)}'
        else:
            remark += 'after action'
        remark += f' by {actor}'
    credit_hour_frontend = '/user/attendance/request/credit-hour'
    recipient = timesheet.timesheet_user
    ws_remark = f'Your credit hour balance claim has been ' + remark
    add_notification(
        actor=get_system_admin(),
        text=ws_remark,
        recipient=recipient,
        action=timesheet,
        url=credit_hour_frontend
    )
    return


@receiver(post_save, sender=CreditHourDeleteRequestHistory)
def create_credit_hour_pre_approval_delete_request_notification(sender, instance, created,
                                                                **kwargs):
    actor = instance.action_performed_by
    delete_request = instance.delete_request
    recipient = delete_request.recipient
    user = delete_request.sender
    date = delete_request.request.credit_hour_date
    subject = "Credit hour delete request"
    email_type = CREDIT_HOUR_DELETE_REQUEST_IS_REQUESTED_FORWARDED_EMAIL
    url = {
        REQUESTED: '/user/supervisor/attendance/requests/credit-hour-delete-request',
        APPROVED: '/user/attendance/reports/credit-hour-delete-history',
        FORWARDED: '/user/supervisor/attendance/requests/credit-hour-delete-request',
        DECLINED: '/user/attendance/reports/credit-hour-delete-history',
    }.get(instance.action_performed)

    if instance.action_performed == REQUESTED:
        notification_text = f"{actor.full_name} sent credit hour delete request for {date}."

    elif instance.action_performed == FORWARDED:
        notification_text = f"{actor.full_name} forwarded " \
                            f"{user.full_name}'s" \
                            f" credit hour delete request for {date}."
    else:
        email_type = CREDIT_HOUR_DELETE_REQUEST_IS_APPROVED_DECLINED_EMAIL
        recipient = user
        subject = f"Credit hour delete request has been {instance.action_performed.lower()}"
        notification_text = f"{actor.full_name} has " \
                            f"{instance.action_performed} your " \
                            f" credit hour delete request for {date}."

    # notify organization here
    if instance.action_performed in [REQUESTED, FORWARDED]:
        interactive_kwargs = dict(
            is_interactive=True,
            interactive_type=CREDIT_HOUR_PRE_APPROVAL_DELETE,
            interactive_data={
                "credit_hour_delete_request_id": delete_request.id,
                "organization": {
                    "name": delete_request.sender.detail.organization.name,
                    "slug": delete_request.sender.detail.organization.slug
                }
            }
        )
    else:
        interactive_kwargs = dict()

    if recipient == get_system_admin() or settings.SHADOW_NOTIFY_ORGANIZATION_CREDIT_REQUEST:
        hr_notification_text = " ".join(
            map(str, (
                actor.full_name,
                'has',
                instance.action_performed.lower(),
                (
                    'their' if instance.action_performed == REQUESTED
                    else f"{user.full_name}'s"
                ),
                'credit hour delete request for',
                date
            ))
        )
        organization = user.detail.organization
        hr_url = (
            f'/admin/{organization.slug}/attendance/request'
            f'/credit-hour-delete-request/?status={instance.action_performed}'
        )

        notify_organization(
            text=hr_notification_text,
            organization=organization,
            actor=actor,
            action=delete_request,
            url=hr_url,
            permissions=[
                ATTENDANCE_PERMISSION,
                ATTENDANCE_CREDIT_HOUR_PERMISSION
            ],
            # **interactive_kwargs
        )

        if instance.action_performed != FORWARDED:
            permissions_list = [ATTENDANCE_PERMISSION, ATTENDANCE_CREDIT_HOUR_REQUEST_PERMISSION]
            recipient_list = get_users_list_from_permissions(permissions_list, organization)
            if actor not in recipient_list:
                send_email_as_per_settings(
                    recipient_list,
                    subject,
                    hr_notification_text,
                    email_type
                )

    if recipient != get_system_admin():
        add_notification(
            text=notification_text,
            actor=actor,
            action=delete_request,
            recipient=recipient,
            url=url,
            **interactive_kwargs
        )
    
    if recipient != actor:
        send_email_as_per_settings(
            recipient,
            subject,
            notification_text,
            email_type
        )


@receiver(post_save, sender=WorkShift)
def create_workshift_legend(sender, instance, created, **kwargs):
    if created:
        WorkShiftLegend.objects.create(shift=instance, legend_text=instance.name[:2].upper(),
                                       legend_color='#9E9E9EFF', )

