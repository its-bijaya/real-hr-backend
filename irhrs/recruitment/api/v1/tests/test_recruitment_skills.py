from irhrs.common.api.tests.common import RHRSAPITestCase
from django.urls import reverse

from irhrs.common.models import Skill

class TestRecruitmentSkillAPI(RHRSAPITestCase):
    organization_name = "Aayulogic"
    users = [
        ('admin@example.com', 'admin', 'Male'),
        ('normal@example.com', 'normal', 'Male'),
    ]
    def setUp(self):
        super().setUp()
        self.url = reverse(                     
            'api_v1:recruitment:common:skill-list'
        ) + f'?organization={self.organization.slug}'

    def patch_url(self, pk):
        return reverse(
            'api_v1:recruitment:common:skill-detail', kwargs={'pk':pk}
        ) + f'?organization={self.organization.slug}'
        

    def test_recruitment_skill(self):
        self.client.force_login(self.admin)
        payload = {
            'name': 'Coding',
            'description': 'I love coding.'
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
            response.json().get('name'),
            'Coding'
        )
        self.assertEqual(
            Skill.objects.get(name="Coding").name,
            "Coding"
        )
        self.assertEqual(
            response.json().get('description'),
            'I love coding.'
        )
        self.assertEqual(
            Skill.objects.get(description='I love coding.').description,
            'I love coding.'
        )
        response = self.client.get(
            self.url
        )
        self.assertEqual(
            response.status_code,
            200
        )
        expected_output = {
            'slug': 'coding',
            'description': 'I love coding.',
            'name': 'Coding'
        }
        self.assertEqual(
            response.json().get('results')[0],
            expected_output
        )
        payload = {
            'name': 'Coding',
            'description': 'I am passinate about coding'
        }
        response = self.client.patch(
            self.patch_url(Skill.objects.first().id),
            payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.json().get("description"),
            'I am passinate about coding'
        )
        self.assertEqual(
            Skill.objects.get(description='I am passinate about coding').description,
            'I am passinate about coding'
        )
        payload = {
            'name': "Coding",
            'description': 'I am passinate about coding'
        }
        response = self.client.post(
            self.url,
            payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.json().get("name")[0],
            'This field must be unique.'
        )


