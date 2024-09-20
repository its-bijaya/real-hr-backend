import datetime
import faker

from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.common.models import Industry
from irhrs.core.constants.common import KNOWLEDGE, ABILITY, EMPLOYEE
from irhrs.core.constants.user import MASTER
from irhrs.organization.api.v1.tests.factory import (
    EmploymentJobTitleFactory,
    OrganizationBranchFactory,
    OrganizationDivisionFactory,
    EmploymentStatusFactory,
    EmploymentLevelFactory,
)
from irhrs.recruitment.api.v1.tests.factory import JobFactory
from irhrs.recruitment.constants import (
    ABOVE,
    HOURLY,
    APPROVED,
    MORNING,
    DRAFT,
    PUBLISHED,
)
from irhrs.recruitment.models import (
    Salary,
    KnowledgeSkillAbility,
    DocumentCategory,
    JobBenefit,
    Job,
)
from irhrs.users.models import UserSupervisor


_faker = faker.Faker()


class TestMixin(RHRSAPITestCase):
    organization_name = "Aayu bank"
    users = [
        ("admin@example.com", "admin", "Male"),
        ("normal@example.com", "normal", "Male"),
        ("supervisor@example.com", "normal", "Male"),
    ]

    def setUp(self):
        super().setUp()
        UserSupervisor.objects.create(
            user=self.created_users[1],
            supervisor=self.created_users[2],
            authority_order=1,
            approve=True,
            deny=True,
            forward=True,
        )

    def payload(self, is_internal=True):
        # prepare data for the payload to create job vacancy
        title = EmploymentJobTitleFactory(organization=self.organization)
        branch = OrganizationBranchFactory(organization=self.organization)
        division = OrganizationDivisionFactory(organization=self.organization)
        industry = Industry.objects.create(name=_faker.name())
        employment_status = EmploymentStatusFactory(organization=self.organization)
        employment_level = EmploymentLevelFactory(organization=self.organization)

        offered_salary = Salary.objects.create(
            currency="Dollar", operator=ABOVE, unit=HOURLY
        )
        ksao = KnowledgeSkillAbility.objects.create(
            name=_faker.name(),
            description="I can play chess very well",
            ksa_type=KNOWLEDGE,
            organization=self.organization,
        )
        ksao2 = KnowledgeSkillAbility.objects.create(
            name=_faker.name(),
            description="I can write code",
            ksa_type=ABILITY,
            organization=self.organization,
        )
        doccat = DocumentCategory.objects.create(
            name=_faker.name(), associated_with=EMPLOYEE
        )
        benefits1 = JobBenefit.objects.create(name=_faker.name(), status=APPROVED)
        request_by = self.created_users[0]
        # return actual payload
        return {
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
            "is_internal": is_internal,
            "requested_by": request_by.id,
            "hiring_info": {},
        }


class TestJobVacancy(TestMixin):
    def test_create_job_vacancy(self):
        url = (
            reverse("api_v1:recruitment:job:job-basic-info-create")
            + f"?organization={self.organization.slug}"
            + "&as=hr"
        )

        self.client.force_login(self.admin)
        response = self.client.post(
            url,
            # public vacancy since `is_internal` is False
            self.payload(False),
            format="json",
        )

        response = self.client.post(
            url,
            # public vacancy since `is_internal` is True
            self.payload(True),
            format="json",
        )

        Job.objects.all().update(status=PUBLISHED)

        self.client.logout()

        job_vacancy_list_page = reverse("api_v1:recruitment:job:search-list")
        response = self.client.get(job_vacancy_list_page)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("count"), 1)

        self.assertFalse(response.json().get("results")[0].get("is_internal"))

        self.client.force_login(self.created_users[1])

        response = self.client.get(job_vacancy_list_page)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json().get("count"), 2)

        self.assertTrue(response.json().get("results")[0].get("is_internal"))
        self.assertFalse(response.json().get("results")[1].get("is_internal"))


class TestRecruitmentJobVacany(TestMixin):
    @property
    def job(self):
        return JobFactory(
            location="Kathmandu",
            organization=self.organization,
            status=PUBLISHED,
            created_by=self.created_users[2],
        )

    @property
    def basic_info_url(self):
        return (
            reverse("api_v1:recruitment:job:job-basic-info-create")
            + f"?organization={self.organization.slug}"
        )

    def test_create_job_vacancy_by_hr_or_supervisor(self):
        self.client.force_login(self.admin)

        hr_url = self.basic_info_url + "&as=hr"

        self.assertFalse(Job.objects.all())
        job_data = self.payload(True)
        hr_response = self.client.post(hr_url, job_data, format="json")
        self.assertEqual(hr_response.status_code, 201)

        self.assertTrue(Job.objects.all())
        self.assertEqual(job_data.get("title"), Job.objects.last().title.slug)

        self.client.force_login(self.created_users[2])
        supervisor_url = self.basic_info_url + "&as=supervisor"
        supervisor_response = self.client.post(
            supervisor_url, self.payload(True), format="json"
        )
        self.assertEqual(supervisor_response.status_code, 201)

    def job_vacancy_update_url(self, job_slug):
        return (
            reverse(
                "api_v1:recruitment:job:job-basic-info-update",
                kwargs={"slug": job_slug},
            )
            + f"?organization={self.organization.slug}"
        )

    def test_update_job_vacancy_by_hr(self):
        self.client.force_login(self.admin)

        hr_url = self.job_vacancy_update_url(self.job.slug) + "&as=hr"
        hr_response = self.client.put(
            hr_url, self.payload(is_internal=True), format="json"
        )

        self.assertEqual(hr_response.status_code, 200, hr_response.data)
        self.assertTrue(Job.objects.filter(location="Bhaktapur"))

    def test_update_job_vacancy_by_supervisor(self):
        self.client.force_login(self.created_users[2])
        job = JobFactory(
            location="Kathmandu",
            organization=self.organization,
            created_by=self.created_users[2],
            status=DRAFT,
        )
        self.client.force_login(self.created_users[2])
        supervisor_url = self.job_vacancy_update_url(job.slug) + "&as=supervisor"
        supervisor_response = self.client.put(
            supervisor_url, self.payload(True), format="json"
        )

        self.assertEqual(supervisor_response.status_code, 200, supervisor_response.data)
        self.assertTrue(Job.objects.filter(location="Bhaktapur"))

    def test_supervisor_having_no_subordinates(self):
        self.client.force_login(self.created_users[2])

        UserSupervisor.objects.all().delete()
        update_url = self.job_vacancy_update_url(self.job.slug) + "&as=supervisor"
        response = self.client.put(update_url, self.payload(True), format="json")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json().get("detail"),
            "You do not have permission to perform this action.",
        )

    def test_cannot_create_or_update_job_vacancy_by_user(self):
        self.client.force_login(self.created_users[1])

        create_url = self.basic_info_url
        response = self.client.post(create_url, self.payload(True), format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json().get("detail"),
            "You do not have permission to perform this action.",
        )

        update_url = self.job_vacancy_update_url(self.job.slug)
        response = self.client.put(update_url, self.payload(True), format="json")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get("detail"), "Not found.")
