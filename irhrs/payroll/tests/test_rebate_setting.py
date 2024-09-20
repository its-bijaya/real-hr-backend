from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.payroll.constants import YEARLY, LIFE_INSURANCE, HEALTH_INSURANCE
from irhrs.payroll.models import RebateSetting
from irhrs.payroll.tests.factory import HeadingFactory


class TestRebateSetting(RHRSAPITestCase):
    organization_name = 'Google'
    users = (
        ('hr@email.com', 'password', 'Female'),
        ('normal@email.com', 'password', 'Female'),
    )

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def url(self, pk=None):
        if pk:
            return reverse(
                'api_v1:payroll:rebate-setting-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'pk': pk
                }
            )

        return reverse(
                'api_v1:payroll:rebate-setting-list',
                kwargs={
                    'organization_slug': self.organization.slug
                }
            )

    @property
    def payload(self):
        return {
            "title": LIFE_INSURANCE,
            "amount": 25000,
            "duration_type": YEARLY,
        }

    def test_rebate_setting(self):
        # create rebate setting
        response = self.client.post(self.url(), data=self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # recreate same rebate setting; error expected
        response = self.client.post(self.url(), data=self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get('non_field_errors')[0],
            'This title is already used.'
        )

        # update rebate setting
        pk = RebateSetting.objects.first().id
        data = self.payload
        data["title"] = HEALTH_INSURANCE
        response = self.client.patch(self.url(pk=pk), data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # create heading
        HeadingFactory(
            organization=self.organization,
            name=HEALTH_INSURANCE,
            rules='[{"rule":"__USER_VOLUNTARY_REBATE__(\'Health Insurance\')","rule_validator":{"numberOnly":false}}]'
        )

        # update rebate setting after using rebate in heading; error expected
        data = self.payload
        data["title"] = LIFE_INSURANCE
        response = self.client.patch(self.url(pk=pk), data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get('title'), 'This rebate is already used in payroll heading.')

        # delete rebate setting after using rebate in heading; error expected
        response = self.client.delete(self.url(pk=pk))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get('non_field_errors')[0],
            'This rebate is already used in payroll heading.'
        )

        # create new rebate setting
        response = self.client.post(self.url(), data=self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # delete newly created rebate setting; expect successful message
        pk = RebateSetting.objects.last().id
        response = self.client.delete(self.url(pk=pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)




