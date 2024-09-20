from django.conf import settings
from django.db.models import F
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver

from cuser.middleware import CuserMiddleware

from irhrs.core.constants.common import LEAVE_REQUEST_NOTIFICATION
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import is_supervisor_of
from irhrs.leave.constants.model_constants import (
    REQUESTED, APPROVED, DENIED, FORWARDED,
    RENEWED, ADDED, DEDUCTED, UPDATED,
    REMOVED, COMPENSATORY, APPROVER, SUPERVISOR)
from irhrs.leave.models import LeaveAccountHistory, LeaveRequestHistory, \
    LeaveRequest, MasterSetting
from django.db import connection, reset_queries

from irhrs.leave.utils.timesheet import revert_timesheet_for_leave
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.permission.constants.permissions import LEAVE_REQUEST_PERMISSION

NOTIFY_ORGANIZATION_LEAVE_REQUEST = settings.SHADOW_NOTIFY_ORGANIZATION_LEAVE_REQUEST


@receiver(post_save, sender=LeaveRequestHistory)
def create_leave_request_notification(sender, instance, created, **kwargs):
    last_action_by = instance.actor
    leave_request = instance.request
    possessive_verb = {
        REQUESTED: 'a',
        FORWARDED: '',
        DENIED: 'your',
        APPROVED: 'your'
    }
    if 0 < leave_request.balance < 1:
        leave_range = f"half day leave for {leave_request.start.astimezone().date()}"
    elif leave_request.balance > 1:
        leave_range = f"leave from {leave_request.start.astimezone().date()} to " \
                      f"{leave_request.end.astimezone().date()}"
    else:
        leave_range = f"leave for {leave_request.start.astimezone().date()}"
    action_text = leave_request.status.lower()

    if leave_request.status == FORWARDED:
        action_text += f' {leave_request.user}\'s '

    text = f"{last_action_by} has " \
           f"{action_text} " \
           f"{possessive_verb.get(leave_request.status)} " \
           f"{leave_range}"

    supervisor_url = '/user/supervisor/leave/requests'

    if instance.recipient_type == APPROVER:
        supervisor_url = '/user/leave/employee-request'

    self_url = '/user/leave/history'
    url = {
        REQUESTED: supervisor_url,
        FORWARDED: supervisor_url,
        DENIED: self_url,
        APPROVED: self_url
    }.get(leave_request.status)

    if leave_request.status in [APPROVED, DENIED]:
        recipient = leave_request.leave_account.user
    else:
        recipient = leave_request.recipient

    if leave_request.status in [REQUESTED, FORWARDED] and instance.recipient_type == SUPERVISOR:
        interactive_kwargs = dict(
            is_interactive=True,
            interactive_type=LEAVE_REQUEST_NOTIFICATION,
            interactive_data={
                "leave_request_id": leave_request.id,
                "organization": {
                    "name": leave_request.user.detail.organization.name,
                    "slug": leave_request.user.detail.organization.slug
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
            action=leave_request,
            url=url,
            **interactive_kwargs
        )
    if recipient == get_system_admin() or NOTIFY_ORGANIZATION_LEAVE_REQUEST:
        hr_notification_text = " ".join(
            map(str, (
                last_action_by.full_name,
                'has',
                action_text,
                (
                    'their' if leave_request.status == REQUESTED
                    else f"{leave_request.user}'s"
                ),
                leave_range
            ))
        )
        organization = leave_request.leave_account.user.detail.organization
        notify_organization(
            text=hr_notification_text,
            action=leave_request,
            organization=organization,
            actor=last_action_by,
            url=f'/admin/{organization.slug}/leave/employees-request',
            permissions=[LEAVE_REQUEST_PERMISSION],
            # **interactive_kwargs
        )


@receiver(post_save, sender=LeaveAccountHistory)
def create_leave_balance_update_notification(sender, instance, *args, **kwargs):
    """
    Sends notification to a user, if there has been balance updates to
    his/her account.
    :param sender:
    :param instance:
    :param args:
    :param kwargs:
    :return:
    """

    # Do not send notification if there has been any update to usable balance
    # only. So, we will check if the action is ADDED(+) or DEDUCTED(-)
    if instance.action in (ADDED, DEDUCTED):
        if (
            # actual balance is unaffected
            instance.new_balance == instance.previous_balance
        ) and (
            # only usable balance is affected.
            instance.new_usable_balance != instance.previous_usable_balance
        ):
            return

    account_name = str(instance.account.rule.leave_type)
    notification_content = {
        REMOVED: f'Your Leave Account {account_name} has been terminated.',
        RENEWED: f'Your Leave Account {account_name} has been renewed.',
        ADDED: f'Your Leave balance for {account_name} has incremented.',
        DEDUCTED: f'Your Leave balance for {account_name} has decremented.',
        UPDATED: f'Your leave Account {account_name} has been updated by '
                 f'{instance.actor} with remarks: {instance.remarks}'
    }.get(instance.action)
    if not notification_content:
        return
    url = f"/user/leave/request"
    recipient = instance.account.user
    add_notification(
        actor=get_system_admin(),
        text=notification_content,
        recipient=recipient,
        action=instance,
        url=url,
    )


@receiver(post_save, sender=LeaveRequestHistory)
def manage_compensatory_account(sender, instance, *args, **kwargs):
    """
    Updates Compensatory Leave Account. i.e. consumption of a compensatory
    Leave after the leave has been approved.
    :param sender:
    :param instance:
    :param args:
    :param kwargs:
    :return:
    """
    # Filter only compensatory leave rule types.
    reset_queries()
    if instance.action == APPROVED:
        leave_account = instance.request.leave_account
        if not leave_account.rule.leave_type.category == COMPENSATORY:
            return
        balance_consumed = instance.request.balance
        reduce_from = leave_account.compensatory_leave.filter(
            balance_granted__gt=F('balance_consumed')
        ).order_by(
            'leave_for'
        )
        balance_to_reduce = balance_consumed
        for day in reduce_from:
            consumable = day.balance_granted - day.balance_consumed
            if balance_to_reduce == 0:
                break
            elif balance_to_reduce >= consumable:
                balance_to_reduce -= consumable
                day.balance_consumed += consumable
            else:
                day.balance_consumed += balance_to_reduce
                balance_to_reduce = 0
            day.save()
        # the request that reaches here is from a compensatory leave account,
        # and the request has been approved.


@receiver(pre_delete, sender=LeaveRequest)
def revert_compensatory_consumption(sender, instance, *args, **kwargs):
    url = '/user/leave/request'

    revert_timesheet_for_leave(instance)
    leave_account = instance.leave_account

    actor = CuserMiddleware.get_user(get_system_admin())

    add_notification(
        actor=actor,
        text=f'Your leave request has been deleted by {actor.full_name}.',
        recipient=instance.user,
        action=instance,
        url=url
    )

    if not leave_account.rule.leave_type.category == COMPENSATORY:
        return
    balance_consumed = instance.balance
    reduce_from = leave_account.compensatory_leave.filter(
        balance_consumed__lte=F('balance_granted')
    ).order_by(
        '-leave_for'
    )
    for day in reduce_from:
        addable = day.balance_consumed
        if balance_consumed == 0:
            break
        elif balance_consumed >= addable:
            balance_consumed -= addable
            day.balance_consumed -= addable
        else:
            day.balance_consumed -= balance_consumed
            balance_consumed = 0
        day.save()


@receiver(pre_delete, sender=MasterSetting)
def un_expire_master_setting(sender, instance, *args, **kwargs):
    """
    When an idle master setting is deleted,
    Set currently active master setting's effective till to None
    Which is set as (effective_till set to idle.effective - day(1))
    """
    MasterSetting.objects.all().active().filter(
        organization=instance.organization
    ).update(effective_till=None)
