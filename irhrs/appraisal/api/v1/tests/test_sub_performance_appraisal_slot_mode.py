from copy import deepcopy

from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.appraisal.api.v1.tests.factory import SubPerformanceAppraisalSlotFactory
from irhrs.appraisal.constants import APPRAISAL_TYPE, SELF_APPRAISAL
from irhrs.common.api.tests.common import RHRSAPITestCase

User = get_user_model()


class TestSubPerformanceAppraisalSlotMode(RHRSAPITestCase):
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
        return [
            {
                'appraisal_type': mode[0],
                'weightage': 25,
            } for mode in APPRAISAL_TYPE[:-1]
        ]

    def url(self, **kwargs):
        if kwargs:
            return reverse(
                'api_v1:appraisal:performance-appraisal-mode-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                    **kwargs
                }
            )
        else:
            return reverse(
                'api_v1:appraisal:performance-appraisal-mode-list',
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

        # duplicate appraisal type for same slot
        duplicate_data = deepcopy(data)
        duplicate_data.pop(-1)
        duplicate_data.append(
            {
                'appraisal_type': SELF_APPRAISAL,
                'weightage': 25,
            }
        )
        response = self.do_create(duplicate_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertListEqual(
            response.json().get('appraisal_type'),
            ['Duplicate appraisal type supplied.']
        )

        # total weightage more than 100
        data[-1].update({
            'weightage': 50
        })
        response = self.do_create(data)
        self.assertListEqual(
            response.json().get('weightage'),
            ['Total weightage must be 100.']
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list(self):
        _ = self.do_create(data=self.data)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 4)
