import datetime

from django.contrib.auth import get_user_model
from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.common.api.tests.factory import DutyStationFactory
from irhrs.common.models import DutyStation
from irhrs.hris.models import DutyStationAssignment
from irhrs.hris.api.v1.tests.factory import DutyStationAssignmentFactory
from irhrs.organization.models import Organization
from irhrs.users.models import User

USER = get_user_model()


class TestDutyStationAssignment(RHRSAPITestCase):
    users = [('hr@email.com', 'secret', 'Male'),
             ('test@example.com', 'supersecret', 'Male'),
             ('userboy@example.com', 'supersecret', 'Male'),
             ]
    organization_name = 'Google Inc.'

    def setUp(self):
        super().setUp()
        self.url = reverse('api_v1:hris:assign-duty-station-list',
                           kwargs={
                               'organization_slug': self.organization.slug,
                           }
                           )
        self.duty_station_one = DutyStationFactory(
            name="Durgam",
            amount=1000,
        )
        self.duty_station_two = DutyStationFactory(
            name="Not Durgam",
            amount=500,
        )
        self.client.force_login(self.created_users[0])

    def create_duty_station_assignments(self):
        self.duty_station_assignment_one = DutyStationAssignmentFactory(
            user=self.created_users[0],
            organization = self.organization,
        )
        self.duty_station_assignment_two = DutyStationAssignmentFactory(
            user=self.created_users[1],
            organization = self.organization,
        )

    def test_duty_station_assignment_list_works(self):
        self.create_duty_station_assignments()
        res = self.client.get(
            self.url
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['results']), 2)

    def test_current_duty_station_assignment_list_works(self):
        self.create_duty_station_assignments()
        self.current_duty_stations = reverse(
            'api_v1:hris:currently-assigned-duty-stations-list',
            kwargs={
                'organization_slug': self.organization.slug,
            })
        res = self.client.get(
            self.current_duty_stations
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['results']), 2)

    def test_current_duty_station_assignment_with_multiple_assignments(self):
        self.create_duty_station_assignments()
        five_days_ago = datetime.date.today() - datetime.timedelta(days=5)
        two_days_ago = datetime.date.today() - datetime.timedelta(days=2)
        currently_assigned_duty_station = DutyStationAssignmentFactory(
            user = self.created_users[0],
            duty_station = self.duty_station_one,
            from_date = five_days_ago,
            to_date = two_days_ago
        )
        self.current_duty_stations = reverse(
            'api_v1:hris:currently-assigned-duty-stations-list',
            kwargs={
                'organization_slug': self.organization.slug,
            })
        res = self.client.get(
            self.current_duty_stations
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['results']), 2)

    def test_create_duty_station_assignment_works(self):
        payload = {
            "user": self.created_users[0].id,
            "from_date": '2020-01-23',
            "to_date": '2021-01-23',
            "duty_station": self.duty_station_one.id
        }
        res = self.client.post(
            self.url,
            data=payload,
            format='json'
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(
            DutyStationAssignment.objects.filter(
                duty_station__id = payload["duty_station"],
                user__id = payload["user"],
                from_date = payload["from_date"],
                to_date = payload["to_date"]
            ).exists()
        )

    def test_update_duty_station_assignment_works(self):
        self.duty_station_assignment_one = DutyStationAssignmentFactory(
            user=self.created_users[0],
            organization = self.organization,
        )
        self.update_url = reverse(
            'api_v1:hris:assign-duty-station-detail', kwargs={
                'pk': self.duty_station_assignment_one.id,
                'organization_slug': self.organization.slug
            })
        payload = {
            "user": self.created_users[0].id,
            "from_date": '2020-02-2',
            "to_date": '2021-01-21',
            "duty_station": self.duty_station_two.id
        }
        res = self.client.put(
            self.update_url,
            data=payload,
            format='json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['to_date'], '2021-01-21')


    def test_delete_duty_station_works(self):
        self.create_duty_station_assignments()
        self.update_url = reverse(
            'api_v1:hris:assign-duty-station-detail', kwargs={
                'pk': self.duty_station_assignment_one.id,
                'organization_slug': self.organization.slug
            })
        res = self.client.delete(
            self.update_url,
            format='json'
        )
        self.assertEqual(res.status_code, 204)
        res = self.client.get(
            self.url
        )
        self.assertEqual(len(res.json()['results']), 1)


    def test_duty_station_list_filter_by_user(self):
        self.create_duty_station_assignments()
        self.url = self.url + \
            f'?user={self.created_users[0].id}'
        res = self.client.get(
            self.url
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['count'], 1)

    def test_assigned_duty_station_cannot_be_deleted(self):
        self.duty_station_assignment_one = DutyStationAssignmentFactory(
            user=self.created_users[0],
            organization = self.organization,
        )
        self.delete_url = reverse(
            'api_v1:commons:duty-station-detail', kwargs={
                'pk': self.duty_station_assignment_one.duty_station.id
            })
        res = self.client.delete(
            self.delete_url,
            format='json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json()['error'],
            f'This duty station cannot be deleted '
            f'because some users are currently assigned to it.'
        )

    def test_updating_duty_station_does_not_throw_assignment_already_exists_error(self):
        self.assignment = DutyStationAssignmentFactory(
            user = self.created_users[0],
            organization = self.organization,
            from_date = '2020-01-01',
            to_date = '2020-01-20'
        )
        self.update_url = reverse(
            'api_v1:hris:assign-duty-station-detail', kwargs={
                'pk': self.assignment.id,
                'organization_slug': self.organization.slug
            })
        payload = {
            "user": self.created_users[0].id,
            "from_date": '2020-01-05',
            "to_date": '2020-01-08',
            "duty_station": self.duty_station_two.id
        }
        res = self.client.put(
            self.update_url,
            data=payload,
            format='json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['from_date'], '2020-01-05')
        self.assertEqual(res.json()['to_date'], '2020-01-08')


    def test_updating_duty_station_with_None_to_date_does_not_throw_error(self):
        self.assignment = DutyStationAssignmentFactory(
            user = self.created_users[0],
            organization = self.organization,
            from_date = '2020-01-01',
            to_date = '2020-01-20'
        )
        self.update_url = reverse(
            'api_v1:hris:assign-duty-station-detail', kwargs={
                'pk': self.assignment.id,
                'organization_slug': self.organization.slug
            })
        payload = {
            "user": self.created_users[0].id,
            "from_date": '2020-01-25',
            "to_date": None,
            "duty_station": self.duty_station_two.id
        }
        res = self.client.put(
            self.update_url,
            data=payload,
            format='json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['from_date'], '2020-01-25')
        self.assertEqual(res.json()['to_date'], None)

    def test_assigned_duty_station_cannot_be_edited(self):
        self.duty_station_assignment_one = DutyStationAssignmentFactory(
            user=self.created_users[0],
            organization = self.organization,
        )
        self.edit_url = reverse(
            'api_v1:commons:duty-station-detail', kwargs={
                'pk': self.duty_station_assignment_one.duty_station.id
            })
        payload = {
            "name": "Very Durgam",
            "description": "This is a very durgam place.",
            "amount": 500,
        }
        res = self.client.put(
            self.edit_url,
            data = payload,
            format='json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['error'],
                         [f'This duty station cannot be updated '
                          f'because some users are currently '
                          f'assigned to it.'])
