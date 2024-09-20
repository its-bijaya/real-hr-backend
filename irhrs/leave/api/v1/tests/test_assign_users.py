from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory
from irhrs.common.api.tests.common import RHRSAPITestCase, RHRSTestCaseWithExperience
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, LeaveAccountFactory
from irhrs.leave.constants.model_constants import ASSIGNED, ASSIGNED_WITH_BALANCE
from irhrs.leave.models import LeaveAccount, LeaveAccountHistory

USER = get_user_model()


class AssignUsersTest(RHRSTestCaseWithExperience):
    organization_name = "ALPL"
    users = [
        ('test@example.com', 'helloSecretWorld', 'Male', 'Programmer'),
    ]

    @property
    def url(self):
        return reverse('api_v1:leave:assign-user-list', args=['alpl'])

    @property
    def normal_user(self):
        return USER.objects.get(email='test@example.com')

    def payload(self, user, leave_rule, assign_default_balance, default_balance, remarks, action):
        return {
            "users": [user],
            "action": action,
            "assign_default_balance": assign_default_balance,
            "leave_rule": leave_rule,
            "default_balance": default_balance,
            "remarks": remarks
        }

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )
        self.master_settings = MasterSettingFactory(organization=self.organization)
        self.leave_type = LeaveTypeFactory(master_setting=self.master_settings)
        self.rule = LeaveRuleFactory(leave_type=self.leave_type)
        IndividualAttendanceSettingFactory(user=self.normal_user)

    def test_assign_users_api(self):
        # Test scenario
        # 1. On valid payload, response should be 201
        # 2. On invalid payload, response should be 400
        # 3. When starting balance is set, the balance should be reflected in leave account
        # 4. When starting balance is set, LeaveAccountHistory should contain ASSIGN_WITH_BALANCE
        # self.assertEqual(LeaveAccount.balance, 35)

        response = self.client.post(
            self.url,
            self.payload(self.normal_user.id, self.rule.id, False, 0, '', "Assign")
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            str(response.json())
        )

        bad_response = self.client.post(
            self.url,
            self.payload(self.normal_user.id, self.rule.id, False, 1, '', "Assign")
        )

        self.assertEqual(
            bad_response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            self.normal_user.leave_accounts.values_list('balance', flat=True).first(),
            0,
            str(response.json())
        )

        self.assertEqual(
            self.normal_user.leave_account_history.values_list('new_balance', flat=True).first(),
            0,
            str(response.json())
        )

        self.assertEqual(
            self.normal_user.leave_account_history.values_list('action', flat=True).first(),
            ASSIGNED,
            str(response.json())
        )

    def test_assign_users_with_default_balance(self):
        response = self.client.post(
            self.url,
            self.payload(self.normal_user.id, self.rule.id, True, 35, 'remarks', "Assign")
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            str(response.json())
        )
        bad_response = self.client.post(
            self.url,
            self.payload(self.normal_user.id, self.rule.id, True, -10, 'remarks', "Assign")
        )
        self.assertEqual(
            bad_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            str(response.json())
        )
        self.assertEqual(
            self.normal_user.leave_accounts.values_list('balance', flat=True).first(),
            35,
            str(response.json())
        )

        self.assertEqual(
            self.normal_user.leave_account_history.values_list('new_balance', flat=True).first(),
            35,
            str(response.json())
        )

        self.assertEqual(
            self.normal_user.leave_account_history.values_list('action', flat=True).first(),
            ASSIGNED_WITH_BALANCE,
            str(response.json())
        )

