from datetime import timedelta
from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import (
    EmploymentLevelFactory,
    OrganizationBranchFactory
)
from irhrs.organization.models.employment import EmploymentJobTitle, EmploymentStatus
from irhrs.users.models.experience import UserExperience


class TestUserExperienceHistory(RHRSAPITestCase):
    users = [("admin@email.com", "password", "male")]
    organization_name = "organization"

    def setUp(self):
        super().setUp()

        developer = EmploymentJobTitle.objects.create(
            organization=self.organization, title="Developer"
        )
        project_manager = EmploymentJobTitle.objects.create(
            organization=self.organization, title="Project Manager"
        )

        assistant = EmploymentLevelFactory(
            organization=self.organization, title="assistant"
        )
        executive = EmploymentLevelFactory(
            organization=self.organization, title="executive"
        )

        branch1 = OrganizationBranchFactory(
            organization=self.organization, name="Branch 1"
        )
        branch2 = OrganizationBranchFactory(
            organization=self.organization, name="Branch 2"
        )

        probation = EmploymentStatus.objects.create(
            organization=self.organization, title="Probation"
        )
        permanent = EmploymentStatus.objects.create(
            organization=self.organization, title="Permanent"
        )

        self.user_experience1 = UserExperience.objects.create(
            user=self.admin,
            organization=self.organization,
            job_title=developer,
            branch=branch1,
            employee_level=assistant,
            employment_status=probation,
            start_date=get_today() - timedelta(days=60), 
            is_current=True,
            current_step=1,
        )
        self.user_experience2 = UserExperience.objects.create(
            user=self.admin,
            organization=self.organization,
            job_title=project_manager,
            branch=branch2,
            employee_level=executive,
            employment_status=permanent,
            start_date=get_today(),
            is_current=True,
            current_step=2
        )

    @property
    def url(self):
        return reverse(
            "api_v1:users:experience-history-list", kwargs={"user_id": self.admin.id}
        )

    def test_employment_experience(self):
        """
        the order of attributes for text is:
        1. job_title
        2. employment_status
        3. branch
        4. employee 
        5. current_step
        """
        self.client.force_login(self.admin)

        expected_text = ['To Project Manager From Developer', 'As Developer']
        self.check_response_text(expected_text)

        self.user_experience2.job_title = self.user_experience1.job_title
        self.user_experience2.save()
        expected_text = ['To Permanent From Probation', 'As Developer']
        self.check_response_text(expected_text)

        self.user_experience2.employment_status = self.user_experience1.employment_status
        self.user_experience2.save()

        expected_text = ['To Branch 2 From Branch 1', 'As Developer']
        self.check_response_text(expected_text)

        self.user_experience2.branch = self.user_experience1.branch
        self.user_experience2.save()
        expected_text = ['To executive From assistant', 'As Developer']
        self.check_response_text(expected_text)

        self.user_experience2.employee_level = self.user_experience1.employee_level
        self.user_experience2.save()
        expected_text = ['To Step 2 From Step 1', 'As Developer']
        self.check_response_text(expected_text)

        self.user_experience2.current_step = self.user_experience1.current_step
        self.user_experience2.save()
        expected_text = [None, 'As Developer']
        self.check_response_text(expected_text)

    def check_response_text(self, expected_text):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        calculated_text = [history["text"] for history in results]
        self.assertEqual(calculated_text, expected_text)
