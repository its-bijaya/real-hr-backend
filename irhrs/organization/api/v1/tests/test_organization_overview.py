import json

from django.urls import reverse
from rest_framework import status

from irhrs.organization.api.v1.tests.setup import OrganizationSetUp


class TestOrganizationOverView(OrganizationSetUp):
    def setUp(self):
        super().setUp()
        self.kwargs = {
                'organization_slug': self.organization.slug
            }

    @property
    def org_detail(self):
        return reverse(
            'api_v1:organization:get-update-organization-detail',
            kwargs=self.kwargs
        )

    def test_organization_overview_for_normal_user_view(self):
        """
        test for organization overview from normal user view
        :return:
        """
        """
        --------------------------------------------------------------------------------------------
        trying to get overview for existing organization  
        """
        response = self.client.get(
            self.org_detail
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = response.json()
        org = self.organization

        self.assertEqual(result.get('name'), org.name)
        self.assertEqual(result.get('abbreviation'), org.abbreviation)
        self.assertEqual(result.get('registration_number'), org.registration_number)
        self.assertEqual(result.get('ownership'), org.ownership)
        self.assertEqual(result.get('size'), org.size)

        """
        --------------------------------------------------------------------------------------------
        trying to get overview for non existing organization 
        """
        self.kwargs = {
            'organization_slug': 'non-existing-organization'
        }
        response = self.client.get(
            self.org_detail
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json().get('detail'), 'Not found.')
