import datetime
from irhrs.recruitment.models.job import Job
from irhrs.users.models.supervisor_authority import UserSupervisor
from irhrs.core.constants.user import MASTER
from irhrs.core.constants.common import ABILITY, EMPLOYEE, KNOWLEDGE
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.recruitment.constants import (
    ABOVE,
    APPROVED,
    DRAFT,
    HOURLY,
    MORNING,
    PENDING,
)
from irhrs.recruitment.models.common import JobBenefit, Salary
from irhrs.common.models.commons import DocumentCategory, Industry
from irhrs.organization.api.v1.tests.factory import (
    EmploymentJobTitleFactory,
    EmploymentLevelFactory,
    EmploymentStatusFactory,
    OrganizationBranchFactory,
    OrganizationDivisionFactory,
)
from django.urls import reverse
from irhrs.common.api.tests.common import RHRSAPITestCase


class TestRecruitmentJobAPI(RHRSAPITestCase):
    organization_name = "Aayulogic"
    users = [
        ("admin@example.com", "admin", "Male"),
        ("normal@example.com", "normal", "Male"),
    ]

    def setUp(self):
        super().setUp()
        self.url = (
            reverse("api_v1:recruitment:job:job-basic-info-create")
            + f"?as=hr&organization={self.organization.slug}"
        )

        self.get_url = (
            reverse("api_v1:recruitment:job:job-list")
            + f"?organization={self.organization.slug}"
        )

        UserSupervisor.objects.create(
            user=self.created_users[1],
            supervisor=self.admin,
            authority_order=1,
        )
        self.client.force_login(self.admin)

    def patch_url(self, pk):
        return (
            reverse("api_v1:recruitment:job:job-status-change", kwargs={"slug": pk})
            + f"?organization={self.organization.slug}&as=hr"
        )

    # Create Job vacancy
    def test_recruitment_job_vacancy(self):
        title = EmploymentJobTitleFactory(organization=self.organization)
        branch = OrganizationBranchFactory(organization=self.organization)
        division = OrganizationDivisionFactory(organization=self.organization)
        industry = Industry.objects.create(name="Infromation technology")
        employment_status = EmploymentStatusFactory(organization=self.organization)
        employment_level = EmploymentLevelFactory(organization=self.organization)

        offered_salary = Salary.objects.create(
            currency="Dollar", operator=ABOVE, unit=HOURLY
        )
        ksao = KnowledgeSkillAbility.objects.create(
            name="chess",
            description="I can play chess very well",
            ksa_type=KNOWLEDGE,
            organization=self.organization,
        )
        ksao2 = KnowledgeSkillAbility.objects.create(
            name="coding",
            description="I can write code",
            ksa_type=ABILITY,
            organization=self.organization,
        )
        doccat = DocumentCategory.objects.create(name="Doc", associated_with=EMPLOYEE)
        doccat2 = DocumentCategory.objects.create(name="PDF", associated_with=EMPLOYEE)
        benefits1 = JobBenefit.objects.create(
            name="Travelling Expenses", status=APPROVED
        )
        request_by = self.created_users[0]

        payload = {
            "title": title.slug,
            "organization": self.organization.slug,
            "branch": branch.slug,
            "division": division.slug,
            "industry": industry.id,
            "vacancies": 1,
            "deadline": datetime.datetime.now() + datetime.timedelta(days=1),
            "employment_status": employment_status.slug,
            "preferred_shift": MORNING,
            "employment_level": employment_level.slug,
            "location": "Bhaktapur",
            "offered_salary_id": offered_salary.id,
            "salary_visible_to_candidate": True,
            "alternate_description": "Alternative Description",
            "description": "This person is hired as Manager",
            "specification": "Managing the staff and companies operation",
            "is_skill_specific": True,
            "skills": [ksao.slug, ksao2.slug],
            "education_degree": MASTER,
            "education_program": ["BBA", "BIT"],
            "is_education_specific": False,
            "is_document_required": True,
            "document_categories": [doccat.slug],
            "benefits": [benefits1.id],
            "apply_online": True,
            "apply_online_alternative": "Apply Instruction",
            "status": DRAFT,
            "hit_count": 1,
            "posted_at": datetime.datetime.now(),
            "data": {},
            "remarks": True,
            "is_internal": True,
            "requested_by": request_by.id,
            "hiring_info": {},
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json().get("location"), "Bhaktapur")
        self.assertEqual(response.json().get("preferred_shift"), "Morning")
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Job.objects.first().title, title)
        self.assertEqual(Job.objects.first().employment_level, employment_level)

        # Check status of posted vacancy
        payload = {
            "status": PENDING,
        }
        response = self.client.patch(
            self.patch_url(Job.objects.first().slug), payload, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Job.objects.get(status=PENDING))

        # Adding value for additional info
        put_payload = {
            "benefits": [benefits1.id],
            "is_document_required": True,
            "document_categories": [doccat2.id],
            "required_two_wheeler": True,
        }
        put_url = (
            reverse(
                "api_v1:recruitment:job:job-additional-info",
                kwargs={"slug": Job.objects.first().slug},
            )
            + f"?organization={self.organization.slug}&as=hr"
        )
        response = self.client.put(put_url, put_payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Job.objects.first().is_document_required, True)
        self.assertEqual(Job.objects.first().benefits.first().id, benefits1.id)
        self.assertEqual(Job.objects.first().document_categories.first().id, doccat2.id)

        # Checking with wrong input to check validation
        patch_bad_payload = {
            "benefits": [benefits1.id],
            "is_document_required": True,
            "document_categories": [],
            "required_two_wheeler": False,
        }

        response = self.client.put(put_url, patch_bad_payload, format="json")
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.json().get("document_categories")[0], "This field is required."
        )
