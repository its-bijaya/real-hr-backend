from datetime import datetime
from django.utils import timezone
from django.urls import reverse
from irhrs.attendance.api.v1.tests.factory import (
    IndividualAttendanceSettingFactory,
    TimeSheetFactory, WorkShiftFactory2,
)
from irhrs.attendance.constants import OFFDAY
from irhrs.attendance.models.shift_roster import TimeSheetRoster
from irhrs.attendance.utils.timesheet import update_work_shift_in_timesheet
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import (
    LeaveAccountFactory,
    LeaveRuleFactory,
    LeaveTypeFactory,
    MasterSettingFactory,
)
from irhrs.leave.constants.model_constants import COMPENSATORY
from irhrs.leave.models.account import LeaveAccountHistory
from irhrs.leave.models.rule import CompensatoryLeave, CompensatoryLeaveCollapsibleRule
from irhrs.leave.tasks import add_compensatory_leave, collapse_compensatory_leave


class TestCompensatoryRule(RHRSAPITestCase):
    users = [
        ("user@gmail.com", "user1", "Male"),
        ("normal@gmail.com", "user2", "Female")
    ]

    organization_name = "aayu"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.created_users[0])
        self.user = self.created_users[1]
        self.master_setting = MasterSettingFactory(
            organization=self.organization,
            employees_can_apply=True,
            admin_can_assign=True,
            paid=True,
            compensatory=True
        )
        self.leave_type = LeaveTypeFactory(
            master_setting=self.master_setting,
            category=COMPENSATORY
        )
        self.leave_rule = LeaveRuleFactory(leave_type = self.leave_type)
        self.leave_account = LeaveAccountFactory(
            user=self.user, rule=self.leave_rule, balance=10
        )
        self.leave_account_history = LeaveAccountHistory.objects.create(
            account=self.leave_account,
            user=self.user,
            actor=self.admin,
            action="Added",
            previous_balance=self.leave_account.balance,
            previous_usable_balance=self.leave_account.usable_balance,
            new_balance=20,
            new_usable_balance=20,
        )

        self.time_sheet = TimeSheetFactory(
            timesheet_user=self.user,
            timesheet_for=get_today() - timezone.timedelta(days=1),
            coefficient=OFFDAY,
            is_present=True,
            punch_in=datetime(2022, 8, 28, 10, 0, 0),
            punch_out=datetime(2022, 8, 28, 15, 0, 0),
        )
        self.compensatory_rules = [
            {
                "balance_to_grant": 2,
                "hours_in_off_day": 4
            },
            {
                "balance_to_grant": 3,
                "hours_in_off_day": 5
            }

        ]
        self.leave_collapsible_rule = {
            "collapse_after": 1,
            "collapse_after_unit": "Days"
        }
        self.payload = {
            "name": "compensatory leave",
            "description": "Multiple compensatory leave rule",
            "employee_can_apply": True,
            "require_prior_approval": False,
            "compensatory_rules": self.compensatory_rules,
            "leave_collapsible_rule": self.leave_collapsible_rule,
            "is_paid": True,
            "admin_can_assign": True,
            "depletion_leave_types": [],
            "leave_type": self.leave_type.id
        }

        self.update_url = reverse(
            "api_v1:leave:leave-type-detail",
            kwargs={
                "organization_slug": self.organization.slug,
                "pk": self.leave_rule.id
            }
        )


    def test_compensatory_leave_rule(self):
        url = reverse(
            "api_v1:leave:leave-type-list",
            kwargs={"organization_slug": self.organization.slug},
        )

        response = self.client.post(url, self.payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)

        self.assertEqual(
            response.json()["compensatory_rules"][0]["balance_to_grant"], 2.0
        )

        self.assertEqual(
            response.json()["leave_collapsible_rule"]["collapse_after"], 1.0
        )

    def test_non_collapsible_leave(self):
        url = reverse(
            "api_v1:leave:leave-type-list",
            kwargs={"organization_slug": self.organization.slug},
        )

        self.payload['leave_collapsible_rule']={}
        payload=self.payload

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)

        self.assertEqual(response.json().get("leave_collapsible_rule"), None)

    def test_update_invalid_compensatory_leave_rules(self):
        self.payload["compensatory_rules"][1]['balance_to_grant']=1
        payload = self.payload
        response = self.client.put(self.update_url, payload, format="json")
        self.assertEqual(response.status_code, 400, response.data)

        self.assertEqual(
            response.json()["balance_to_grant"][1],
            "Must be greater than previous balance to grant.",
        )

    def test_update_valid_compensatory_leave_rules(self):
        response = self.client.put(self.update_url, self.payload, format="json")
        self.assertEqual(response.status_code, 200, response.data)

        self.assertEqual(
            response.json()["compensatory_rules"], self.compensatory_rules
        )

    def test_compensatory_leave_balance_added_and_deducted(self):
        self.client.force_login(self.created_users[1])
        for rule in self.compensatory_rules:
            CompensatoryLeave.objects.create(
                    rule=self.leave_rule,
                    **rule
                )

        previous_balance = self.leave_account.balance
        added_balance = previous_balance+self.compensatory_rules[1]['balance_to_grant']

        add_compensatory_leave(self.leave_account, self.time_sheet)
        self.assertEqual(
            added_balance,
            self.leave_account.balance
        )

        if self.leave_collapsible_rule:
            CompensatoryLeaveCollapsibleRule.objects.bulk_create([
                CompensatoryLeaveCollapsibleRule(
                    rule=self.leave_rule,
                    **self.leave_collapsible_rule

                )
            ])
        collapse_compensatory_leave(self.leave_account)
        self.assertEqual(
            added_balance-self.compensatory_rules[1]['balance_to_grant'],
            self.leave_account.balance
        )

    def test_revert_compensatory_leave_when_shift_changes(self):
        self.client.force_login(self.created_users[1])
        for rule in self.compensatory_rules:
            CompensatoryLeave.objects.create(
                rule=self.leave_rule,
                **rule
            )

        previous_balance = self.leave_account.balance
        added_balance = previous_balance + self.compensatory_rules[1]['balance_to_grant']

        add_compensatory_leave(self.leave_account, self.time_sheet)
        self.assertEqual(
            added_balance,
            self.leave_account.balance
        )
        compensatory_leaves = self.time_sheet.compensatory_leave.all()

        self.assertEqual(
            1,
            compensatory_leaves.count()
        )
        self.assertEqual(
            self.compensatory_rules[1]['balance_to_grant'],
            compensatory_leaves.first().balance_granted
        )
        IndividualAttendanceSettingFactory(user=self.time_sheet.timesheet_user)
        work_shift = WorkShiftFactory2(work_days=7)
        TimeSheetRoster.objects.create(user=self.user, shift=work_shift, date=self.time_sheet.timesheet_for)
        work_shift.work_days.update(applicable_from=self.time_sheet.timesheet_for-timezone.timedelta(days=1))
        update_work_shift_in_timesheet(self.time_sheet, work_shift)
        self.leave_account.refresh_from_db()

        self.assertEqual(compensatory_leaves.count(), 0)
        self.assertEqual(previous_balance, self.leave_account.balance)
