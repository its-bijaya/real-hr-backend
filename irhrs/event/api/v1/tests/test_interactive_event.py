import json

from datetime import timedelta
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.event.api.v1.tests.setup import EventSetUp
from irhrs.event.constants import OUTSIDE, SEMINAR
from irhrs.event.models import Event
from irhrs.noticeboard.models import Post


class TestInteractiveEvent(EventSetUp):

    def payload(self):
        member_id = self.members[0][1]
        data = {
                'title': self.fake.text(max_nb_chars=100),
                'start_at': timezone.now() + timedelta(days=1),
                'end_at': timezone.now() + timedelta(days=2),
                'event_location': OUTSIDE,
                'description': self.fake.text(max_nb_chars=10),
                'location': self.fake.address(),
                'event_category': SEMINAR
            }
        eventdetail = {
            "minuter": member_id,
            "time_keeper": member_id
        }

        data.update({
            "eventdetail": json.dumps(eventdetail)
        })
        return data

    def test_creating_interactive_events(self):
        self._create_interactive_event_for_test()

    def _create_interactive_event_for_test(self, data=None):
        if not data:
            data = self.payload()
            data.update({
                'interactive_event': True
            })
            data = [(key, value) for key, value in data.items()] + self.members
        _data = urlencode(data)
        response = self.client.post(
            self.event_list_url, data=_data,
            content_type='application/x-www-form-urlencoded'
        )
        event = Event.objects.get(id=response.data.get('id'))
        _members_count = event.members.all().count()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['title'], event.title)
        self.assertEqual(response.data['members']['members_count'],
                         _members_count)
        return event

    def test_adding_post_on_interactive_event_by_member(self):
        post_url = reverse(
            "api_v1:noticeboard:post-list"
        )

        event = self._create_interactive_event_for_test()
        data = [
            ("post_content", self.fake.text(max_nb_chars=10000)),
            ("post_type_id", event.id),
            ("post_type", 'Event')
        ]
        _data = urlencode(data)
        response = self.client.post(
            post_url, data=_data,
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        posted_data = Post.objects.filter(object_id=event.id,
                                          content_type=self.content_type)
        self.assertTrue(posted_data.exists())

        ########################################################################
        #                          For Event Members                           #
        ########################################################################

        """
        ------------------------------------------------------------------------
        Test to add a post for an interactive event by member
        result => must be able to add post for event
        """
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        response = self.client.post(
            post_url, data=_data,
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        posted_data = Post.objects.filter(
            id=response.data.get('id'),
            object_id=event.id,
            content_type=self.content_type
        )
        self.assertTrue(posted_data.exists())
        post = posted_data.first()

        """
        ------------------------------------------------------------------------
        Test for like a post for an interactive event by member
        result => must be able to like a post for event
        """
        post_like_url = reverse(
            "api_v1:noticeboard:post-like-list",
            kwargs={
                'post_id': post.id
            }
        )
        data_like = {"liked": True}
        response = self.client.post(
            post_like_url,
            data=data_like,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = self.user.objects.get(email=self.users[1][0])
        self.assertEqual(response.data.get('liked_by').get('id'), user.id)
        self.assertTrue(post.likes.filter(liked_by=user).exists())

        """
        ------------------------------------------------------------------------
        Test for commenting a post for an interactive event by member
        result => must be able to add comment for a post in event
        """
        post_comment_url = reverse(
            "api_v1:noticeboard:post-comment-list",
            kwargs={
                'post_id': post.id
            }
        )

        data_cmt = {"content": self.fake.text()}
        response = self.client.post(
            post_comment_url,
            data=data_cmt,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = self.user.objects.get(email=self.users[1][0])
        self.assertEqual(response.data.get('commented_by').get('id'), user.id)
        self.assertTrue(post.comments.filter(commented_by=user).exists())
        comment = post.comments.first()

        """
        ------------------------------------------------------------------------
        Test for replying a comment for a post for an interactive event by member
        result => must be able to reply comment for a post in event
        """
        self.client.login(email=self.users[2][0], password=self.users[2][1])
        comment_reply_url = reverse(
            "api_v1:noticeboard:comment-reply-list",
            kwargs={
                'comment_id': comment.id
            }
        )

        data_reply = {"reply": self.fake.text()}
        response = self.client.post(
            comment_reply_url,
            data=data_reply,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = self.user.objects.get(email=self.users[2][0])
        self.assertEqual(data_reply.get('reply'), response.data.get('reply'))
        self.assertEqual(response.data.get('reply_by').get('id'), user.id)
        self.assertTrue(comment.replies.filter(reply_by=user).exists())

        """
        ------------------------------------------------------------------------
        Test for replying a comment for a post for an interactive event by member
        result => must be able to reply comment for a post in event
        """
        comment_like_url = reverse(
            "api_v1:noticeboard:comment-like-list",
            kwargs={
                'comment_id': comment.id
            }
        )

        response = self.client.post(
            comment_like_url,
            data=data_like,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = self.user.objects.get(email=self.users[2][0])
        self.assertEqual(data_like.get('liked'), response.data.get('liked'))
        self.assertEqual(response.data.get('liked_by').get('id'), user.id)
        self.assertTrue(comment.likes.filter(liked_by=user).exists())

        """
        ------------------------------------------------------------------------
        trying to add post on disabled event by event member
        result => must not be able to add post on disabled event
        """
        event.enabled_event = False
        event.save()

        self._test_for_disabled_event_and_permission_for_event_post(
            url_data={
                'path': post_url,
                'data': _data,
                'content_type': 'application/x-www-form-urlencoded'
            },
            field='post_type'
        )

        """
        ------------------------------------------------------------------------
        trying to comment a post on disabled event by event member
        result => must not be able to comment a post on disabled event
        """
        self._test_for_disabled_event_and_permission_for_event_post(
            url_data={
                'path': post_comment_url,
                'data': data_cmt,
                'format': "json"
            },
            field='post'
        )

        """
        ------------------------------------------------------------------------
        trying to like a comment on disabled event by event member
        result => must not be able to like a comment on disabled event
        """
        self._test_for_disabled_event_and_permission_for_event_post(
            url_data={
                'path': comment_like_url,
                'data': data_like,
                'format': "json"
            },
            field='post'
        )

        """
        ------------------------------------------------------------------------
        trying to reply a comment on disabled event by event member
        result => must not be able to reply a comment on disabled event
        """
        self._test_for_disabled_event_and_permission_for_event_post(
            url_data={
                'path': comment_reply_url,
                'data': data_reply,
                'format': "json"
            },
            field='post'
        )

        """
        ------------------------------------------------------------------------
        trying to like a post on disabled event by event member
        result => must not be able to like a post on disabled event
        """
        self._test_for_disabled_event_and_permission_for_event_post(
            url_data={
                'path': post_like_url,
                'data': data_reply,
                'format': "json"
            },
            field='post'
        )

        ########################################################################
        #                           For Non Members                            #
        ########################################################################
        """
        ------------------------------------------------------------------------
        Test to add a post for an interactive event by member
        result => must be able to add post for event
        """
        self.client.login(email=self.users[3][0], password=self.users[3][1])
        event.enabled_event = True
        event.save()
        self._test_for_disabled_event_and_permission_for_event_post(
            url_data=dict(
                path=post_url, data=_data,
                content_type='application/x-www-form-urlencoded'
            ),
            field='post_type'
        )
        """
        ------------------------------------------------------------------------
        Test for like a post for an interactive event by member
        result => must be able to like a post for event
        """
        self._test_for_disabled_event_and_permission_for_event_post(
            url_data=dict(
                path=post_like_url,
                data=data_like,
                format='json'
            ),
            field='post'
        )

        """
        ------------------------------------------------------------------------
        Test for commenting a post for an interactive event by member
        result => must be able to add comment for a post in event
        """
        self._test_for_disabled_event_and_permission_for_event_post(
            url_data=dict(
                path=post_comment_url,
                data=data_cmt,
                format='json'
            ),
            field='post'
        )

        """
        ------------------------------------------------------------------------
        Test for replying a comment for a post for an interactive event by member
        result => must be able to reply comment for a post in event
        """
        self._test_for_disabled_event_and_permission_for_event_post(
            url_data=dict(
                path=comment_reply_url,
                data=data_reply,
                format='json'
            ),
            field='post'
        )

        """
        ------------------------------------------------------------------------
        Test for replying a comment for a post for an interactive event by member
        result => must be able to reply comment for a post in event
        """
        self._test_for_disabled_event_and_permission_for_event_post(
            url_data=dict(
                path=comment_like_url,
                data=data_like,
                format='json'
            ),
            field='post'
        )

    def _test_for_disabled_event_and_permission_for_event_post(self, field, url_data: dict):
        response = self.client.post(
            **url_data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(isinstance(response.data.get(field), list))
