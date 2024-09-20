from django.urls import reverse
from rest_framework import status


from irhrs.organization.api.v1.tests.factory import (
    EmploymentJobTitleFactory,
    EmploymentLevelFactory,
    EmploymentStatusFactory,
    KnowledgeSkillAbilityFactory,
)
from irhrs.recruitment.models.job import Job
from irhrs.recruitment.models.common import Template
from irhrs.recruitment.constants import (
    APPLIED,
    COMPLETED,
    EXTERNAL_USER_LETTER,
    INTERVIEWED,
    MORNING,
    PRE_SCREENING,
    REJECTED,
    SCREENED,
    SELECTED,
)
from irhrs.recruitment.models.question import QuestionSet
from irhrs.recruitment.models import PreScreening
from irhrs.organization.models import organization
from irhrs.recruitment.api.v1.tests.factory import JobApplyFactory, JobFactory
from irhrs.recruitment.constants import PENDING
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.users.models.supervisor_authority import UserSupervisor
from irhrs.recruitment.models.job_apply import JobApply, JobApplyStage, Interview


class TestRecruitmentPreScreeningAPI(RHRSAPITestCase):
    organization_name = "Aayulogic"
    users = [
        ("admin@example.com", "admin", "Male"),
        ("normal@example.com", "normal", "Male"),
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
            hiring_info={"pre_screening_letter": None},
            specification="Assistant",
            is_skill_specific=True,
            education_degree="Bachlor",
            education_program=None,
        )

        self.url = reverse(
            "api_v1:recruitment:pre_screening-list", kwargs={"job_slug": self.job.slug}
        )

        self.initialize_url = (
            reverse(
                "api_v1:recruitment:pre_screening-initialize",
                kwargs={"job_slug": self.job.slug},
            )
            + f"?organization={self.organization.slug}&as=hr"
        )

        self.screened_url_completed = reverse(
            "api_v1:recruitment:pre_screening-list", kwargs={"job_slug": self.job.slug}
        )

    def screened_url(self, pk):
        return reverse(
            "api_v1:recruitment:pre_screening-complete",
            kwargs={"job_slug": self.job.slug, "pk": pk},
        )

    def test_recruitment_pre_screening(self):
        self.client.force_login(self.admin)
        self.job.stages = [APPLIED, INTERVIEWED, SELECTED, REJECTED]
        self.job.save()
        self.job.skills.add(
            KnowledgeSkillAbilityFactory(organization=self.organization)
        )
        job_apply = JobApplyFactory(job=self.job)

        question_set1 = QuestionSet.objects.create(
            name="Question 1", form_type=PRE_SCREENING, is_archived=False
        )
        template1 = Template.objects.create(
            title="Mail_tempalte",
            message="This is the template for writing Mail",
            type=EXTERNAL_USER_LETTER,
            organization=self.organization,
        )

        payload = {
            "responsible_person": self.created_users[1].id,
            "job_apply": job_apply.id,
            "score": 50.0,
            "question_set": question_set1.id,
            "email_template": template1.slug,
        }

        # 1. Should receive candidate in pending tab after initializing the prescreening process
        response = self.client.post(
            self.initialize_url,
            data={"score": 50},
            format="json",
        )
        self.assertTrue(Interview.objects.filter(status=PENDING).exists())
