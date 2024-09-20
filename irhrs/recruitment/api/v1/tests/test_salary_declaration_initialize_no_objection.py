from django.urls.base import reverse
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.organization.api.v1.tests.factory import EmploymentJobTitleFactory, \
    EmploymentLevelFactory, EmploymentStatusFactory
from irhrs.recruitment.api.v1.tests.factory import JobApplyFactory, NoObjectionFactory
from irhrs.recruitment.constants import APPROVED, COMPLETED, MORNING, PENDING, \
    PROGRESS, SALARY_DECLARATION_LETTER
from irhrs.recruitment.models.common import Template
from irhrs.recruitment.models.job import Job
from irhrs.recruitment.models.job_apply import JobApply, NoObjection, \
    ReferenceCheck, SalaryDeclaration
from irhrs.users.models.supervisor_authority import UserSupervisor
from irhrs.users.models.user import ExternalUser


class TestSalaryDeclarationInitializeNoObjection(RHRSAPITestCase):

    users = [
        ("admin@example.com", "admin", "male"),
        ("user@example.com", "example", "female")
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
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
            specification="Trainee",
            is_skill_specific=True,
            education_degree="Bachelor",
            education_program=None,
        )
        self.job_apply = JobApplyFactory(
            job=self.job
        )

        UserSupervisor.objects.create(
            user=self.created_users[1],
            supervisor=self.created_users[0],
            user_organization=self.organization,
            supervisor_organization=self.organization
        )
        
        self.salary_declaration_url = reverse(
            "api_v1:recruitment:salary:declaration-list",
            kwargs={
                'job_slug': self.job.slug
            } 
        ) + f"?organization={self.organization.slug}&as=hr"

    def test_reference_check_completed_and_salary_declaration_pending(self):
        # reference check completed
        ReferenceCheck.objects.create(
            job_apply=self.job_apply,
            status=COMPLETED,
            verified=True,
            score=100
        )
        url = reverse(
            "api_v1:recruitment:reference_check:reference_check-salary_declaration_forward",
            kwargs={
                'job_slug': self.job.slug
            }
        )
        payload = {
            "responsible_person": self.created_users[0].id,
            "score": 70,
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            ReferenceCheck.objects.first().status,
            COMPLETED
        )

        # salary_declaration_pending
        response = self.client.get(self.salary_declaration_url, format='json')
        
        self.assertEqual(
            response.status_code, 200
        )

        self.assertEqual(
            response.json().get('results')[0].get('status'),
            PENDING
        )
        
    def test_assign_email_template(self):
        # assign email template
        Template.objects.create(
            title="recruitment",
            message="hello",
            type=SALARY_DECLARATION_LETTER,
            organization=self.organization
        )

        payload = {
            'status': PENDING,
            'organization': self.organization.slug
        }

        response = self.client.get(
            self.salary_declaration_url, payload, format='json'
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            Template.objects.first().type, 'salary_declaration_letter'
        )

    def test_salary_declaration_progress(self):
        # Salary declared form and Status progress
        salary_form = SalaryDeclaration.objects.create(
            job_apply=JobApply.objects.get(job=self.job.id),
            salary="9000",
            candidate_remarks="salary",
            status=PROGRESS
        )
        response = self.client.get(self.salary_declaration_url, format='json')
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(
            SalaryDeclaration.objects.first().status, PROGRESS
        )

        self.assertEqual(
            salary_form.salary, '9000'
        )

        self.assertEqual(
            response.json().get('results')[0].get('no_objection_info')['status'],
            'Not Initialized'
        )

    def test_salary_declaration_complete(self):
        SalaryDeclaration.objects.create(
            job_apply=JobApply.objects.get(job=self.job.id),
            salary="9000",
            candidate_remarks="salary",
            status=PROGRESS
        )
        
        url = reverse(
            "api_v1:recruitment:salary:declaration-complete",
            kwargs={
                'job_slug': self.job.slug,
                'pk': SalaryDeclaration.objects.first().id
            }
        ) + f"?organization={self.organization.slug}&as=hr"

        response = self.client.post(url, format="json")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json().get('status'), "Completed"
        )

    def test_initialize_no_objection(self):
        NoObjectionFactory(
            job_apply=self.job_apply,
            job=self.job,
            responsible_person=self.created_users[0],
            status=COMPLETED
        )
        user = ExternalUser.objects.first().full_name
        url = reverse(
            "api_v1:recruitment:no_objection:no_objection-list",
            kwargs={
                'job_slug': self.job.slug
            }
        ) + f'?organization={self.organization.slug}&as=hr'

        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json().get('results')[0]['title'],
            'No Objection for Salary Declaration of candidate '
            f'{user}'
        )
        
    def test_no_objection_verify(self):
        NoObjectionFactory(
            job_apply=self.job_apply,
            job=self.job,
            responsible_person=self.created_users[0],
            status=COMPLETED
        )
        url = reverse(
            "api_v1:recruitment:no_objection:no_objection-verify",
            kwargs={
                'job_slug': self.job.slug,
                'pk': NoObjection.objects.first().id
            }
        ) + f'?organization={self.organization.slug}&as=hr'

        payload = {
            'status': 'Approved',
            'remarks': 'Verified'
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json().get('status'), COMPLETED)
        self.assertEqual(
            NoObjection.objects.first().status,
            APPROVED
        )

