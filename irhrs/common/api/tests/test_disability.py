from django.urls import reverse

from irhrs.common.models import Disability
from .common import RHRSAPITestCase


class TestDisability(RHRSAPITestCase):
    organization_name = 'Organization'
    users = [
        ('test@example.com', 'helloSecretWorld', 'Male')
    ]

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])

    def test_create(self):
        url = reverse('api_v1:commons:disability-list')
        data = {
            "title": "disability1",
            "description": "This is disability."
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

        slug = response.data.get('slug')
        disability = Disability.objects.get(slug=slug)

        for attr in data:
            self.assertEqual(getattr(disability, attr), data.get(attr))

        wrong_data = {
            "title": "",
            "description": "The description"
        }
        response = self.client.post(url, data=wrong_data)
        self.assertEqual(response.status_code, 400)

        # try to send same title again
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_list(self):
        data = [
            {"title": "disability1",
             "description": "This is disability."},
            {"title": "disability12",
             "description": "This is disability12."},
            {"title": "disability3",
             "description": "This is disability3."},
            {"title": "disability4",
             "description": "This is disability4."},
        ]
        url = reverse('api_v1:commons:disability-list')
        for datum in data:
            self.client.post(url, data=datum)

        # test list
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), len(data))

        # test search
        response = self.client.get(url, data={'search': 'disability1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 2)
