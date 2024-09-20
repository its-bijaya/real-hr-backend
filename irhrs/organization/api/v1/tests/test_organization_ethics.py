import random
from random import randint

from django.urls import reverse
from rest_framework import status

from irhrs.organization.api.v1.tests.setup import OrganizationSetUp
from irhrs.organization.models import OrganizationEthics


class TestOrganizationEthics(OrganizationSetUp):
    moral_ethics = ["Do", "Dont", "Rules", "Regulation"]

    def setUp(self):
        super().setUp()
        self.generate_ethics()

    def generate_ethics(self):
        for _ in range(randint(1, 10)):
            OrganizationEthics(
                organization=self.organization,
                moral=random.choice(self.moral_ethics),
                published=random.choice([False, True]),
                is_archived=random.choice([False, True])
            )

    def test_organization_ethics(self):
        """
        test get method for organization ethics
        :return:
        """
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        ethics = self.organization.ethics.filter(
            is_archived=False,
            published=True
        )
        response = self.client.get(
            reverse(
                'api_v1:organization:organization-ethics-list',
                kwargs={
                    'organization_slug': self.organization.slug
                }
            ),
            data={
                'published': True,
                'archived': False
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), ethics.count())
        results = response.json().get('results')
        for i, ethic in enumerate(ethics):
            self.assertEqual(ethic.title, results[i].get('title'))
            self.assertEqual(ethic.description, results[i].get('description'))
            self.assertEqual(ethic.slug, results[i].get('slug'))
            self.assertEqual(ethic.organization_id, results[i].get('organization'))
            self.assertEqual(ethic.moral, results[i].get('moral'))
