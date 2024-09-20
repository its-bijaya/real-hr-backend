import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.organization.models import MeetingRoom, OrganizationBranch, MeetingRoomStatus


class MeetingRoomTestCase(RHRSTestCaseWithExperience):
    users = [('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
             ('hello@hello.com', 'secretThing', 'Male', 'Clerk')]
    organization_name = "Google"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123

    def setUp(self):
        super().setUp()
        self.user = get_user_model()
        self.branch = OrganizationBranch.objects.create(
            organization=self.organization,
            branch_manager=None,
            name='Kathmandu',
            description='',
            contacts=json.dumps({
                'Mobile': '1234567890'
            }),
            email='',
            code='',
            mailing_address='',
        )
        self.organization_meeting_room_list_url = reverse(
            'api_v1:organization:meeting-room-list',
            kwargs={'organization_slug': self.organization.slug}
        )
        self.client.login(email=self.users[0][0], password=self.users[0][1])

    def test_adding_meeting_room_to_organization(self):
        meeting_room = self._create_organization_meeting_room()
        # adding meeting_room with same name

        _data = {
            "organization": self.organization,
            "branch": "Kathmandu",
            "name": "Sagamatha Hall",
            "location": "Sundhara",
            "floor": "2",
            "area": "454 sq. km",
            "capacity": 200,
            "description": ""
        }

        self.data = _data
        response = self.client.post(self.organization_meeting_room_list_url, data=_data)
        self.assertEqual(response.status_code, 400)
        self._update_organization_meeting_room(meeting_room)
        self._meeting_room_book(meeting_room)
        self._get_available_status()

    def _create_organization_meeting_room(self, data=None):
        if not data:
            data = {
                "organization": self.organization,
                "branch": self.branch.slug,
                "name": "Sagarmatha Hall",
                "location": "Sundhara",
                "floor": "2",
                "area": "454 sq. km",
                "capacity": 200,
                "description": ""
            }
            response = self.client.post(self.organization_meeting_room_list_url,
                                        data=data)
            self.assertEqual(response.status_code, 201)
            meeting_room = MeetingRoom.objects.get(
                id=response.data.get('id'))
            self.assertEqual(meeting_room.name, data.get('name'))
            self.assertEqual(meeting_room.location, data.get('location'))
            self.assertEqual(meeting_room.floor, data.get('floor'))
            self.assertEqual(meeting_room.area, data.get('area'))
            self.assertEqual(meeting_room.capacity, data.get('capacity'))

            return meeting_room

    def _update_organization_meeting_room(self, meeting_room):
        update_url = reverse(
            'api_v1:organization:meeting-room-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'slug': meeting_room.slug
            }
        )
        data = {
            'name': 'Sangrila Hall',
            'capacity': 400
        }
        response = self.client.patch(update_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], data.get('name'))
        self.assertEqual(response.data['capacity'], data.get('capacity'))

    def _meeting_room_book(self, meeting_room):
        time_now = timezone.now()
        booked_from = time_now + timedelta(days=10)
        booked_to = time_now + timedelta(days=11)
        data = {
            'meeting_room': meeting_room,
            'booked_from': booked_from,
            'booked_to': booked_to
        }
        available = MeetingRoomStatus(**data)
        available.save()
        available_test_url = reverse(
            'api_v1:organization:meeting-room-available-rooms',
            kwargs={
                'organization_slug': self.organization.slug,
            },
        )
        response = self.client.get(
            available_test_url,
            data={
                'start_at': booked_from,
                'end_at': booked_to
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['available'], False)
        response = self.client.get(
            available_test_url,
            data={
                'start_at': time_now,
                'end_at': time_now + timedelta(days=12)
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['available'], False)

    def _get_available_status(self):
        test_url = reverse(
            'api_v1:organization:meeting-room-available-rooms',
            kwargs={
                'organization_slug': self.organization.slug,
            }
        )
        test_url += '?start_at=2019-10-03&end_at=2019-10-19'
        response = self.client.get(
            test_url,
            data={
                'start_at': timezone.now() + timedelta(days=100),
                'end_at': timezone.now() + timedelta(days=110)
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['available'], True)
