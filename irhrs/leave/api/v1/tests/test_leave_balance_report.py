from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_yesterday
from irhrs.leave.api.v1.tests.factory import LeaveAccountFactory, LeaveRuleFactory, \
    LeaveTypeFactory, MasterSettingFactory
from irhrs.leave.constants.model_constants import GENERAL, YEARS_OF_SERVICE, COMPENSATORY
from irhrs.organization.api.v1.tests.factory import OrganizationBranchFactory


class TestLeaveBalanceReport(RHRSTestCaseWithExperience):
    users = [
        ('admin@email.com', 'password', 'Female', 'HR'),
        ('normal@email.com', 'password', 'Male', 'Developer'),
        ('usertwo@email.com', 'password', 'Male', 'Developer'),
        ('normalthree@email.com', 'password', 'Male', 'Developer')
    ]
    organization_name = 'Google'

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.master_setting = MasterSettingFactory(
            name="Master Setting 2021",
            organization=self.organization,
            effective_from=get_yesterday()
        )
        self.leave_type1 = LeaveTypeFactory(
            name="Casual Leave",
            master_setting=self.master_setting,
            category=GENERAL
        )
        self.leave_type2 = LeaveTypeFactory(
            name="Birami Leave",
            master_setting=self.master_setting,
            category=YEARS_OF_SERVICE
        )
        self.leave_type3 = LeaveTypeFactory(
            name="Unpaid Leave",
            master_setting=self.master_setting,
            category=COMPENSATORY
        )
        self.rule1 = LeaveRuleFactory(
            name="Document Required",
            leave_type=self.leave_type1
        )
        self.rule2 = LeaveRuleFactory(
            name="Continuous Leave",
            leave_type=self.leave_type2
        )
        self.rule3 = LeaveRuleFactory(
            name="Depletion Required",
            leave_type=self.leave_type3
        )
        self.account1 = LeaveAccountFactory(
            user=self.created_users[1],
            rule=self.rule1
        )
        self.account2 = LeaveAccountFactory(
            user=self.created_users[1],
            rule=self.rule2
        )
        self.account3 = LeaveAccountFactory(
            user=self.created_users[2],
            rule=self.rule2
        )
        self.account4 = LeaveAccountFactory(
            user=self.created_users[2],
            rule=self.rule3
        )
        self.branch1 = OrganizationBranchFactory(
            name="Kathmandu",
            organization=self.organization
        )
        self.branch2 = OrganizationBranchFactory(
            name="Lalitpur",
            organization=self.organization
        )
        self.leave_type_name_for_user1 = [self.leave_type1.name, self.leave_type2.name]
        self.leave_type_name_for_user2 = [self.leave_type2.name, self.leave_type3.name]
        first_user_detail = self.created_users[1].detail
        first_user_detail.branch = self.branch1
        first_user_detail.save()

        second_user_detail = self.created_users[2].detail
        second_user_detail.branch = self.branch2
        second_user_detail.save()

    @staticmethod
    def get_leave_type_name(leave_accounts):
        return [account['name'] for account in leave_accounts]

    def test_leave_balance_report(self):
        url = reverse(
            'api_v1:leave:individual-leave-balance-report-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

        # check if overlapped leave_type effects users leave account in report
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('results')[0].get('full_name'),
            self.created_users[1].full_name
        )
        leave_accounts = response.json().get('results')[0].get('leave_accounts')
        self.assertEqual(
            len(leave_accounts),
            2
        )
        self.assertEqual(
            self.get_leave_type_name(leave_accounts),
            self.leave_type_name_for_user1
        )
        self.assertEqual(
            response.json().get('results')[1].get('full_name'),
            self.created_users[2].full_name
        )

        leave_accounts = response.json().get('results')[1].get('leave_accounts')
        self.assertEqual(
            len(leave_accounts),
            2
        )
        self.assertEqual(
            self.get_leave_type_name(leave_accounts),
            self.leave_type_name_for_user2
        )

        # check if search by name effects users leave account in report
        search_url = url + "?search=norm"
        response = self.client.get(search_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            len(response.json().get('results')),
            1
        )
        self.assertEqual(
            response.json().get('results')[0].get('full_name'),
            self.created_users[1].full_name
        )
        leave_accounts = response.json().get('results')[0].get('leave_accounts')
        self.assertEqual(
            len(leave_accounts),
            2
        )
        self.assertEqual(
            self.get_leave_type_name(leave_accounts),
            self.leave_type_name_for_user1
        )

        # check if filter by branch effects users leave account in report
        branch_filter_url = url + f"?branch={self.branch1.slug}"
        response = self.client.get(branch_filter_url)
        self.assertEqual(
            len(response.json().get('results')),
            1
        )
        self.assertEqual(
            response.json().get('results')[0].get('full_name'),
            self.created_users[1].full_name
        )
        leave_accounts = response.json().get('results')[0].get('leave_accounts')
        self.assertEqual(
            len(leave_accounts),
            2
        )
        self.assertEqual(
            self.get_leave_type_name(leave_accounts),
            self.leave_type_name_for_user1
        )

        # check if filter by branch effects users leave account in report
        branch_filter_url = url + f"?branch={self.branch2.slug}"
        response = self.client.get(branch_filter_url)
        self.assertEqual(
            len(response.json().get('results')),
            1
        )
        self.assertEqual(
            response.json().get('results')[0].get('full_name'),
            self.created_users[2].full_name
        )
        leave_accounts = response.json().get('results')[0].get('leave_accounts')
        self.assertEqual(
            len(leave_accounts),
            2
        )
        self.assertEqual(
            self.get_leave_type_name(leave_accounts),
            self.leave_type_name_for_user2
        )

