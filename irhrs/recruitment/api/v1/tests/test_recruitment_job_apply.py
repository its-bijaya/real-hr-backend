from irhrs.common.api.tests.common import RHRSAPITestCase
from django.urls import reverse

from irhrs.organization.api.v1.tests.factory import OrganizationFactory

class TestRecruitmentSkillAPI(RHRSAPITestCase):
    organization_name = "Aayulogic"
    users = [
        ('admin@example.com', 'admin', 'Male'),
        ('normal@example.com', 'normal', 'Male'),
    ]
    def setUp(self):
        super().setUp()
        self.url = reverse(                     
            'api_v1:recruitment:common:employment_status-list'
        ) 
    