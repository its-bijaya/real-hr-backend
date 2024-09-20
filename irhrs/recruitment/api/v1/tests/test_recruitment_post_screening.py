from django.http import response
from django.urls import reverse
from irhrs.organization.models import organization

from rest_framework import status
from irhrs.attendance.constants import APPROVED, FORWARDED

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.notification.models.notification import Notification
from irhrs.organization.api.v1.tests.factory import EmploymentJobTitleFactory, EmploymentLevelFactory, EmploymentStatusFactory, KnowledgeSkillAbilityFactory
from irhrs.recruitment.api.v1.tests.factory import JobApplyFactory, JobFactory, NoObjectionFactory, PostScreeningFactory, TemplateFactory
from irhrs.recruitment.constants import COMPLETED, DENIED, MORNING, PENDING, PROGRESS, REJECTED, SCREENED, SHORTLISTED
from irhrs.recruitment.models import job_apply
from irhrs.recruitment.models.common import JobBenefit, Template
from irhrs.recruitment.models.job import Job
from irhrs.recruitment.models.job_apply import JobApply, JobApplyStage, NoObjection, PostScreening, PreScreening, PreScreeningInterview
from irhrs.users.models.supervisor_authority import UserSupervisor

class TestRecruitmentPostScreeningAPI(RHRSAPITestCase):
    organization_name = "Apple.inc"
    users = [
        ('mark@example.com', 'Mark', 'Male'),
        ('bill@example.com', 'Bill', 'Male'),
        ('elon@example.com', 'Elon', 'Male'),
        ('jeff@example.com', 'Jeff', 'Male')
    ]

    def patch_url(self, pk):
        return reverse(
            'api_v1:recruitment:post_screening-detail',
            kwargs={
                'job_slug':self.job.slug,
                'pk' : pk
            }
    ) 

    def patch_url_marking(self, pk):
        return reverse(
            'api_v1:recruitment:post_screening-detail',
            kwargs={
                'job_slug':self.job.slug,
                'pk' : pk
            }
    ) 

    def get_url(self, pk):
        return reverse(
            'api_v1:recruitment:no_objection:no_objection-memorandum-report',
        kwargs={
            'job_slug':self.job.slug,
            'pk':pk
        }
    ) 
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
            hiring_info={"pre_screening_letter": None},
            specification="Assistant",
            is_skill_specific=True,
            education_degree="Bachlor",
            education_program=None,
        )
        self.job_apply1 = JobApplyFactory(
            job=self.job
        )

        UserSupervisor.objects.create(
            user= self.created_users[1],
            supervisor=self.created_users[0],
            user_organization=self.organization,
            supervisor_organization=self.organization
        )

        self.url = reverse(
            'api_v1:recruitment:pre_screening-post_screening_forward',
            kwargs={
                'job_slug':self.job.slug
            }
        )

    def test_recruitment_post_screening_pending(self):
        self.client.force_login(self.admin)
        self.job.skills.add(KnowledgeSkillAbilityFactory(organization = self.organization))
        
        PreScreening.objects.create(
            job_apply = self.job_apply1,
            status=COMPLETED,
            verified=True,
            score=100
        )
        payload = {
            "responsible_person": self.created_users[0].id,
            "score": 50,
        }

        response = self.client.post(
            self.url,
            payload,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK    
        )

        # when mark is updated status need to change to "Completed"
        self.assertEqual(
            PreScreening.objects.first().status,
            COMPLETED
        )

        self.url_get= reverse(
            'api_v1:recruitment:post_screening-list',
            kwargs={
                'job_slug':self.job.slug
            }
        ) + f'?status=Pending&organization={self.organization.slug}&as=hr'

        response1 = self.client.get(
            self.url_get
        )

        self.assertEqual(
            response1.json().get('results')[0].get('status'),
            PENDING
        )
        
        self.assertEqual(
            PostScreening.objects.first().id,
            response1.json().get('results')[0].get('id')
        )
 
        payload = {
            "responsible_person":self.created_users[0].id,
            "status":PENDING
        }

        response = self.client.patch(
            self.patch_url(PostScreening.objects.first().id),
            payload,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertTrue(response1.json().get("responsible_person") != PostScreening.objects.first().responsible_person.id)

        self.assertEqual(
            Notification.objects.first().recipient,
            self.created_users[0]            
            )

        self.assertEqual(
            Notification.objects.first().text,
            "You have been assigned as Responsible person for Final Shortlist of a candidate."
        )

        payload_marking = {
            "score":95,
            "status":PROGRESS
        }

        response = self.client.patch(
            self.patch_url_marking(PostScreening.objects.first().id),
            payload_marking,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        
        self.assertEqual(
            PostScreening.objects.first().status,
            PROGRESS
        )

        self.assertEqual(
            PostScreening.objects.first().score,
            95.0
        )
    
    def test_forward_both_score(self):
        no_objection = NoObjectionFactory(
            job=self.job
        )
       
        self.get_both_score=reverse(
            'api_v1:recruitment:no_objection:no_objection-memorandum-report',
                kwargs={
                    'job_slug': self.job.slug, 'pk': NoObjection.objects.first().id
                }
            ) + f'?organization={self.organization.slug}&as=hr'

        self.client.force_login(self.admin) 
        
        response = self.client.get(
            self.get_both_score
        )

    def test_status_completed(self):
        post_screening = PostScreeningFactory(
            job_apply = self.job_apply1,
            score = 90,
            data={
                # hack: Viewset requires data but this test doesn't -
                # need data this is why we make random json here
                "Detail":"Post screening data" 
            }
        )
        
        self.status_completed_url=reverse(
            'api_v1:recruitment:post_screening-complete',
                kwargs={
                    'job_slug': self.job.slug, 'pk': PostScreening.objects.first().id
                }
            ) + f'?organization={self.organization.slug}&as=hr'
        
        payload = {
            "status" : PROGRESS,
        }

        self.client.force_login(self.admin)
    
        response = self.client.post(
            self.status_completed_url,
            data=payload,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            PostScreening.objects.first().status,
            COMPLETED
        )

    def test_initialize_no_objection(self):
        self.initialize_no_objection_url = reverse(
            'api_v1:recruitment:no_objection:no_objection-list',
            kwargs={
                'job_slug': self.job.slug
            }
        )

        self.client.force_login(self.admin)

        payload= {
            "score":20,
            "title": "No Objection for python devloper",
            "responsible_person": self.created_users[0].id,
            "email_template":TemplateFactory().slug,
            "report_template":TemplateFactory().slug,
            "stage":SHORTLISTED,
        }
        
        response = self.client.post(
            self.initialize_no_objection_url,
            data = payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.json().get("id"),
            NoObjection.objects.first().id
        )
        self.assertEqual(
            SHORTLISTED,
            NoObjection.objects.first().stage
        )
        self.assertEqual(
            response.json().get("responsible_person"),
            NoObjection.objects.first().responsible_person_id
        )

    def test_no_objection_verify(self):
        no_objection = NoObjectionFactory(
            job_apply = self.job_apply1,
            job = self.job,
            responsible_person = self.created_users[0],
            status = COMPLETED
        )
        self.no_objection_verify_url = reverse(
            'api_v1:recruitment:no_objection:no_objection-verify',
            kwargs={
                'job_slug': self.job.slug, 'pk': NoObjection.objects.first().id
            }
        )

        self.client.force_login(self.admin)
        payload = {
            'remarks': 'Denied process not completed',
            'status':DENIED,
            'detail': 'This is the detail of no objection'
        }

        response = self.client.post(
            self.no_objection_verify_url,
            data=payload,
            format='json'
        )
        
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            JobApply.objects.first().status,
            REJECTED
        )

        self.assertTrue(
            JobApplyStage.objects.filter(
                job_apply=JobApply.objects.first(),
                status=REJECTED).exists()
            )

    def test_no0bjection_approved(self):
        
        no_objection = NoObjectionFactory(
            job_apply = self.job_apply1,
            job = self.job,
            responsible_person = self.created_users[0],
            status = COMPLETED
        )

        self.prescreening_interview_status = reverse(
            'api_v1:recruitment:no_objection:no_objection-list',
            kwargs= {
                'job_slug':self.job.slug
            }
        )+ f'?organization={self.organization.slug}&as=hr'

        self.client.force_login(self.admin)

        response = self.client.get(
            self.prescreening_interview_status
        )

        self.assertEqual(
            response.json().get('results')[0].get('stage'),
            SCREENED
        )

        self.assertEqual(
            response.json().get('results')[0].get('status'),
            COMPLETED
        )

    def test_no_objection_verify_approve(self):
        no_objection = NoObjectionFactory(
            job_apply = self.job_apply1,
            job = self.job,
            responsible_person = self.created_users[0],
            status = COMPLETED
        )
        
        post_screening = PostScreeningFactory(
            job_apply=self.job_apply1,
            responsible_person = self.created_users[1],
            status=FORWARDED
            )
        
        pre_screening = PreScreening.objects.create(
            job_apply=self.job_apply1,
            status=FORWARDED,
            verified=True,
            score=100
        )
        pre_screening_interview = PreScreeningInterview.objects.create(
            responsible_person=self.admin,
            job_apply=self.job_apply1,
        )

        self.client.force_login(self.admin)

        self.no_objection_verify_url_approve = reverse(
            'api_v1:recruitment:no_objection:no_objection-verify',
            kwargs={
                'job_slug': self.job.slug, 'pk': NoObjection.objects.first().id
            }
        )

        payload = {
            'remarks': 'Approved all good to go',
            'status': APPROVED,
            'detail': 'This is no objection'
        }

        response = self.client.post(
            self.no_objection_verify_url_approve,
            data=payload,
            format='json'
        )
        
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            NoObjection.objects.first().status,
            APPROVED
        )

        self.approved_status = reverse(
            'api_v1:recruitment:no_objection:no_objection-list',
            kwargs={
                'job_slug':self.job.slug
            }
        ) + f'?organization={self.organization.slug}&as=hr'

        self.client.force_login(self.admin)

        response = self.client.get(
            self.approved_status
        )

        self.assertEqual(
            response.json().get('results')[0].get("status"),
            APPROVED
        )

        self.prescreening_status = reverse(
            'api_v1:recruitment:post_screening-list',
            kwargs={
                'job_slug':self.job.slug
            }
        ) + f'?status={FORWARDED}&organization={self.organization.slug}&as=hr'

        response = self.client.get(
            self.prescreening_status
        )

        self.assertEqual(
            response.json().get('results')[0].get('status'),
            FORWARDED
        )

        self.prescreening_status = reverse(
            'api_v1:recruitment:pre_screening_interview-list',
            kwargs={
                'job_slug':self.job.slug
            }
        ) + f'?status={PENDING}&organization={self.organization.slug}&as=hr'

        response = self.client.get(
            self.prescreening_status
        )

        self.assertEqual(
            response.json().get('results')[0].get('status'),
            PENDING
        )
        