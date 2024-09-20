"""@irhrs_docs"""
import logging

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from irhrs.core.constants.common import INTERACTIVE_NOTIFICATION_CHOICES
from irhrs.core.utils import get_system_admin, nested_get, nested_getattr
from irhrs.notification.api.v1.serializers.notification import \
    NotificationSerializer, OrganizationNotificationSerializer
from irhrs.notification.models.notification import OrganizationNotification
from irhrs.permission.models import HRSPermission
from irhrs.websocket.helpers import send_for_group as websocket_group
from .models import Notification

USER = get_user_model()


def extract_interactive_kwargs(kwargs):
    is_interactive = kwargs.get('is_interactive', False)
    if not is_interactive:
        return dict()

    interactive_type = kwargs.get('interactive_type')
    assert ((interactive_type, interactive_type) in INTERACTIVE_NOTIFICATION_CHOICES), "Invalid Interactive Type."

    interactive_data = kwargs.get('interactive_data', dict())
    assert isinstance(interactive_data, dict)

    return {
        'is_interactive': is_interactive,
        'interactive_type': interactive_type,
        'interactive_data': interactive_data
    }


def add_notification(text, recipient, action, **kwargs):
    """
    add notification function

    :argument recipient: someone who receives notification.
    :type recipient: USER
        Can be USER instance or an iterable
        containing multiple USER instances

    :argument text: Notification Text
    :type text: str

    :argument action: Action Object
    :type action: object

    :key label: Label of notification

    :key actor: someone who sends notification

    :key sticky: sticky nature of notification

    :key can_be_reminded: whether notification can be reminded or not
    """
    if not recipient:
        # If no recipient, do nothing
        return

    if recipient == get_system_admin():
        # This scenario occurs when user whose supervisor is RealHRBot requests
        # 1) Leave Request
        # 2) Attendance Adjustment
        # 3) Overtime Request
        # 4) Timesheet Report Request
        # The request will be valid, but as RealHRBot can not login and approve
        # requests, we shall forward this request to HR.

        # Making HR Notifications non-interactive as not currently processed by FE.
        kwargs['is_interactive'] = False

        actor = kwargs.get('actor')
        target_organization = nested_getattr(actor, 'detail.organization')
        if target_organization:
            notify_organization(
                text=text,
                action=action,
                organization=target_organization,
                actor=actor
            )
        else:
            logging.warning(
                "Failed to send this notification: "
                + text
                + " as no organization was found"
            )
        return
    if isinstance(recipient, USER):
        recipient = [recipient]

    label = kwargs.get('label', None)
    actor = kwargs.get('actor', None)
    sticky = kwargs.get('sticky', False)
    can_be_reminded = kwargs.get('can_be_reminded', False)
    url = kwargs.get('url', None)

    context = {
        'action': action,
        'text': text,
        'sticky': sticky,
        'can_be_reminded': can_be_reminded,
        'url': url
    }

    if actor is None:
        context.update({'actor': get_system_admin()})
    else:
        context.update({'actor': actor})

    if label is not None:
        context.update({'label': label})

    # get interactive kwargs
    context.update(extract_interactive_kwargs(kwargs))

    notifications = []
    for rec in recipient:
        if actor == rec:
            # no need to send notification of her/his actions
            continue
        notifications.append(Notification(recipient=rec, **context))
    instances = Notification.objects.bulk_create(notifications)
    for notify in instances:
        ser = NotificationSerializer(instance=notify)
        _success = websocket_group(str(notify.recipient.id), ser.data,
                                   msg_type='notification')


def read_notifications(notifications):
    """
    read notifications
    :param notifications: notifications to read
    :type notifications: QuerySet
    :return: None
    """
    # sticky notifications are automatically read once detail is visited or
    # acknowledged in case of HR_NOTICE,
    notifications.filter(read=False, sticky=False,
                         notify_on__lte=timezone.now()
                         ).update(read=True)


def read_notification(notification):
    """
    Read single notification
    :param notification: notification to read
    :type notification: Notification
    :return: None
    """
    if not notification.sticky or notification.notify_on > timezone.now():
        notification.read = True
        notification.save()


def remind_notification_at(notification, datetime):
    """set reminder for notification"""
    if not notification.sticky and notification.can_be_reminded:
        notification.notify_on = datetime
        notification.read = False
        notification.save()
        return True
    else:
        return False


def get_notifications(action, actor):
    """
    Notification lists by given user for given action
    """
    content_type = ContentType.objects.get_for_model(action)
    return Notification.objects.filter(
        action_content_type=content_type,
        action_object_id=action.id,
        actor=actor
    )


def notify_organization(text, action, organization, **kwargs):
    label = kwargs.get('label', None)
    actor = kwargs.get('actor', None) or get_system_admin()
    url = kwargs.get('url', '')
    permissions = kwargs.get('permissions', [])

    permission_codes = {x.get('code') for x in permissions}
    context = {
        'actor': actor,
        'text': text,
        'url': url,
        'action': action,
        'recipient': organization,
        'associated_permissions': list(permission_codes)
    }

    if label:
        context['label'] = label

    context.update(extract_interactive_kwargs(kwargs))

    notification = OrganizationNotification.objects.create(
        **context
    )

    ser = OrganizationNotificationSerializer(instance=notification)
    websocket_group(
        f'org_{organization.slug}',
        ser.data,
        msg_type='org_notification'
    )
