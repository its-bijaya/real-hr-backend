import json
from datetime import timedelta
from random import randint
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.event.api.v1.tests.factory import MeetingFactory
from irhrs.event.api.v1.tests.setup import EventSetUp, MeetingSetup
from irhrs.event.constants import OUTSIDE, MEETING, MINUTER, TIME_KEEPER, MEMBER
from irhrs.event.models import Event, EventDetail


class TestMeeting(EventSetUp):
    event_detail_kwargs = {}

    def setUp(self):
        super().setUp()
        self._data = {
            'title': self.fake.text(max_nb_chars=100),
            'start_at': timezone.now() + timedelta(days=1),
            'end_at': timezone.now() + timedelta(days=2),
            'event_location': OUTSIDE,
            'description': self.fake.text(max_nb_chars=10),
            'location': self.fake.address(),
            'event_category': MEETING,
            'interactive_event': True
        }
        self.meeting = {
            "agenda": [self.fake.text(max_nb_chars=100) for _ in range(randint(1, 5))],
            "notification_time": [30, 40],
            "minuter": self.sys_users[0].id,
            "time_keeper": self.sys_users[1].id
        }

    @property
    def data(self):
        self._data.update({
            'eventdetail': json.dumps(self.meeting)
        })
        data = [(key, value) for key, value in self._data.items()] + self.members
        return data

    @property
    def event_detail_url(self):
        return reverse(
            viewname='api_v1:event:-detail', kwargs=self.event_detail_kwargs
        )

    def test_for_creating_meeting(self):
        """
        --------------------------------------------------------------------------------------------
        test for creating a meeting using api covering different scenario
        :return:
        """

        """
        --------------------------------------------------------------------------------------------
        creating meeting with proper dataset
        result => must create meeting with this data set
        """
        meeting = self._create_meeting()

        """
        --------------------------------------------------------------------------------------------
        creating meeting without time_keeper or minuter
        result => must create meeting for this scenario
        """
        self.meeting.update({
            'time_keeper': None,
            'minuter': None
        })
        _ = self._create_meeting()

        """
        --------------------------------------------------------------------------------------------
        creating meeting without any agenda
        result => must throw 400 error for this scenario
        """
        self.meeting.update({
            'agenda': []
        })
        _ = self._create_meeting()
        del self.meeting['agenda']
        _ = self._create_meeting()
        """
        --------------------------------------------------------------------------------------------
        creating meeting without any agenda
        result => must throw 400 error for this scenario
        """
        self.meeting.update({
            'notification_time': []
        })
        _ = self._create_meeting()

        """
        --------------------------------------------------------------------------------------------
        creating meeting with agenda more than 2000 chars
        result => must not create agenda
        """
        self.meeting.update({
            'agenda': [self.fake.text(max_nb_chars=5000)]
        })
        self._test_meeting_for_validation(field='agenda')

        """
        --------------------------------------------------------------------------------------------
        creating meeting with non member time_keeper or minuter
        result => must throw 400 error for this scenario
        """
        # for time_keeper
        self.meeting.update({
            'agenda': [],
            'time_keeper': self.sys_users[-1].id
        })
        self._test_meeting_for_validation(field='time_keeper')

        # for minuter
        self.meeting.update({
            'time_keeper': None,
            'minuter': self.sys_users[2].id
        })
        self._test_meeting_for_validation(field='minuter')

        """
        --------------------------------------------------------------------------------------------
        try to create meeting with out meeting detail
        result => must not create meeting
        """
        data = [
                   ('title', self.fake.text(max_nb_chars=100)),
                   ('start_at',
                    timezone.now() + timedelta(days=1)),
                   ('end_at',
                    timezone.now() + timedelta(days=2)),
                   ('event_location', OUTSIDE),
                   ('description', self.fake.text(max_nb_chars=10)),
                   ('location', self.fake.address()),
                   ('event_category', MEETING),
                   ('interactive_event', True)
               ] + self.members
        _data = urlencode(data)
        response = self.client.post(self.event_list_url, data=_data,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(isinstance(response.data.get('eventdetail'), list))

    def _create_meeting(self):
        response = self.client.post(
            path=self.event_list_url, data=urlencode(self.data),
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = Event.objects.get(id=response.data.get('id'))
        meeting = event.eventdetail
        return self._validate_create_and_update_meeting(meeting=meeting)

    def _test_meeting_for_validation(self, field=None, update=False):
        if not update:
            response = self.client.post(
                path=self.event_list_url, data=urlencode(self.data),
                content_type='application/x-www-form-urlencoded'
            )
        else:
            response = self.client.post(
                path=self.event_detail_url, data=urlencode(self.data),
                content_type='application/x-www-form-urlencoded'
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        if field:
            self.assertTrue(isinstance(response.data.get(field), list))

    def test_for_updating_event(self):
        self.meeting.update({
            "agenda": [self.fake.text(max_nb_chars=100) for _ in range(randint(1, 5))],
            "notification_time": [30, 40],
            "minuter": self.sys_users[0].id,
            "time_keeper": self.sys_users[1].id
        })
        meeting = self._create_meeting()
        self.event_detail_kwargs.update({'pk': meeting.event_id})
        self.meeting.update({
            'time_keeper': None,
            'minuter': None
        })
        _ = self._update_meeting()

        """
        --------------------------------------------------------------------------------------------
        created meeting without time keeper and minuter and updated later
        result => must update meeting with the position of members in attendance model
        """
        meeting = self._create_meeting()
        self.assertFalse(meeting.time_keeper)
        self.assertFalse(meeting.minuter)
        members = [member[1] for member in self.members]
        attendances = meeting.meeting_attendances.filter(
            member_id__in=members,
            position=MEMBER
        ).exists()
        self.assertTrue(attendances)
        self.meeting.update({
            "minuter": self.sys_users[0].id,
            "time_keeper": self.sys_users[1].id
        })
        self.event_detail_kwargs.update({'pk': meeting.event_id})
        updated_meeting = self._update_meeting()
        minuter = updated_meeting.meeting_attendances.filter(
            member_id=self.meeting.get('minuter')).first()
        time_keeper = updated_meeting.meeting_attendances.filter(
            member_id=self.meeting.get('time_keeper')).first()
        self.assertEqual(minuter.position, MINUTER)
        self.assertEqual(time_keeper.position, TIME_KEEPER)

    def _update_meeting(self):
        response = self.client.patch(
            path=self.event_detail_url, data=urlencode(self.data),
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        meeting = EventDetail.objects.filter(event_id=response.data.get('id')).first()
        return self._validate_create_and_update_meeting(meeting=meeting)

    def _validate_create_and_update_meeting(self, meeting):
        if meeting.meeting_agendas.exists():
            self.assertTrue(
                meeting.meeting_agendas.filter(
                    title__in=self.meeting.get('agenda'),
                    discussion__isnull=True,
                    decision__isnull=True,
                    discussed=False
                ).exists()
            )

        if meeting.notifications.exists():
            self.assertTrue(
                meeting.notifications.filter(
                    time__in=self.meeting.get('notification_time'),
                    notified=False
                ).exists
            )

        event_members = list(meeting.event.event_members.all().values_list('user_id', flat=True))
        event_members.append(meeting.created_by.id)
        self.assertTrue(meeting.meeting_attendances.filter(member_id__in=event_members).exists())

        self.assertEqual(
            meeting.time_keeper.user_id if meeting.time_keeper else None,
            self.meeting.get('time_keeper')
        )
        self.assertEqual(
            meeting.minuter.user_id if meeting.minuter else None,
            self.meeting.get('minuter')
        )
        return meeting

    def test_delete_meeting(self):
        _ = [MeetingFactory() for _ in range(0, 5)]
        self.meeting.update({
            "agenda": [self.fake.text(max_nb_chars=100) for _ in range(randint(1, 6))],
            "notification_time": [30, 40, 10],
            "minuter": self.sys_users[0].id,
            "time_keeper": self.sys_users[1].id
        })
        meeting = self._create_meeting()
        self.assertTrue(meeting.meeting_agendas.exists())
        self.assertTrue(meeting.notifications.exists())
        self.event_detail_kwargs.update({'pk': meeting.event_id})
        response = self.client.delete(self.event_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(meeting.meeting_agendas.exists())
        self.assertFalse(meeting.meeting_attendances.exists())

    def test_meeting_agenda_crud(self):
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1]
        )
        self.members.append(('members', self.user.objects.get(email=self.users[3][0]).id))
        self.meeting.update({
            "minuter": self.sys_users[0].id,
            "time_keeper": self.sys_users[1].id
        })
        meeting = self._create_meeting()

        """
        --------------------------------------------------------------------------------------------
        test for creating meeting agenda and updating it by event minuter and meeting organizer
        result => must be able to update meeting agenda and must be able to add discussion and
        decision for meeting
        """
        # by minuter
        self.client.login(
            email=self.users[1][0],
            password=self.users[1][1]
        )
        agenda = meeting.meeting_agendas.first()
        self._test_agenda_update_for_meeting(agenda=agenda, meeting=meeting)

        # by meeting organizer
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1]
        )
        agenda = meeting.meeting_agendas.last()
        self._test_agenda_update_for_meeting(agenda=agenda, meeting=meeting)

        """
        --------------------------------------------------------------------------------------------
        test for creating meeting agenda and updating it by member and time keeper
        result => must not be able to update meeting agenda
        """
        # by time_keeper
        self.client.login(
            email=self.users[2][0],
            password=self.users[2][1]
        )
        agenda = meeting.meeting_agendas.first()
        self.agenda_detail_url = reverse(
            'api_v1:event:meeting-agenda-detail',
            kwargs={'pk': agenda.id, 'event_id': meeting.event_id}
        )
        data = {
            'title': self.fake.text(max_nb_chars=100),
            'discussion': self.fake.text(max_nb_chars=20000),
            'decision': self.fake.text(max_nb_chars=20000),
            'discussed': True
        }
        response = self.client.patch(self.agenda_detail_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get('detail').code, 'permission_denied')

        # by member
        self.client.login(
            email=self.users[3][0],
            password=self.users[3][1]
        )
        agenda = meeting.meeting_agendas.last()
        self.agenda_detail_url = reverse(
            'api_v1:event:meeting-agenda-detail',
            kwargs={'pk': agenda.id, 'event_id': meeting.event_id}
        )
        data = {
            'title': self.fake.text(max_nb_chars=100),
            'discussion': self.fake.text(max_nb_chars=20000),
            'decision': self.fake.text(max_nb_chars=20000),
            'discussed': True
        }
        response = self.client.patch(self.agenda_detail_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get('detail').code, 'permission_denied')

    def _test_agenda_update_for_meeting(self, agenda, meeting):
        self.agenda_detail_url = reverse(
            'api_v1:event:meeting-agenda-detail',
            kwargs={'pk': agenda.id, 'event_id': meeting.event_id}
        )
        data = {
            'title': self.fake.text(max_nb_chars=100),
            'discussion': self.fake.text(max_nb_chars=20000),
            'decision': self.fake.text(max_nb_chars=20000),
            'discussed': True
        }
        response = self.client.patch(self.agenda_detail_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('discussion'), data.get('discussion'))
        self.assertEqual(response.data.get('decision'), data.get('decision'))
        self.assertEqual(response.data.get('discussed'), data.get('discussed'))

        updated_agenda = meeting.meeting_agendas.get(id=agenda.id)
        self.assertEqual(updated_agenda.discussion, data.get('discussion'))
        self.assertEqual(updated_agenda.decision, data.get('decision'))
        self.assertEqual(updated_agenda.discussed, data.get('discussed'))


class TestMeetingAcknowledge(MeetingSetup):
    """
    this test is used to cover test case scenario while acknowledging meeting before it has been
    prepared
    """

    @property
    def meeting_acknowledge_url(self):
        return reverse(
            'api_v1:event:-meeting-acknowledge',
            kwargs={
                'pk': self.meeting.event_id
            }
        )

    def test_meeting_acknowledge(self):
        """
        :return:
        """
        """
        try to acknowledge meeting before it has been prepared
        """
        response = self.client.post(
            self.meeting_acknowledge_url,
            data={}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get('detail'), 'Meeting has not been prepared yet.')

        """
        try to acknowledge meeting after it has been prepared by user who are associated
        with meeting
        """
        self.meeting.prepared = True
        self.meeting.save()
        for user in self.SYS_USERS[0:6]:
            self.client.force_login(user=user)
            response = self.client.post(
                self.meeting_acknowledge_url,
                data={}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        meeting_members = list(
            self.meeting.meeting_attendances.all().order_by(
                'member_id'
            ).values_list('member_id', flat=True)
        )
        acknowledge_member = list(
            self.meeting.acknowledge_records.all().order_by(
                'member_id'
            ).values_list('member_id', flat=True)
        )
        self.assertListEqual(meeting_members, acknowledge_member)

        """
        try to acknowledge meeting after it has been prepared by user who are not associated
        with meeting
        """
        for user in self.SYS_USERS[6:-1]:
            self.client.force_login(user=user)
            response = self.client.post(
                self.meeting_acknowledge_url,
                data={}
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
