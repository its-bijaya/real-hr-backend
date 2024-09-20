from copy import deepcopy

from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.appraisal.api.v1.tests.factory import SubPerformanceAppraisalSlotFactory
from irhrs.common.api.tests.common import RHRSAPITestCase

User = get_user_model()


class TestScoreAndScalingSetting(RHRSAPITestCase):
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
                "name": "Outstanding",
                "scale": 1,
                "score": 10
            },
            {
                "name": "Good",
                "scale": 2,
                "score": 5
            },
            {
                "name": "Bad",
                "scale": 3,
                "score": 1
            }
        ]

    def url(self, **kwargs):
        if kwargs:
            return reverse(
                'api_v1:appraisal:score-and-scaling-setting-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                    **kwargs
                }
            )
        else:
            return reverse(
                'api_v1:appraisal:score-and-scaling-setting-list',
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

        # test for duplicate name
        data.append({
            "name": "Outstanding",
            "scale": 1,
            "score": 20
        })
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test for duplicate score
        data.pop(-1)
        data.append({
            "name": "Outstanding 1",
            "scale": 1,
            "score": 10
        })
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list(self):
        _ = self.do_create(data=self.data)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 3)
