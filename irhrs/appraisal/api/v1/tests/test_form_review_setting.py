from copy import deepcopy

from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.appraisal.api.v1.tests.factory import SubPerformanceAppraisalSlotFactory
from irhrs.appraisal.constants import SELF_APPRAISAL, SUBORDINATE_APPRAISAL, PEER_TO_PEER_FEEDBACK, \
    SUPERVISOR_APPRAISAL
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
            "viewable_appraisal_submitted_form_type": [
                SELF_APPRAISAL, SUBORDINATE_APPRAISAL,
                PEER_TO_PEER_FEEDBACK, SUPERVISOR_APPRAISAL
            ],
            "can_hr_download_form": True
        }

    def url(self, **kwargs):
        if kwargs:
            return reverse(
                'api_v1:appraisal:form-review-setting-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                    **kwargs
                }
            )
        else:
            return reverse(
                'api_v1:appraisal:form-review-setting-list',
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

        # duplicate appraisal type
        data['viewable_appraisal_submitted_form_type'].pop(-1)
        data['viewable_appraisal_submitted_form_type'].append(SELF_APPRAISAL)
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertListEqual(
            response.json().get('viewable_appraisal_submitted_form_type'),
            ["Duplicate appraisal type submitted."]
        )

    def test_list(self):
        _ = self.do_create(data=self.data)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
