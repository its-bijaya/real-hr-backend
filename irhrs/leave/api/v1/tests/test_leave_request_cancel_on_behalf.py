from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today, get_yesterday
from irhrs.leave.api.v1.tests.factory import LeaveAccountFactory, LeaveRequestFactory
from irhrs.leave.constants.model_constants import APPROVED
from irhrs.leave.models import LeaveRequest


class TestLeaveRequestCancelOnBehalf(RHRSAPITestCase):
    organization_name = 'Leave Test'
    users = [
        ('hr@email.com', 'password', 'Female'),
        ('usr@email.com', 'password', 'Male'),
        ('user@email.com', 'password', 'Male'),
    ]

    def setUp(self):
        super().setUp()
        self.hr, self.usr, self.user = self.created_users
        account = LeaveAccountFactory(user=self.created_users[1])
        self.request = LeaveRequestFactory(
            user=self.usr,
            recipient=self.user,
            leave_rule=account.rule,
            leave_account=account,
            start=get_yesterday(with_time=True),
            end=get_today(with_time=True),
            balance=1,
            status=APPROVED
        )

    def test_cancel_on_behalf_for_hr(self):
        self.client.force_login(self.hr)
        response = self.client.delete(
            self.url + '?as=hr',
            data={'remarks': 'HR.'},
            format='json'
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK
        )
        self.assertTrue(self.is_deleted)

    def test_cancel_on_behalf_without_as_hr(self):
        self.client.force_login(self.hr)
        response = self.client.delete(
            self.url,
            data={'remarks': 'HR.'},
            format='json'
        )
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )
        self.assertFalse(self.is_deleted)

    def test_cancel_on_behalf_for_normal_user(self):
        self.client.force_login(self.user)
        response = self.client.delete(
            self.url + '?as=hr',
            data={'remarks': 'HR.'},
            format='json'
        )
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN
        )
        self.assertFalse(self.is_deleted)

    @property
    def url(self):
        return reverse(
            'api_v1:leave:leave-request-detail',
            kwargs={
                'pk': self.request.id,
                'organization_slug': self.organization.slug
            }
        )

    @property
    def is_deleted(self):
        return LeaveRequest.objects.include_deleted().filter(
            id=self.request.id
        ).values_list('is_deleted', flat=True).first()
