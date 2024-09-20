from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.core import mail
from rest_framework import status

from irhrs.core.utils.common import get_today
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.questionnaire.models.questionnaire import Question
from irhrs.assessment.models import AssessmentSet, UserAssessment
from irhrs.assessment.models.helpers import IN_PROGRESS, PENDING
from irhrs.assessment.api.v1.tests.factory import (
    AssessmentSectionFactory,
    AssessmentSetFactory,
    UserAssessmentFactory
)


class TestAssessmentCreate(RHRSTestCaseWithExperience):
    users = [("test@example.com", "secretThingIsHere", "Male", "Manager"),
             ("testone@example.com", "secretThingIsHere", "Female", "Programmer")]
    organization_name = "Organization"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123

    def setUp(self) -> None:
        super().setUp()

    @property
    def create_url(self):
        url = reverse(
            'api_v1:assessment-list',
            kwargs={'organization_slug': self.organization.slug}
        )
        return url

    def assign_url(self, kwargs):
        url = reverse(
            'api_v1:assessment-assign-assessment',
            kwargs=kwargs
        )
        return url

    @property
    def assessment_set_create_data(self):
        payload = {
            "assessment_sections": [],
            "assessment_set": {
                "duration": 600,
                "marginal_percentage": "30",
                "description": "Asses desc",
                "title": "Test Assessment"
            }
        }
        return payload


    def test_create_assessment_set(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.create_url,
            data=self.assessment_set_create_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            AssessmentSet.objects.filter(
                title=self.assessment_set_create_data["assessment_set"]["title"]
            ).exists()
        )



    @property
    def assessment_set_assign_data(self):
        tomorrow_with_time = get_today(with_time=True) + timedelta(days=1)
        payload = {
            "expiry_date": tomorrow_with_time,
            "users": [
              self.created_users[1].id
            ]
        }
        return payload

    def test_assign_assessment(self):
        self.client.force_login(self.admin)
        assessment_set = AssessmentSetFactory(organization=self.organization)
        kwargs = {
            'organization_slug': self.organization.slug,
            'pk': assessment_set.id
        }
        assign_url = self.assign_url(kwargs=kwargs) + "?as=hr"
        response = self.client.post(
            assign_url,
            data=self.assessment_set_assign_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            UserAssessment.objects.filter(
                user=self.created_users[1],
                assessment_set=assessment_set.id
            ).exists()
        )

    def test_assign_assignment_email(self):
        self.client.force_login(self.admin)
        assessment_set = AssessmentSetFactory(organization=self.organization)
        kwargs = {
            'organization_slug': self.organization.slug,
            'pk': assessment_set.id
        }
        assign_url = self.assign_url(kwargs=kwargs) + "?as=hr"

        def can_send_email(user, email_type):
            if user == self.created_users[1]:
                return True
            else:
                return False

        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.post(
                assign_url,
                data=self.assessment_set_assign_data,
                format="json"
            )
        self.assertEqual(len(mail.outbox), 1)
        mail_instance = mail.outbox[0]

        self.assertEqual(mail_instance.to, [self.created_users[1].email])
        self.assertEqual(mail_instance.subject, "New assessments were assigned.")

    @property
    def assessment_complete_data(self):
        payload = {
            "remarks": "Completed."
        }
        return payload

    def submit_assesment_url(self, kwargs):
        url = reverse(
            'api_v1:take-assessment-exit-assessment',
            kwargs=kwargs
        )
        return url

    def test_complete_assignment(self):
        user_assessment = UserAssessmentFactory(
            assessment_set__organization=self.organization,
            status=IN_PROGRESS,
            user=self.created_users[1]
        )
        kwargs = {
            'organization_slug': self.organization.slug,
            'assessment_id': user_assessment.assessment_set.id
        }
        submit_assessment_url = self.submit_assesment_url(kwargs=kwargs)

        def can_send_email(user, email_type):
            if user == self.admin:
                return True
            else:
                return False

        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            self.client.force_login(self.created_users[1])
            response = self.client.post(
                submit_assessment_url,
                data=self.assessment_complete_data,
                format="json",
            )
        self.assertEqual(len(mail.outbox), 1)
        mail_instance = mail.outbox[0]

        self.assertEqual(mail_instance.to, [self.admin.email])
        self.assertEqual(
            mail_instance.subject,
            f"Assessment completed by {self.created_users[1].full_name}"
        )

        self.assertEqual(
            mail_instance.body,
            (
                f"'{user_assessment.assessment_set.title}' assigned to"
                f" '{user_assessment.user.full_name}' has been completed."
            )
        )

    def assessment_unassign_url(self, kwargs):
        url = reverse(
            'api_v1:assessment-remove-assigned-user',
            kwargs=kwargs
        )
        return url

    def test_unassign_assessment(self):
        user_assessment = UserAssessmentFactory(
            assessment_set__organization=self.organization,
            status=PENDING,
            user=self.created_users[1]
        )
        kwargs = {
            'organization_slug': self.organization.slug,
            'assigned_user_id': user_assessment.id,
            'pk': user_assessment.assessment_set.id
        }
        assessment_unassign_url = self.assessment_unassign_url(kwargs=kwargs) + '?as=hr'

        def can_send_email(user, email_type):
            return True

        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            self.client.force_login(self.admin)
            response = self.client.delete(
                assessment_unassign_url,
                data=self.assessment_complete_data,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(mail.outbox), 1)
        mail_instance = mail.outbox[0]

        self.assertEqual(mail_instance.to, [self.created_users[1].email])
        self.assertEqual(
            mail_instance.subject,
            "Assessment was unassigned."
        )

        self.assertEqual(
            mail_instance.body,
            (
                f"{user_assessment.assessment_set.title} assessment which "
                f"was previously assigned to you has been unassigned."
            )
        )
