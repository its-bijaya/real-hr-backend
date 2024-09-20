from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, LeaveAccountFactory
from irhrs.leave.constants.model_constants import ASSIGNED
from irhrs.leave.models import LeaveAccountHistory
from irhrs.users.models import UserSupervisor


class TestUserLeaveAccountHistory(RHRSAPITestCase):
    organization_name = 'Google'
    users = [
        ('admin@email.com', 'password', 'Male'),
        ('normal@email.com', 'password', 'Male'),
        ('supervisorone@email.com', 'password', 'Male'),
        ('supervisortwo@email.com', 'password', 'Male'),
        ('supervisorthree@email.com', 'password', 'Male'),
    ]

    def setUp(self):
        super().setUp()
        self.master_settings = MasterSettingFactory(
            organization=self.organization,
            half_shift_leave=True,
            effective_from=get_today() - timezone.timedelta(days=30),
            effective_till=get_today() + timezone.timedelta(days=30)
        )
        self.leave_type = LeaveTypeFactory(master_setting=self.master_settings)
        self.rule = LeaveRuleFactory(leave_type=self.leave_type)
        self.account = LeaveAccountFactory(user=self.created_users[1], rule=self.rule)
        UserSupervisor.objects.bulk_create([
            UserSupervisor(
                user=self.created_users[1],
                supervisor=self.created_users[2],
                authority_order=1
            ),
            UserSupervisor(
                user=self.created_users[1],
                supervisor=self.created_users[3],
                authority_order=2
            ),
            UserSupervisor(
                user=self.created_users[1],
                supervisor=self.created_users[4],
                authority_order=3
            )
        ])

    def validate_response(self, response):
        # assertion for given response
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('count'),
            3
        )

    def validate_supervisor_can_view_history(self, supervisor_url, user):
        self.client.force_login(user)
        response = self.client.get(supervisor_url)
        self.validate_response(response)

    def test_user_leave_account_history(self):
        for i in range(3):
            LeaveAccountHistory.objects.create(
                user=self.created_users[1],
                actor=self.created_users[2],
                account=self.account,
                action=ASSIGNED,
                previous_balance=10-i,
                previous_usable_balance=10-i,
                new_balance=9-(i+1),
                new_usable_balance=9-(i+1),
                remarks="leave"
            )

        normal_url = reverse(
            'api_v1:leave:user-balance-history-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'balance_id': self.account.id,
                'user_id': self.created_users[1].id
            }
        )
        self.client.force_login(self.created_users[2])
        response = self.client.get(normal_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

        # can view history of own leave account
        self.client.force_login(self.created_users[1])
        response = self.client.get(normal_url)
        self.validate_response(response)

        # can view leave account history of their subordinates
        supervisor_url = normal_url + '?as=supervisor'

        self.validate_supervisor_can_view_history(supervisor_url, self.created_users[2])
        self.validate_supervisor_can_view_history(supervisor_url, self.created_users[3])
        self.validate_supervisor_can_view_history(supervisor_url, self.created_users[4])

        # HR can view leave account history of all user
        hr_url = normal_url + "?as=hr"
        self.client.force_login(self.admin)
        response = self.client.get(hr_url)
        self.validate_response(response)
