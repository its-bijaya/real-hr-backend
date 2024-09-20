from django.contrib.auth import get_user_model
from django.urls import reverse
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.common.models.commons import ReligionAndEthnicity


USER = get_user_model()
class TestProfileCompleteness(RHRSAPITestCase):
    users = [('hr@email.com', 'secret', 'Male'),
             ('test@example.com', 'supersecret', 'Male'),
             ]
    organization_name = 'Google Inc.'

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'api_v1:hris:profile-completeness-list',
            kwargs={
                'organization_slug': self.organization.slug,
            }
        ) + '?ordering=full_name'
        user_1_detail = self.created_users[0].detail
        user_2_detail = self.created_users[1].detail
        religion = ReligionAndEthnicity.objects.create(name="Hindu", category="Religion")
        user_1_detail.religion = religion
        user_1_detail.save()
        user_2_detail.save()
        self.client.force_login(self.admin)

    def test_profile_completeness_api_works(self):
        res = self.client.get(
            self.url
        )
       
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['results']), 2)
        self.assertEqual(res.json()['results'][0]['user_detail']['full_name'], 'hr hr')
        self.assertEqual(res.json()['results'][1]['user_detail']['full_name'], 'test test')
        self.assertEqual(res.json()['results'][0]['completeness_percent'], 20)
        self.assertEqual(res.json()['results'][1]['completeness_percent'], 10)
