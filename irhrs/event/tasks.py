import logging
import textwrap
from datetime import timedelta

from django.db.models import Prefetch
from django.utils import timezone

from irhrs.event.models import EventDetail, MeetingNotification
from irhrs.event.utils import get_event_frontend_url
from irhrs.notification.utils import add_notification

logger = logging.getLogger(__name__)


def send_meeting_notification():
    """
    Task for sending notification for meeting

    :return:
    """

    meetings = EventDetail.objects.select_related('event').filter(
        event__start_at__gt=timezone.now().astimezone()
    ).prefetch_related(
        Prefetch(
            'notifications',
            queryset=MeetingNotification.objects.filter(notified=False),
            to_attr='notification'
        )
    )
    for meeting in meetings:
        title = textwrap.shorten(text=meeting.event.title, width=30)
        notification_times = meeting.notification
        start_at = meeting.event.start_at.astimezone()
        duration = start_at - timezone.now().astimezone()

        for notification_time in notification_times:
            if timedelta(minutes=notification_time.time) > duration:
                notification_text = f'Meeting `{title}` is going to be held on {start_at.strftime("%m/%d/%Y, %I:%M %p")}.'
                notification_url = get_event_frontend_url(meeting.event)
                for attendance in meeting.meeting_attendances.all():
                    add_notification(
                        recipient=attendance.member,
                        text=notification_text,
                        actor=None,
                        action=attendance.meeting,
                        url=notification_url,
                    )
                    logger.debug(f'*** Notification send to {attendance.member}***')
                notification_time.notified = True
                notification_time.save()
