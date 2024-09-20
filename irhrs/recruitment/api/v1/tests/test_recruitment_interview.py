from django.urls import reverse
from rest_framework import status

from irhrs.recruitment.api.v1.tests.factory import JobApplyFactory, \
    InterViewAnswerFactory, InterviewFactory
from irhrs.recruitment.api.v1.tests.test_recruitment_mixin import TestRecruitmentMixin
from irhrs.recruitment.constants import COMPLETED
from irhrs.recruitment.models import Interview, InterViewAnswer


class TestInterview(TestRecruitmentMixin):

    def setUp(self):
        super().setUp()
        self.job_apply = JobApplyFactory(job=self.job)
        self.interview = InterviewFactory(job_apply=self.job_apply)
        self.interview_answer1 = InterViewAnswerFactory(
            interview=self.interview,
            internal_interviewer=self.admin,
            conflict_of_interest=False,
            status=COMPLETED,
            data=self.dummy_data()
        )
        self.interview_answer1 = InterViewAnswerFactory(
            interview=self.interview,
            internal_interviewer=self.created_users[1],
            conflict_of_interest=True,
            status=COMPLETED,
            data=self.dummy_data(conflict=True)
        )

    @property
    def url(self):
        return reverse(
            'api_v1:recruitment:interview:interview-list',
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

    def test_interview_list(self):
        pending_url = self.url + f"?status=Pending&organization={self.organization.slug}&as=hr"
        response = self.client.get(pending_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('results')[0].get("id"),
            self.interview.id
        )

    def test_interview_answer_list(self):
        url = reverse(
            'api_v1:recruitment:interview:interview-complete',
            kwargs={
                'job_slug': self.job.slug,
                'pk': self.interview.id
            }
        )
        # for interview answer complete API we do not require any payload.
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
            Interview.objects.first().score,
            100
        )
        InterViewAnswer.objects.all().update(conflict_of_interest=False)

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
            Interview.objects.first().score,
            50
        )
