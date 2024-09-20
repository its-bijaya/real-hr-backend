import datetime
import json
from irhrs.recruitment.models.common import Template
from irhrs.recruitment.api.v1.tests.factory import JobApplyFactory, JobFactory
from irhrs.recruitment.models.applicant import Applicant
from irhrs.organization.models import organization
from irhrs.recruitment.models import job_apply
from irhrs.recruitment.constants import EXTERNAL_USER_LETTER, MORNING, PENDING, SCREENED, SHORTLISTED
from irhrs.recruitment.models.job import Job
from irhrs.common.api.tests.common import RHRSAPITestCase
from django.urls import reverse

from irhrs.common.models import Skill
from irhrs.organization.api.v1.tests.factory import EmploymentJobTitleFactory, EmploymentLevelFactory, EmploymentStatusFactory
class TestRecruitmentNoObjection(RHRSAPITestCase):
    organization_name = "Aayulogic"
    users = [
        ('admin@example.com', 'admin', 'Male'),
        ('normal@example.com', 'normal', 'Male'),
    ]

    def setUp(self):
        super().setUp()
        self.job = Job.objects.create(
            title=EmploymentJobTitleFactory(organization=self.organization),
            organization=self.organization,
            vacancies=1,
            employment_status=EmploymentStatusFactory(organization=self.organization),
            preferred_shift=MORNING,
            employment_level=EmploymentLevelFactory(organization=self.organization),
            salary_visible_to_candidate=False,
            alternate_description="Nothing",
            description="",
            specification="Assistant",
            is_skill_specific=True,
            education_degree="Bachlor",
            education_program=None,
        )
        self.url = reverse(                     
            'api_v1:recruitment:no_objection:no_objection-list',
            kwargs={
                'job_slug':self.job.slug
                }
        ) 
    def test_recruitment_no_objection(self):
        self.client.force_login(self.admin)
        job_apply = JobApplyFactory()
        job = JobFactory(organization=self.organization)
        template1 = Template.objects.create(title='Title',message='Hello World',type=EXTERNAL_USER_LETTER,organization=self.organization,)
        email_template = template1.slug
        
        
        payload ={
            'title' : 'Title_for_no_objection',
            'job_apply' :job_apply.id,
            'job' : job.slug,
            'stage' : SHORTLISTED,
            'score' : 0,
            'email_template': email_template,
            'report_template': email_template,
            'status': PENDING,
            'responsible_person': self.created_users[1].id,
        }
        response = self.client.post(
            self.url,
            data=payload,
            format='json',
        )

# Test Case Scenerio:
# 1. Approve candidate should get no objection before going for pre screening
#    - conditions for acceptance of no_objection
#         * Responsible person should chanage status of the candidate to APPROVED
# 2. One should complete assesment and interview after that HR send candidate for no objection after interview with score
# 3. Salary should be declared and verified by HR for no objection process 