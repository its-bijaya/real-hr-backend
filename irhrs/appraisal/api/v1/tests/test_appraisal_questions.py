import base64
from os import path
from django.contrib.auth import get_user_model
from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.questionnaire.api.v1.tests.factory import QuestionFactory
from irhrs.appraisal.api.v1.tests.factory import PerformanceAppraisalQuestionSetFactory
from irhrs.appraisal.models.question_set import (
    PerformanceAppraisalQuestionSection,
    PerformanceAppraisalQuestionSet
)

USER = get_user_model()


class TestForms(RHRSAPITestCase):
    users = [
        ("hr@email.com", "secret", "Male"),
        ("engineer@email.com", "secret", "Male"),
        ("accountant@email.com", "secret", "Male"),
        ("clerk@email.com", "secret", "Male"),
        ("luffy@email.com", "secret", "Male"),
    ]
    organization_name = "Google Inc."

    def test_form_question_set_creation_works(self):
        QuestionFactory(category__organization=self.organization)
        QuestionFactory()
        payload = {"name": "set A", "description": "This is set A", "sections": []}
        url = reverse(
            "api_v1:appraisal:appraisal-question-set-list",
            kwargs={"organization_slug": self.organization.slug},
        )
        self.client.force_login(self.admin)
        res = self.client.post(url, data=payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(
            PerformanceAppraisalQuestionSet.objects.filter(name=res.json()["name"]).exists()
        )

    def test_form_question_section_creation_works(self):
        question_set = PerformanceAppraisalQuestionSetFactory()
        payload = {
            "title": "dasd",
            "description": "sad",
            "total_weightage": 0,
            "marginal_weightage": 0,
        }

        url = reverse(
            "api_v1:appraisal:appraisal-question-section-list",
            kwargs={
                "organization_slug": self.organization.slug,
                "question_set": question_set.id,
            },
        ) + "?as=hr"
        self.client.force_login(self.admin)
        res = self.client.post(url, data=payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(
            PerformanceAppraisalQuestionSection.objects.filter(title=res.json()["title"]).exists()
        )

