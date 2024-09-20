import json
import os

from django.urls import reverse
from rest_framework import status

from config import settings
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.recruitment.models import Province, Country, OrganizationBranch


def seed_locations():
    # REFERENCE seed_locations.py
    with open(
        os.path.abspath(
            os.path.join(
                settings.PROJECT_DIR,
                'fixtures/commons/locations.json'
            )
        )
    ) as f:
        location_data = json.load(f)
        countries = location_data['countries']
        provinces = location_data['provinces']

        for country_data in countries:
            _id = country_data.pop('id')
            Country.objects.get_or_create(id=_id, defaults=country_data)

        nepal = Country.objects.get(name="Nepal")
        for province in provinces:
            _id = province.pop('id')
            province.update({"country": nepal})
            Province.objects.get_or_create(id=_id, defaults=province)


class TestOrganizationBranch(RHRSAPITestCase):
    organization_name = "Google"
    users = (
        ('admin@gmail.com', 'secretWorldIsThis', 'Male'),
        ('hello@hello.com', 'secretThing', 'Male'),
        ('helloa@hello.com', 'secretThing', 'Male'),
        ('hellob@hello.com', 'secretThing', 'Male')
    )

    def setUp(self):
        super().setUp()
        seed_locations()
        self.client.force_login(self.admin)

    @property
    def branch_url(self):
        return reverse(
            'api_v1:organization:organization-branch-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    @property
    def payload(self):
        return {
            "name": "Kathmandu",
            "description": "Kathmandu Branch",
            "contacts": {"Phone": "9812345562/9876543210"},
            "branch_manager": self.created_users[1].id,
            "email": "info@aayulogic.com",
            "address": "shantinagar, kathmandu",
            "code": "1234",
            "province": Province.objects.get(name="Bagmati Pradesh").id,
            "country": Country.objects.get(name="Nepal").id,
            "is_archived": False,
            "mailing_address": "info@aayulogic.com",
            "region": "Asia"
        }

    def test_organization_branch(self):
        # create new organization branch
        response = self.client.post(
            self.branch_url,
            self.payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        # test whether created branch is shown in list or not
        response = self.client.get(
            self.branch_url
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('results')[0].get("name"),
            "Kathmandu"
        )
        self.assertEqual(
            response.json().get('statistics').get('total_branch'),
            1
        )

        # update created branch
        update_url = reverse(
            'api_v1:organization:organization-branch-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'slug': 'kathmandu'
            }
        )
        data = self.payload
        data["description"] = "Kathmanduu"
        self.assertEqual(
            OrganizationBranch.objects.first().description,
            "Kathmandu Branch"
        )
        response = self.client.put(
            update_url,
            data=data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            OrganizationBranch.objects.first().description,
            "Kathmanduu"
        )

        # select country Nepal and don't send province. This should raise ValidationError
        data = self.payload
        data["province"] = None
        response = self.client.put(
            update_url,
            data=data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json().get('province'),
            ['Please select valid province.']
        )

        # select country other than Nepal and don't send province. This should pass
        data = self.payload
        india = Country.objects.get(name="India")
        data["country"] = india.id
        data["province"] = None
        response = self.client.put(
            update_url,
            data=data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            OrganizationBranch.objects.first().country_ref,
            india
        )
        self.assertFalse(OrganizationBranch.objects.first().province)
