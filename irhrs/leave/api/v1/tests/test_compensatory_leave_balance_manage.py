from django.utils import timezone
from irhrs.core.utils.common import get_today
from django.urls import reverse

from irhrs.attendance.constants import OFFDAY
from irhrs.attendance.api.v1.tests.factory import TimeSheetFactory
from irhrs.leave.constants.model_constants import COMPENSATORY
from irhrs.leave.api.v1.tests.factory import LeaveAccountFactory, LeaveRuleFactory, LeaveTypeFactory
from irhrs.common.api.tests.common import RHRSAPITestCase


class CompensatoryLeaveBalanceManageTestCase(RHRSAPITestCase):
    users = [
        ("admin@example.com", "Male", "secret"),
        ("userone@example.com", "Male", "secret"),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.leave_type = LeaveTypeFactory(category=COMPENSATORY)
        self.leave_rule = LeaveRuleFactory(leave_type=self.leave_type)
        self.leave_account = LeaveAccountFactory(
            user=self.created_users[1],
            balance=20,
            rule=self.leave_rule
        )
        self.timesheet = TimeSheetFactory(
            timesheet_user=self.created_users[1],
            coefficient=OFFDAY,
            timesheet_for=get_today() - timezone.timedelta(days=1),
            is_present=True
        )

    def test_compensatory_leave_balance_manage(self):
        url = reverse(
            "api_v1:leave:manage-compensatory-list",
            kwargs={
                "organization_slug": self.organization.slug,
                "user_id": self.created_users[1].id,
                "account_id": self.leave_account.id
            }
        )
        self.client.login(email=self.users[0][0], password=self.users[0][1])

        data = {
            "leave_for": self.timesheet.timesheet_for,
            "balance_granted": 1.5,
            "balance_consumed": 0.5,
            "remarks": "Updated balance"
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201, response.data)
