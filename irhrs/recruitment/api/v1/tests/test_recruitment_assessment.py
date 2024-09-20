from django.urls import reverse
from rest_framework import status

from irhrs.recruitment.api.v1.tests.factory import AssessmentFactory, JobApplyFactory, \
    AssessmentAnswerFactory
from irhrs.recruitment.api.v1.tests.test_recruitment_mixin import TestRecruitmentMixin
from irhrs.recruitment.constants import COMPLETED
from irhrs.recruitment.models import Assessment, AssessmentAnswer


class TestAssessment(TestRecruitmentMixin):

    def setUp(self):
        super().setUp()
        self.job_apply = JobApplyFactory(job=self.job)
        self.assessment = AssessmentFactory(job_apply=self.job_apply)
        self.assessment_answer1 = AssessmentAnswerFactory(
            assessment=self.assessment,
            internal_assessment_verifier=self.admin,
            conflict_of_interest=False,
            status=COMPLETED,
            data=self.dummy_data()
        )
        self.assessment_answer1 = AssessmentAnswerFactory(
            assessment=self.assessment,
            internal_assessment_verifier=self.created_users[1],
            conflict_of_interest=True,
            status=COMPLETED,
            data=self.dummy_data(conflict=True)
        )

    @property
    def url(self):
        return reverse(
            'api_v1:recruitment:assessment-list',
            kwargs={
                'job_slug': self.job.slug
            }
        )

    @staticmethod
    def dummy_data(conflict=False):
        score = 0
        percentage = 0
        if not conflict:
            score = 3
            percentage = 100
        return {
            'percentage': percentage,
            'description': '',
            'given_score': score,
            'total_score': 3,
            'is_recommended': 'yes',
            'overall_remarks': '<p>i know him<br></p>'
        }

    def test_assessment_list(self):
        pending_url = self.url + f"?status=Pending&organization={self.organization.slug}&as=hr"
        response = self.client.get(pending_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('results')[0].get("id"),
            self.assessment.id
        )

    def test_assessment_answer_list(self):
        url = reverse(
            'api_v1:recruitment:assessment-complete',
            kwargs={
                'job_slug': self.job.slug,
                'pk': self.assessment.id
            }
        )
        # for assessment answer complete API we do not require any payload.
        response = self.client.post(url, data={}, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.json().get('status'),
            'Completed'
        )
        self.assertEqual(
            Assessment.objects.first().score,
            100
        )
        AssessmentAnswer.objects.all().update(conflict_of_interest=False)

        response = self.client.post(url, data={}, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('status'),
            'Completed'
        )
        self.assertEqual(
            Assessment.objects.first().score,
            50
        )
