from irhrs.recruitment.models.external_profile import External
from django.urls import reverse

from irhrs.core.constants import organization
from irhrs.core.constants.common import KSA_TYPE
from irhrs.organization.models import knowledge_skill_ability
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.constants.common import ABILITY, KNOWLEDGE
from irhrs.organization.models.organization import Organization


class TestRecruitmentExternalProfileAPI(RHRSAPITestCase):
    organization_name = "Aayulogic Pvt. Ltd."
    users = [
        ('admin@example.com', 'admin', 'Male'),
        ('normal@example.com', 'normal', 'Male'),
    ]
    def setUp(self):
        super().setUp()
        self.url = reverse(                     
            'api_v1:recruitment:external:external-list',
            kwargs={'organization_slug': self.organization.slug}
        )
    def patch_url(self, pk):
        return reverse(
            'api_v1:recruitment:external:external-detail', 
            kwargs={'organization_slug': self.organization.slug, 'pk':pk}
        )
        
    def test_recuitment_external_profile(self):
        self.client.force_login(self.admin)
        organization = self.organization
        ksao = KnowledgeSkillAbility.objects.create(name='chess', description='I can play chess very well', ksa_type=KNOWLEDGE, organization=self.organization)
        ksao2 = KnowledgeSkillAbility.objects.create(name='coding',description='I can write code',ksa_type=ABILITY, organization=self.organization)

        payload = {
            'user': {
                'full_name': self.created_users[0].full_name,
                'phone_number': 1234,
                'email': "example@example.com",
            },
            'ksao': [ksao.slug, ksao2.slug]

        }
        response = self.client.post(
            self.url,
            payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            201
        )
        self.assertEqual(
            Organization.objects.get(name="Aayulogic Pvt. Ltd.").name,
            'Aayulogic Pvt. Ltd.'
        )
        response = self.client.get(
            self.url
        )
        self.assertEqual(
            response.status_code,
            200
        )
        expected_output = {
            'name': 'chess',
            'slug': 'knowledge-chess',
        }
        self.assertEqual(
            response.json().get('results')[0].get('ksao')[0],
            expected_output
        )
        payload = {
            'user': {
                'full_name': self.created_users[0].full_name,
                'phone_number': 1234,
                'email': "example@example.com",
            },
            'ksao': [ksao.slug, ksao2.slug]
        }

        response = self.client.patch(
            self.patch_url(External.objects.first().id),
            payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            External.objects.first().user.full_name,
            self.created_users[0].full_name
        )

