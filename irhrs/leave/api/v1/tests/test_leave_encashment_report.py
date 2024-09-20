from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.leave.api.v1.tests.factory import LeaveEncashmentFactory


class LeaveEncashmentReportTestCase(RHRSAPITestCase):

    users = [
        ('admin@email.com', 'password', 'Female'),
        ('normal@email.com', 'password', 'Male')
    ]
    organization_name = 'Google'

    def test_list(self):
        record_1 = LeaveEncashmentFactory(user=self.admin, status="Generated")
        record_2 = LeaveEncashmentFactory(user=self.created_users[1], status="Encashed")

        url = reverse('api_v1:leave:encashments-list',
                      kwargs={'organization_slug': self.organization.slug})

        # hr viewing as normal
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response_ids = [entry["id"] for entry in response.data.get('results')]
        self.assertEqual(len(response_ids), 1)
        self.assertIn(record_1.id, response_ids)
        self.assertEqual(response.data.get('stats'), {
            "All": 1,
            "Generated": 1,
            "Approved": 0,
            "Denied": 0,
            "Encashed": 0,
        })

        # hr viewing as hr
        response = self.client.get(url+"?as=hr")
        self.assertEqual(response.status_code, 200)
        response_ids = [entry["id"] for entry in response.data.get('results')]
        self.assertEqual(len(response_ids), 2)
        self.assertIn(record_1.id, response_ids)
        self.assertIn(record_2.id, response_ids)
        self.assertEqual(response.data.get('stats'), {
            "All": 2,
            "Generated": 1,
            "Approved": 0,
            "Denied": 0,
            "Encashed": 1,
        })

        # normal user viewing
        self.client.force_login(self.created_users[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response_ids = [entry["id"] for entry in response.data.get('results')]
        self.assertEqual(len(response_ids), 1)
        self.assertIn(record_2.id, response_ids)
        self.assertEqual(response.data.get('stats'), {
            "All": 1,
            "Generated": 0,
            "Approved": 0,
            "Denied": 0,
            "Encashed": 1,
        })

    def test_update(self):
        instance = LeaveEncashmentFactory(user=self.created_users[1], balance=20,
                                          status="Generated")

        url = reverse('api_v1:leave:encashments-detail',
                      kwargs={'organization_slug': self.organization.slug, 'pk': instance.id})

        self.client.force_login(self.admin)

        payload = {
            "balance": 10,
            "remarks": "Updated"
        }

        response = self.client.put(url+"?as=hr", data=payload)
        self.assertEqual(response.status_code, 200, response.data)
        instance.refresh_from_db()
        self.assertEqual(instance.balance, 10)
        self.assertTrue(
            instance.history.filter(
                actor=self.admin,
                action="Updated",
                previous_balance=20,
                new_balance=10
            ).exists()
        )

    def test_update_with_status_other_than_generated(self):
        self.client.force_login(self.admin)
        payload = {
            "balance": 10,
            "remarks": "Updated"
        }

        for status in ["Approved", "Denied", "Encashed"]:
            instance = LeaveEncashmentFactory(
                user=self.created_users[1], balance=20, status=status
            )
            url = reverse('api_v1:leave:encashments-detail',
                          kwargs={'organization_slug': self.organization.slug, 'pk': instance.id})

            response = self.client.put(url + "?as=hr", data=payload)
            self.assertEqual(response.status_code, 400, response.data)
            self.assertEqual(response.data["non_field_errors"],
                             ["Can only update balance of encashment with `Generated` status"],
                             status)

    def test_bulk_action(self):
        record_1 = LeaveEncashmentFactory(user=self.admin)
        record_2 = LeaveEncashmentFactory(user=self.created_users[1])

        url = reverse('api_v1:leave:encashments-bulk-action',
                      kwargs={'organization_slug': self.organization.slug}) + "?as=hr"

        payload = {
            "actions": [
                {
                    "id": record_1.id,
                    "status": "Approved",
                    "remarks": "Good"
                },
                {
                    "id": record_2.id,
                    "status": "Denied",
                    "remarks": "Bad"
                }
            ]
        }

        self.client.force_login(self.admin)
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, 200, response.data)

        # retry acting on same instance
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, 400, response.data)

        # both should have error dict filled
        self.assertNotEqual(response.data["actions"][0], {})
        self.assertNotEqual(response.data["actions"][1], {})
