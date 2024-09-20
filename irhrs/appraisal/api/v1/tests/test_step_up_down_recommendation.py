from copy import deepcopy

from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.appraisal.api.v1.tests.factory import SubPerformanceAppraisalSlotFactory
from irhrs.common.api.tests.common import RHRSAPITestCase

User = get_user_model()


class TestDeadlineExceedScoreDeductionCondition(RHRSAPITestCase):
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
           "recommendation_criteria": [
              {
                 "score_acquired_from": 40,
                 "score_acquired_to": 50,
                 "change_step_by": 1
              },
              {
                 "score_acquired_from": 51,
                 "score_acquired_to": 75,
                 "change_step_by": 2
              }
           ]
        }

    def url(self, **kwargs):
        if kwargs:
            return reverse(
                'api_v1:appraisal:step-up-down-recommendation-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                    **kwargs
                }
            )
        else:
            return reverse(
                'api_v1:appraisal:step-up-down-recommendation-list',
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

        # check for overlapped data
        data.get("recommendation_criteria")[0].update({
            'score_acquired_from': 40,
            'score_acquired_to': 55
        })
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # check for invalid data
        data.get("recommendation_criteria")[0].update({
            'score_acquired_from': 50,
            'score_acquired_to': 40
        })
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list(self):
        _ = self.do_create(data=self.data)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
