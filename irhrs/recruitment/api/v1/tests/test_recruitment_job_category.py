# from irhrs.core.mixins.viewset_mixins import ParentFilterMixin
from irhrs.common.api.tests.common import RHRSAPITestCase
from django.urls import reverse

from irhrs.recruitment.models.common import JobCategory

class TestRecruitmentJobCategoryAPI(RHRSAPITestCase):
    organization_name = "Aayulogic"
    users = [
        ('admin@example.com', 'admin', 'Male'),
        ('normal@example.com', 'normal', 'Male'),
    ]
    def setUp(self):
        super().setUp()
        self.url = reverse(
            'api_v1:recruitment:common:job_category-list'
        ) + f'?organization={self.organization.slug}'

    def patch_url(self, pk):
        return reverse(
            'api_v1:recruitment:common:job_category-detail', kwargs={'pk':pk}
        ) + f'?organization={self.organization.slug}'
        

    def test_recruitment_job_catagory(self):
        self.client.force_login(self.admin)
        payload = {
            'parent': '',
            'name': 'Programmer'
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
            JobCategory.objects.get(name="Programmer").name,
            "Programmer"
        )
        payload = {
            'parent': JobCategory.objects.get(name="Programmer").id,
            'name': 'Developer'
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
            JobCategory.objects.get(name="Developer").parent,
            JobCategory.objects.get(name="Programmer")
        )
        response = self.client.get(
            self.url
        )
        self.assertEqual(
            response.status_code,
            200
        )
        expected_output = {
            'slug':'programmer',
            'name': 'Programmer',
            'parent': 1
        }
        self.assertEqual(
            response.json().get('results')[0].get('slug'),
            expected_output.get('slug')
        )
        payload = {
            'parent': JobCategory.objects.get(name="Developer").id,
            'name': 'QAQC'
        }
        response = self.client.patch(
            self.patch_url(JobCategory.objects.first().id),
            payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.json().get('name'),
            'QAQC'
        )
