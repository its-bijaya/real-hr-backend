from django.contrib.auth import get_user_model
from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.hris.api.v1.tests.factory import DutyStationFactory
from irhrs.common.models import DutyStation


USER = get_user_model()


class TestDutyStations(RHRSAPITestCase):
    users = [('hr@email.com', 'secret', 'Male')]
    organization_name = 'Google Inc.'

    def setUp(self):
        super().setUp()
        self.url = reverse('api_v1:commons:duty-station-list', kwargs={
        })
        self.duty_station_one = DutyStationFactory(
            name="Durgam One",
            amount=1000,
        )
        self.duty_station_two = DutyStationFactory(
            name="Not Durgam Two",
            amount=500,
        )
        self.client.force_login(self.created_users[0])

    def test_duty_station_list_works(self):
        res = self.client.get(
            self.url
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['results']), 2)

    def test_create_duty_station_works(self):
        payload = {
            "name": "Durgam",
            "description": "This is a durgam place.",
            "amount": 500,
        }
        res = self.client.post(
            self.url,
            data=payload,
            format='json'
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(
            DutyStation.objects.filter(
                name = payload["name"],
                description = payload["description"],
                amount = payload["amount"]
            ).exists()
        )

    def test_update_duty_station_works(self):
        self.update_url = reverse(
            'api_v1:commons:duty-station-detail', kwargs={
                'pk': self.duty_station_one.id
            })
        payload = {
            "name": "Not Durgam",
            "description": "This is a durgam place.",
            "amount": 500,
        }
        res = self.client.patch(
            self.update_url,
            data=payload,
            format='json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(
            DutyStation.objects.filter(
                name = payload["name"],
                description = payload["description"],
                amount = payload["amount"]
            ).exists()
        )

    def test_delete_duty_station_works(self):
        self.update_url = reverse(
            'api_v1:commons:duty-station-detail', kwargs={
                'pk': self.duty_station_one.id
            })
        res = self.client.delete(
            self.update_url,
            format='json'
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(DutyStation.objects.exclude(is_archived=True).count(),
                         1)

        res = self.client.get(
            self.url
        )
        self.assertEqual(len(res.json()['results']), 1)
