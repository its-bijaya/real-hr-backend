from datetime import timedelta
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from irhrs.event.api.v1.tests.setup import MeetingSetup
from irhrs.event.models import EventDetail
from irhrs.event.tasks import send_meeting_notification
from irhrs.notification.models import Notification


class TestMeetingNotificationBackgroundTask(MeetingSetup):
    def test_meeting_notification_background_task(self):
        _no_of_members = self.meeting.meeting_attendances.all()  # added one for meeting creator
        content_type = ContentType.objects.get_for_model(EventDetail)
        for minute in range(10, 60, 10):
            with patch('django.utils.timezone.now',
                       return_value=timezone.now() + timedelta(minutes=minute)):
                send_meeting_notification()
                notifications = Notification.objects.filter(
                    action_content_type=content_type,
                    action_object_id=self.meeting.id
                )
                self.assertEqual(
                    notifications.count(),
                    _no_of_members.count() * (minute // 10)
                )
        notified_user = list(set(notifications.values_list('recipient_id', flat=True)))
        meeting_members = list(_no_of_members.values_list('member_id', flat=True))
        notified_user.sort()
        meeting_members.sort()
        self.assertListEqual(
            notified_user,
            meeting_members
        )
