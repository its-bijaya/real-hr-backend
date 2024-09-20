from copy import deepcopy

from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.appraisal.api.v1.tests.factory import SubPerformanceAppraisalSlotFactory
from irhrs.common.api.tests.common import RHRSAPITestCase

User = get_user_model()


class TestFormDesign(RHRSAPITestCase):
    organization_name = "Necrophos"
    users = [
        ('admin@gmail.com', 'hellonepal', 'Male'),
        ('luffy@onepiece.com', 'passwordissecret', 'Female'),
        ('guest@admin.com', 'guestnotallowed', 'Other')
    ]
    fake = Factory.create()

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.users = User.objects.all()
        self.performance_appraisal_slot = SubPerformanceAppraisalSlotFactory()

    @property
    def data(self):
        return {
            "appraisal_type": "Self Appraisal",
            "instruction_for_evaluator": "asdasd",
            "include_kra": False,
            "caption_for_kra": "",
            "include_ksa": True,
            "caption_for_ksa": "This is test.",
            "generic_question_set": None,
            "add_feedback": True,
            "answer_types": [
                {
                    "question_type": "ksa",
                    "answer_type": "long-text",
                    "description": "Asdf",
                    "is_mandatory": True
                }
            ]
        }

    def url(self, **kwargs):
        if kwargs:
            return reverse(
                'api_v1:appraisal:performance-appraisal-form-design-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                    **kwargs
                }
            )
        else:
            return reverse(
                'api_v1:appraisal:performance-appraisal-form-design-list',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                    **kwargs
                }
            )

    def do_create(self, data):
        return self.client.post(self.url(), data=data, format='json')

    def test_create(self):
        data = deepcopy(self.data)
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list(self):
        _ = self.do_create(data=self.data)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
