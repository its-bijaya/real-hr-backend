import random
from random import randint

from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSUnitTestCase
from irhrs.core.constants.common import KSA_TYPE
from irhrs.core.utils import nested_get
from irhrs.organization.api.v1.tests.factory import KSAFactory, OrganizationFactory
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility


class TestKSA(RHRSUnitTestCase):
    @property
    def ksa_url(self):
        action = 'detail' if 'slug' in self.kwargs else 'list'
        return reverse(
            f"api_v1:organization:ksa-settings-{action}",
            kwargs=self.kwargs if self.kwargs else None
        )

    def test_ksa(self):
        for ksa_type in dict(KSA_TYPE).keys():
            self.kwargs = {
                'organization_slug': self.organization.slug,
                'ksa_type': ksa_type
            }
            self._test_add_ksa(ksa_type)
            self._test_list_ksa(ksa_type)
            self._test_update_ksa(ksa_type)

    def _test_add_ksa(self, ksa_type):
        # for valida data
        data = {
            'name': self.fake.word(),
            'description': self.fake.text()
        }
        request_data = dict(
            path=self.ksa_url,
            data=data,
            format='json'
        )
        response = self.client.post(
            **request_data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            "Must be created."
        )

        obj = KnowledgeSkillAbility.objects.get(slug=response.json().get('slug'))

        # trying to create with duplicate data
        response = self.client.post(
            **request_data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            "Name, organization and ksa_type must be unique together"
        )

        self.kwargs.update(
            {
                'slug': obj.slug
            }
        )
        self._test_delete_ksa(ksa_type, obj=obj)

    def _test_list_ksa(self, ksa_type):
        if 'slug' in self.kwargs:
            del self.kwargs['slug']
        # testing for validating list api of ksa
        other_org = OrganizationFactory()
        for _ in range(randint(5, 10)):
            KSAFactory(
                ksa_type=ksa_type,
                organization=random.choice([self.organization, other_org])
            )
        response = self.client.get(
            self.ksa_url
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'Must be 200 ok.'
        )
        self.validate_data(
            results=nested_get(response.json(), 'results'),
            data=KnowledgeSkillAbility.objects.filter(
                ksa_type=ksa_type,
                organization=self.organization
            )
        )

    def _test_delete_ksa(self, ksa_type, obj):
        response = self.client.delete(
            self.ksa_url
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def _test_update_ksa(self, ksa_type):
        ksa = [KSAFactory(ksa_type=ksa_type, organization=self.organization) for _ in range(5)]
        # try to update data
        self.kwargs.update({
            'slug': ksa[0].slug
        })
        data = {
            'name': self.fake.word(),
            'description': self.fake.text()
        }
        response = self.client.patch(
            self.ksa_url,
            data=data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.validate_data(
            results=[data],
            data=KnowledgeSkillAbility.objects.filter(slug=response.json().get('slug'))
        )

        # to to update ksa with existing other ksa name
        self.kwargs.update({
            'slug': ksa[1].slug
        })
        response = self.client.patch(
            self.ksa_url,
            data={
                'name': ksa[2].name,
                'description': self.fake.text()
            }
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'Name must be unique for Knowledge'
        )

