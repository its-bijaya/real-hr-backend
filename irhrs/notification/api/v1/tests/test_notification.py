from time import sleep
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import tag
from django.urls import reverse
from django.utils import timezone

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.constants.common import LEAVE_REQUEST_NOTIFICATION
from irhrs.notification.models import Notification
from irhrs.notification.utils import add_notification
from irhrs.users.models import UserDetail


class TestNotification(RHRSAPITestCase):
    users = [("test@example.com", "secretThingIsHere", "Male"),
             ("testone@example.com", "secretThingIsHere", "Female")]
    organization_name = "Organization"

    def setUp(self):
        super().setUp()
        self.client.login(username=self.users[0][0], password=self.users[0][1])
        # Delete all notifications before test
        Notification.objects.all().delete()

    def test_create(self):
        # create a notification using our add_notification
        userdetail = UserDetail.objects.get(user__email=self.users[0][0])
        notification_cases = [{
            "action": self.organization,
            "text": "Updated organization status",
            "recipient": userdetail.user
        }, {
            "action": self.organization,
            "text": "Updated organization status",
            "recipient": userdetail.user,
            "is_interactive": True,
            "interactive_type": LEAVE_REQUEST_NOTIFICATION,
            "interactive_data": {}
        }]
        for data in notification_cases:
            Notification.objects.all().delete()

            add_notification(**data)

            notification_count = Notification.objects.all().count()
            self.assertEqual(notification_count, 1)

            notification = Notification.objects.all()[0]
            for attr in data:
                self.assertEqual(getattr(notification, attr, None), data.get(attr), f"Failed for {data}")

    def test_list(self):
        """Covers list and read_all operations"""
        url = reverse('api_v1:notification:notifications-list')
        url_read_all = reverse('api_v1:notification:notifications-read-all')
        userdetail1 = UserDetail.objects.get(user__email=self.users[0][0])
        userdetail2 = UserDetail.objects.get(user__email=self.users[1][0])

        notifications_data = [
            {
                "action": self.organization,
                "text": f"Updated organization status {i}",
                "recipient": userdetail1.user
            }
            for i in range(0, 5)
        ]

        notifications_data += [
            {
                "action": self.organization,
                "text": f"Updated organization status {i*2}",
                "recipient": userdetail2.user
            }
            for i in range(0, 5)
        ]

        for data in notifications_data:
            add_notification(**data)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 5)

        # get unread notifications
        response = self.client.get(url, data={'read': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 5)

        # get read notifications
        response = self.client.get(url, data={'read': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 0)

        # read all notifications
        response = self.client.post(url_read_all)
        self.assertEqual(response.status_code, 200)

        # check numbers again
        # get unread notifications
        response = self.client.get(url, data={'read': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 0)

        # get read notifications
        response = self.client.get(url, data={'read': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 5)

        # login with other user and check
        self.client.login(email=self.users[1][0], password=self.users[1][1])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 5)

        # get unread notifications
        response = self.client.get(url, data={'read': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 5)

        # get read notifications
        response = self.client.get(url, data={'read': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 0)

        # read all notifications
        response = self.client.post(url_read_all)
        self.assertEqual(response.status_code, 200)

        # check numbers again
        # get unread notifications
        response = self.client.get(url, data={'read': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 0)

        # get read notifications
        response = self.client.get(url, data={'read': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 5)

    def test_notification_retrieve(self):
        # although no url to retrieve, we'll check for data consistency here
        userdetail = UserDetail.objects.get(user__email=self.users[0][0])
        data = {
            "action": self.organization,
            "text": "Updated organization status",
            "recipient": userdetail.user,
            "url": "/xyz"
        }
        add_notification(**data)

        url = reverse('api_v1:notification:notifications-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 1)

        notification_data = response.data.get('results')[0]

        self.assertEqual(notification_data.get('url'), data.get('url'))
        self.assertEqual(notification_data.get('text'), data.get('text'))

        # notification with id in action_data
        userdetail = UserDetail.objects.get(user__email=self.users[0][0])
        data = {
            "action": userdetail.user,
            "text": "Updated your userdetail",
            "recipient": userdetail.user,
            "url": "/asds"
        }
        add_notification(**data)

        url = reverse('api_v1:notification:notifications-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 2)

        # recent notification is on top
        notification_data = response.data.get('results')[0]

        self.assertEqual(notification_data.get('url'), data.get("url"))
        self.assertEqual(notification_data.get('text'), data.get('text'))

    @tag('slow')
    def test_remind_me_later(self):
        url = reverse('api_v1:notification:notifications-list')
        userdetail = UserDetail.objects.get(user__email=self.users[0][0])
        data = {
            "action": self.organization,
            "text": "Updated organization status",
            "recipient": userdetail.user,
            "can_be_reminded": True
        }
        add_notification(**data)

        # check notification
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 1)

        # set reminder
        notification_id = Notification.objects.first().id
        remind_url = reverse('api_v1:notification:notifications-remind',
                             kwargs={'pk': notification_id})
        remind_at = timezone.now() + timezone.timedelta(seconds=50)
        data = {
            'remind_at': remind_at
        }

        # Notification not shown now
        response = self.client.post(remind_url, data=data)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 0)

        # check what happens tomorrow
        with patch('django.utils.timezone.now', return_value=timezone.now() + timezone.timedelta(days=1)):
            # after 1 min it should be shown
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data.get('count'), 1)

            # setting past date < in this case same data again >
            response = self.client.post(remind_url, data=data)
            self.assertEqual(response.status_code, 400)

            # setting invalid date format
            data = {"remind_at": "201220122012"}
            response = self.client.post(remind_url, data=data)
            self.assertEqual(response.status_code, 400)

    def test_notification_can_not_be_reminded(self):
        userdetail = UserDetail.objects.get(user__email=self.users[0][0])
        data = {
            "action": self.organization,
            "text": "Updated organization status",
            "recipient": userdetail.user,
            "can_be_reminded": False
        }
        add_notification(**data)

        notification_id = Notification.objects.first().id
        remind_url = reverse('api_v1:notification:notifications-remind',
                             kwargs={'pk': notification_id})
        remind_at = timezone.now() + timezone.timedelta(seconds=50)
        data = {
            'remind_at': remind_at
        }

        # Notification not shown now
        response = self.client.post(remind_url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_sticky(self):
        # try to remind sticky notification
        userdetail = UserDetail.objects.get(user__email=self.users[0][0])
        data = {
            "action": self.organization,
            "text": "Updated organization status",
            "recipient": userdetail.user,
            "sticky": True,
            "can_be_reminded": True
        }
        add_notification(**data)

        notification = Notification.objects.first()
        remind_url = reverse('api_v1:notification:notifications-remind',
                             kwargs={'pk': notification.id})
        remind_at = timezone.now() + timezone.timedelta(seconds=50)
        data = {
            'remind_at': remind_at
        }

        response = self.client.post(remind_url, data=data)
        self.assertEqual(response.status_code, 400)

        # test read of sticky notice should not be read
        read_url = reverse('api_v1:notification:notifications-read',
                           kwargs={'pk': notification.id})

        self.assertFalse(notification.read)
        response = self.client.post(read_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(notification.read)

    def test_read_notification(self):
        userdetail1 = UserDetail.objects.get(user__email=self.users[0][0])
        notifications_data = [
            {
                "action": self.organization,
                "text": f"Updated organization status {i}",
                "recipient": userdetail1.user
            }
            for i in range(0, 5)
        ]

        for data in notifications_data:
            add_notification(**data)

        # get a notification
        notification = Notification.objects.filter(recipient=userdetail1.user,
                                                   read=False)[0]
        read_url = reverse('api_v1:notification:notifications-read',
                           kwargs={'pk': notification.pk})
        response = self.client.post(read_url)
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()

        self.assertEqual(notification.read, True)
