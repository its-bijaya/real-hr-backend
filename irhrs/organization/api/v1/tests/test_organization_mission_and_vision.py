from random import randint

from django.urls import reverse
from rest_framework import status

from irhrs.organization.api.v1.tests.setup import OrganizationSetUp
from irhrs.organization.api.v1.tests.factory import (OrganizationMissionFactory,
                                                     OrganizationVisionFactory)


class TestOrganizationDocument(OrganizationSetUp):
    files = []

    def setUp(self):
        super().setUp()
        self.generate_mission()
        self.generate_vision()

    def generate_mission(self):
        OrganizationMissionFactory.create_batch(
            10,
            organization=self.organization,
        )

    def generate_vision(self):
        OrganizationVisionFactory(organization=self.organization)

    def test_organization_mission(self):
        """
        tested get method for mission of an organization
        :return:
        """
        missions = self.organization.missions.all()

        self.client.login(email=self.users[1][0], password=self.users[1][1])
        response = self.client.get(
            reverse(
                'api_v1:organization:organization-mission-list',
                kwargs={
                    'organization_slug': self.organization.slug
                }
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), missions.count())
        results = response.json().get('results')
        for i, _mission in enumerate(missions):
            self.assertEqual(_mission.slug, results[i].get('slug'))
            self.assertEqual(_mission.title, results[i].get('title'))
            self.assertEqual(_mission.description, results[i].get('description'))
            self.assertEqual(_mission.organization_id, results[i].get('organization'))

    def test_organization_vision(self):
        """
        tested get method for vision of an organization
        :return:
        """
        vision = self.organization.vision

        self.client.login(email=self.users[1][0], password=self.users[1][1])
        response = self.client.get(
            reverse(
                'api_v1:organization:organization-vision',
                kwargs={
                    'organization_slug': self.organization.slug
                }
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        self.assertEqual(vision.title, response.get('title'))
        self.assertEqual(vision.slug, response.get('slug'))
