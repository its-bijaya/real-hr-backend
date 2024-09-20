import json
from datetime import timedelta
from random import randint
from urllib.parse import urlencode

from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.event.api.v1.tests.factory import EventFactory
from irhrs.event.api.v1.tests.setup import EventSetUp
from irhrs.event.constants import OUTSIDE, SEMINAR, INSIDE, PRIVATE, PUBLIC
from irhrs.event.models import Event
from irhrs.event.utils.recurring import create_recurring_events
from irhrs.organization.api.v1.tests.factory import MeetingRoomFactory
from irhrs.organization.models import MeetingRoomStatus


class TestEvents(EventSetUp):
    def test_create_event(self):
        """
        ------------------------------------------------------------------------
        test for creating normal event
        result => must create an event for given set of data
        """

        _ = self._create_event_for_test()

        """
        ------------------------------------------------------------------------
        test for creating event with event location being inside and with
        meeting room
        result => must not create any event for this particular situation
        """
        meeting_room = MeetingRoomFactory(
            organization=self.organization,
            branch=self.branch
        )
        member_id = self.members[0][1]
        data = {
            'title': self.fake.text(max_nb_chars=100),
            'start_at': timezone.now() + timedelta(days=1),
            'end_at': timezone.now() + timedelta(days=2),
            'event_location': INSIDE,
            'description': self.fake.text(max_nb_chars=10),
            'meeting_room': meeting_room.id
        }
        eventdetail = {
            "minuter": member_id,
            "time_keeper": member_id
        }

        data.update({
            "eventdetail": json.dumps(eventdetail)
        })
        data = [(key, value) for key, value in data.items()] + self.members

        self._create_event_for_test(data=data)

        """"
        ------------------------------------------------------------------------
        test for creating event in past date
        result => must not create event for past date
        """

        data = [
            ('title', self.fake.text(max_nb_chars=100)),
            ('start_at', timezone.now() - timedelta(minutes=1)),
            ('end_at', timezone.now() + timedelta(days=2)),
            ('event_category', SEMINAR)
        ]
        self._test_for_error_while_creating_and_updating_event(data, 'start_at')

        """
        ------------------------------------------------------------------------
        test for creating event with event location being inside but without
        any meeting room
        result => must not create any event for this particular situation
        """
        data = [
            ('title', self.fake.text(max_nb_chars=100)),
            ('start_at', timezone.now() + timedelta(days=1)),
            ('end_at', timezone.now() + timedelta(days=2)),
            ('event_location', INSIDE),
            ('description', self.fake.text(max_nb_chars=10)),
        ]
        self._test_for_error_while_creating_and_updating_event(data,
                                                               'meeting_room')

        """
        ------------------------------------------------------------------------
        test for length of title more than 200 while creating event
        input => title for event more than 200 chars
        result => should not create event
        """
        data = [
            ('title', self.fake.text(max_nb_chars=400)),
            ('start_at', timezone.now() + timedelta(days=1)),
            ('end_at', timezone.now() + timedelta(days=2)),
            ('event_location', OUTSIDE),
            ('description', self.fake.text(max_nb_chars=10)),
            ('location', self.fake.address())
        ]
        self._test_for_error_while_creating_and_updating_event(data, 'title')

        """
        ------------------------------------------------------------------------
        test for event location being outside without any location detail
        result => must not create event for this scenario
        """
        data = [
            ('title', self.fake.text(max_nb_chars=200)),
            ('start_at', timezone.now() + timedelta(days=1)),
            ('end_at', timezone.now() + timedelta(days=2)),
            ('event_location', OUTSIDE),
            ('description', self.fake.text(max_nb_chars=10)),
        ]
        self._test_for_error_while_creating_and_updating_event(data, 'location')

        """
        test for end date less then start date
        result =>must not create event for this scenario
        """
        data = [
            ('title', self.fake.text(max_nb_chars=200)),
            ('start_at', timezone.now() + timedelta(days=2)),
            ('end_at', timezone.now() + timedelta(days=1)),
            ('event_location', OUTSIDE),
            ('description', self.fake.text(max_nb_chars=10)),
            ('location', self.fake.address())
        ]
        self._test_for_error_while_creating_and_updating_event(data, 'end_at')

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

    def _create_event_for_test(self, data=None):
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

    def _test_for_error_while_creating_and_updating_event(self, data,
                                                          field=None,
                                                          update=False):
        _data = urlencode(data)
        if not update:
            response = self.client.post(
                self.event_list_url, data=_data,
                content_type='application/x-www-form-urlencoded'
            )
        else:
            response = self.client.patch(
                self.event_detail_url, data=_data,
                content_type='application/x-www-form-urlencoded'
            )
        self.assertEqual(response.status_code, 400)
        if field:
            self.assertTrue(isinstance(response.data[field], list))

    def test_updating_event(self):
        event = self._create_event_for_test()
        self.event_detail_url = reverse('api_v1:event:-detail',
                                        kwargs={'pk': event.id})
        data = self.payload()
        data.update({
            'title': self.fake.text(max_nb_chars=100)
        })
        data = [(key, value) for key, value in data.items()] + self.members
        _updated_event = self._update_event_for_test(data=data)
        self.assertNotEqual(event.title, _updated_event.title)

        """
        ------------------------------------------------------------------------
        test for event title more than 200 chars while update
        result => must not update data
        """
        data = [
            ('title', self.fake.text(max_nb_chars=400))
        ]
        self._test_for_error_while_creating_and_updating_event(data=data,
                                                               field='title',
                                                               update=True)

        """
        ------------------------------------------------------------------------
        test for past start date
        result => must not update data
        """
        data = [
            ('start_at', timezone.now() - timedelta(days=1))
        ]
        self._test_for_error_while_creating_and_updating_event(
            data=data,
            field='start_at',
            update=True
        )

        """
        ------------------------------------------------------------------------
        test for end date smaller than start date
        result => must not update data
        """
        data = [
            ('start_at', timezone.now() + timedelta(days=2)),
            ('end_at', timezone.now() + timedelta(days=1))
        ]
        self._test_for_error_while_creating_and_updating_event(
            data=data,
            field='end_at',
            update=True
        )

        """
        ------------------------------------------------------------------------
        test for event_location being inside without any room
        result => must not update data
        """
        data = [
            ('event_location', INSIDE),
        ]
        self._test_for_error_while_creating_and_updating_event(data=data,
                                                               field='meeting_room',
                                                               update=True)

        """
        ------------------------------------------------------------------------
        test for updating event with previous event_location outside to inside
        with meeting room
        result => must update event
        """
        meeting_room = MeetingRoomFactory(
            organization=self.organization,
            branch=self.branch
        )
        data = self.payload()
        data.update({
            'event_location': INSIDE,
            'meeting_room': meeting_room.id
        })
        data = [(key, value) for key, value in data.items()] + self.members
        _ = self._update_event_for_test(data=data)
        _updated_event = Event.objects.get(id=event.id)
        self.assertEqual(_updated_event.event_location, INSIDE)
        self.assertEqual(_updated_event.room.meeting_room.id, meeting_room.id)
        room = _updated_event.room

        """
        ------------------------------------------------------------------------
        test whether meeting room changes and gets delete or not when meeting
        room is changed
        result => must update and change meeting room also delete meeting room
        status for that meeting room
        """
        data = self.payload()
        data.update({
            'event_location': INSIDE,
            'meeting_room': meeting_room.id,
            'start_at': timezone.now() + timedelta(days=5),
            'end_at': timezone.now() + timedelta(days=6)
        })
        data = [(key, value) for key, value in data.items()] + self.members
        _ = self._update_event_for_test(data=data)
        _updated_event = Event.objects.get(id=event.id)
        self.assertEqual(_updated_event.event_location, INSIDE)
        self.assertEqual(_updated_event.room.meeting_room.id, meeting_room.id)
        new_room = _updated_event.room
        self.assertNotEqual(room.id, new_room.id)
        self.assertFalse(MeetingRoomStatus.objects.filter(id=room.id).exists())
        self.assertTrue(
            MeetingRoomStatus.objects.filter(id=new_room.id).exists())

        """
        ------------------------------------------------------------------------
        test for changing event location form Inside to Outside
        result => must remove room associated to event
        """
        data = self.payload()
        data.update({
            'event_location': OUTSIDE,
            'location': self.fake.address(),
        })
        data = [(key, value) for key, value in data.items()] + self.members
        self.event_detail_url = reverse(
            'api_v1:event:-detail', kwargs={'pk': event.id}
        )
        _ = self._update_event_for_test(data=data)
        _updated_event = Event.objects.get(id=event.id)
        self.assertEqual(_updated_event.event_location, OUTSIDE)
        self.assertEqual(_updated_event.location, data[5][1])
        self.assertEqual(_updated_event.room, None)

    def _update_event_for_test(self, data):
        _data = urlencode(data)
        response = self.client.patch(
            self.event_detail_url, data=_data,
            content_type='application/x-www-form-urlencoded'
        )
        _updated_event = Event.objects.get(id=response.data.get('id'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], _updated_event.title)
        return _updated_event

    def test_for_event_list(self):
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        response = self.client.get(self.event_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        events = Event.objects.filter(Q(created_by__email=self.users[0][0]) |
                                      Q(members__email__in=[self.users[0][0]]) |
                                      Q(event_type=PUBLIC)).distinct()
        self.assertEqual(events.count(), response.data.get('count'))
        results = response.json().get('results')
        for i, event in enumerate(events):
            self.assertEqual(event.id, results[i].get('id'))
            self.assertEqual(event.title, results[i].get('title'))
            self.assertEqual(event.event_category, results[i].get('event_category'))
            self.assertEqual(event.event_location, results[i].get('event_location'))
            self.assertEqual(event.location, results[i].get('location'))

    def test_for_event_detail(self):
        _ = [EventFactory(location=self.fake.address(), event_location=OUTSIDE)
             for _ in range(5)]
        event = Event.objects.first()
        self.event_detail_url = reverse(
            'api_v1:event:-detail',
            kwargs={'pk': event.id}
        )
        response = self.client.get(self.event_detail_url)
        self.assertEqual(response.data.get('id'), event.id)
        self.assertEqual(response.data.get('event_location'),
                         event.event_location)
        self.assertEqual(response.data.get('location'), event.location)

    def test_for_deleting_event(self):
        _ = [EventFactory(location=self.fake.address(), event_location=OUTSIDE)
             for _ in range(5)]
        event = self._create_event_for_test()
        self.assertTrue(Event.objects.filter(id=event.id).exists())
        self.event_detail_url = reverse(
            'api_v1:event:-detail',
            kwargs={'pk': event.id}
        )
        response = self.client.delete(self.event_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(id=event.id).exists())

    def test_for_accepting_event(self):
        emails = [email[0] for email in self.users if
                  not email[0] == self.users[0][0]]
        users = self.user.objects.filter(email__in=emails)
        members = [('members', user.id) for user in users if
                   not user.email == self.users[3][0]]
        data = self.payload()
        data.update({
            'event_type': PRIVATE
        })
        data = [(key, value) for key, value in data.items()] + members
        event = self._create_event_for_test(data=data)
        self.assertEqual(event.event_members.count(), len(members))
        accept_url = reverse("api_v1:event:-accept", kwargs={'pk': event.id})

        """
        ------------------------------------------------------------------------
        event creator tries to accept event
        result => raise error
        """
        response = self.client.post(
            accept_url,
            data=json.dumps(
                {
                    "invitation_status": "Accepted"
                }
            ),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get('detail'),
                         'Cannot join Events created by self')

        """
        ------------------------------------------------------------------------
        try to accept event by event member
        result => should be able to accept event
        """
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        response = self.client.post(
            accept_url,
            data=json.dumps(
                {
                    "invitation_status": "Accepted"
                }
            ),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('invitation_status'), 'Accepted')

        """
        ------------------------------------------------------------------------
        non member user of event trying to accept event
        result => not able to accept this event, must raise 404 from get_object
        method
        """
        self.client.login(email=self.users[3][0], password=self.users[3][1])
        response = self.client.post(
            accept_url,
            data=json.dumps(
                {
                    "invitation_status": "Accepted"
                }
            ),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data.get('detail'), 'Not found.')

        """
        ------------------------------------------------------------------------
        test for accepting past event
        result => not able to accept those events
        """
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        event.start_at = timezone.now() - timedelta(days=2)
        event.end_at = timezone.now() - timedelta(days=1)
        event.save()

        response = self.client.post(
            accept_url,
            data=json.dumps(
                {
                    "invitation_status": "Accepted"
                }
            ),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data.get('detail'),
            'Cannot Join expired events'
        )

    def test_for_removing_member_from_event(self):
        emails = [email[0] for email in self.users if
                  not email[0] == self.users[0][0]]
        users = self.user.objects.filter(email__in=emails)
        members = [('members', user.id) for user in users if
                   not user.email == self.users[3][0]]
        data = self.payload()
        data.update({
            'event_type': PRIVATE
        })
        data = [(key, value) for key, value in data.items()] + members
        event = self._create_event_for_test(data=data)
        self.assertEqual(event.event_members.count(), len(members))
        member_remove_url = reverse(
            "api_v1:event:-remove-member",
            kwargs={
                'pk': event.id,
                'member_id': members[0][1]
            }
        )

        """
        ------------------------------------------------------------------------
        Non member user for event tries to remove event member
        result => data not found error
        """
        self.client.login(email=self.users[3][0], password=self.users[3][1])
        response = self.client.delete(member_remove_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get('detail'), 'Not found.')

        """
        ------------------------------------------------------------------------
        event member tries to remove event member
        result => must not be able to remove member from event
        """
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        response = self.client.delete(member_remove_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get('detail'), 'Event doesn\'t exist.')

        """
        ------------------------------------------------------------------------
        event creator tries to remove event member
        result => must be able to remove member from event
        """
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        # attendees should be present before delete
        self.assertTrue(event.eventdetail.meeting_attendances.filter(member=members[0][1]).exists())
        response = self.client.delete(member_remove_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(event.event_members.filter(id=members[0][1]).exists())
        # attendees should be deleted after removing member
        self.assertFalse(event.eventdetail.meeting_attendances.filter(member=members[0][1]).exists())
        """
        ------------------------------------------------------------------------
        try to remove nom member form event
        result => raise validation error
        """
        member = users.get(email=self.users[3][0])
        member_remove_url = reverse(
            "api_v1:event:-remove-member",
            kwargs={
                'pk': event.id,
                'member_id': member.id
            }
        )
        response = self.client.delete(member_remove_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data.get('detail'),
            'User is not the member of this event.'
        )

    def test_for_repeat_rule_using_api(self):
        """
        ------------------------------------------------------------------------
        test for repeat rule using api
        """
        count = randint(2, 9)
        month = randint(1, 12)
        day = randint(1, 28)
        data = self.payload()
        data.update({
            'repeat_rule': f'FREQ=YEARLY;COUNT={count};BYMONTH={month};BYMONTHDAY={day}'
        })
        data = [(key, value) for key, value in data.items()] + self.members
        event = self._create_event_for_test(data=data)
        self._test_for_child_event_validation(event=event, count=count, month=month, day=day)

        """
        --------------------------------------------------------------------------------------------
        test for repeat rule before start date of event
        return => must not create event
        """
        data[-1] = ('repeat_rule', f'FREQ=DAILY;INTERVAL=1;'
                                   f'UNTIL={timezone.now().date() - timedelta(1)}')
        _data = urlencode(data)
        response = self.client.post(
            self.event_list_url, data=_data,
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(isinstance(response.data.get('repeat_rule'), list))

        """
        --------------------------------------------------------------------------------------------
        test for repeat rule for daily
        return => must create and repeat event
        """
        interval = randint(1, 3)
        data[-1] = ('repeat_rule',
                    f'FREQ=DAILY;INTERVAL={interval};UNTIL={timezone.now().date() + timedelta(10)}')
        _data = urlencode(data)
        response = self.client.post(
            self.event_list_url, data=_data,
            content_type='application/x-www-form-urlencoded'
        )
        event = Event.objects.get(id=response.data.get('id'))
        child_events = Event.objects.filter(generated_from=event).order_by('start_at')
        date = None
        for child in child_events:
            date = (date if date else timezone.now().date() + timedelta(
                days=1)) + timedelta(days=interval)
            self.assertEqual(child.start_at.month, date.month)
            self.assertEqual(child.start_at.day, date.day)
            self.assertNotEqual(child.id, event.id)
            self.assertEqual(child.title, event.title)
            self.assertEqual(child.event_members.count(), event.event_members.count())
            self.assertEqual(child.repeat_rule, None, 'Child event must not have repeat rule')

    def test_member_update_updates_attendees(self):
        members_copy = [('members', user.id) for user in self.sys_users]
        self.members = [members_copy[0], members_copy[1]]
        event = self._create_event_for_test()

        self.assertTrue(
            event.eventdetail.meeting_attendances.filter(member=members_copy[0][1]).exists()
        )
        self.assertTrue(
            event.eventdetail.meeting_attendances.filter(member=members_copy[1][1]).exists()
        )
        self.assertFalse(
            event.eventdetail.meeting_attendances.filter(member=members_copy[2][1]).exists()
        )

        data = {
            'members': [members_copy[0][1], members_copy[1][1], members_copy[2][1]]
        }
        event_detail_url = reverse('api_v1:event:-detail', kwargs={'pk': event.id})
        response = self.client.patch(event_detail_url, data=data)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            event.eventdetail.meeting_attendances.filter(member=members_copy[0][1]).exists()
        )
        self.assertTrue(
            event.eventdetail.meeting_attendances.filter(member=members_copy[1][1]).exists()
        )
        self.assertTrue(
            event.eventdetail.meeting_attendances.filter(member=members_copy[2][1]).exists()
        )

        data = {
            'members': [members_copy[0][1]]
        }

        response = self.client.patch(event_detail_url, data=data)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            event.eventdetail.meeting_attendances.filter(member=members_copy[0][1]).exists()
        )
        self.assertFalse(
            event.eventdetail.meeting_attendances.filter(member=members_copy[1][1]).exists()
        )
        self.assertFalse(
            event.eventdetail.meeting_attendances.filter(member=members_copy[2][1]).exists()
        )

    def test_for_recurring_function_used_to_repeat_event(self):
        count = randint(2, 9)
        month = randint(1, 12)
        day = randint(1, 28)
        event = self._create_event_for_test()
        event.repeat_rule = f'FREQ=YEARLY;COUNT={count};BYMONTH={month};BYMONTHDAY={day}'
        self.assertEqual(event.event_set.count(), 0)

        create_recurring_events(event)
        self._test_for_child_event_validation(event=event, count=count, month=month, day=day)

    def _test_for_child_event_validation(self, event, count, month, day):
        child_events = Event.objects.filter(generated_from=event)
        self.assertEqual(count, child_events.count())
        for child in child_events:
            self.assertEqual(child.start_at.month, month)
            self.assertNotEqual(child.id, event.id)
            self.assertEqual(child.title, event.title)
            self.assertEqual(child.event_members.count(), event.event_members.count())
            self.assertEqual(child.repeat_rule, None, 'Child event must not have repeat rule')
