from django.urls import reverse
from rest_framework import status

from ...api.tests.common import RHRSAPITestCase


class DocumentCategoryTestCase(RHRSAPITestCase):
    organization_name = 'ABC Company'
    users = [
        ('dellone@dell.com', 'password', 'Male'),
        ('dellzero@dell.com', 'password', 'Female'),
    ]

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1]
        )
        self.url = reverse('api_v1:commons:document-category-list')

    def test_create_document_category(self):
        response = self.client.post(
            self.url,
            data={
                'name': 'New Document Type'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('name'),
                         'New Document Type')

    def test_get_document_category(self):
        # Create New
        _ = self.client.post(
            self.url,
            data={
                'name': 'Test Category'
            }
        )
        response = self.client.get(
            self.url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('results')[0].get('name'),
                         'Test Category')

    def test_search_document_category(self):
        # Create New Category
        _ = self.client.post(
            self.url,
            data={
                'name': 'New Document Category'
            }
        )
        response = self.client.get(
            self.url+'?name=new'
        )
        self.assertEqual(response.data.get('results')[0].get('name'),
                         'New Document Category')

        response = self.client.get(
            self.url+'?search=asdfasdfasdf'
        )
        self.assertFalse(response.data.get('results'))
