"""
All tests related to office equipment category are created here
"""
from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.constants.common import TANGIBLE


class EquipmentCategoryTestCase(RHRSAPITestCase):
    organization_name = 'Aayulogic Pvt. Ltd.'
    users = [
        ('me@username.com', 'password', 'Male'),
        ('metwo@username.com', 'password', 'Female')
    ]

    def setUp(self):
        super().setUp()
        self.client.login(email='me@username.com',
                          password='password')
        self.url = reverse('api_v1:commons:equipment-category-list')

    def test_create_equipment_category(self):
        data = {
            'name': 'Desk',
            'type': TANGIBLE
        }
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('name'), data.get('name'))

        # Invalid Data
        data = {
            'name': '',
            'type': TANGIBLE
        }
        response = self.client.post(self.url,
                                    data=data
                                    )
        self.assertEqual(response.data.get('name')[0].__str__(), 'This field may not be blank.')

        # Duplicated Data
        data = {
            'name': 'Desk',
        }
        response = self.client.post(self.url,
                                    data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('name')[0].__str__(), 'equipment category with this name already exists.')

    def test_search_test_equipment_category(self):
        _ = self.client.post(self.url,
                             data={
                                 'name': 'new equipment',
                                 'type': TANGIBLE
                             })
        response = self.client.get(
            self.url+'?name=new'
        )
        self.assertEqual(response.data.get('results')[0].get('name'),
                         'new equipment')
        response = self.client.get(
            self.url +'?search=kklskdf'
        )
        self.assertFalse(response.data.get('results'))

    def test_update_equipment_category(self):
        data = {
            'name': 'Desk',
            'type': TANGIBLE
        }
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('name'), data.get('name'))
        new_data = {
            'name': 'Chair',
            'type': TANGIBLE
        }
        detail_url = reverse('api_v1:commons:equipment-category-detail', kwargs={
            'slug': 'desk'})
        response = self.client.put(detail_url, data=new_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), 'Chair')
        self.assertEqual(response.data.get('type'), TANGIBLE)


