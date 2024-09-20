from datetime import timedelta

from django.core import mail
from django.urls import reverse

from irhrs.attendance.api.v1.tests.factory import WorkShiftFactory2
from irhrs.attendance.models import BreakOutPenaltySetting, PenaltyRule, \
    IndividualAttendanceSetting, IndividualUserShift, WorkDay
from irhrs.attendance.models.breakout_penalty import BreakoutPenaltyLeaveDeductionSetting
from irhrs.attendance.tasks.timesheets import populate_timesheet_for_user
from irhrs.attendance.tests.factory import TimeSheetUserPenaltyFactory
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.constants.organization import LEAVE_DEDUCTION_ON_PENALTY
from irhrs.core.constants.payroll import MONTH
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, LeaveAccountFactory
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.attendance.constants import CREDIT_HOUR, FREQUENCY
from irhrs.organization.models import EmailNotificationSetting


class TestPenaltyEmail(RHRSTestCaseWithExperience):
    users = [
        ("hr@gmail.com", "admin", "Female", "admin"),
        ("user@gmail.com", "first", "Female", "supervisor")
    ]

    organization_name = "Aayu bank"
    def setUp(self):
        super().setUp()
        fiscal_year = FiscalYearFactory(
            organization=self.organization,
            start_at=get_today(),
            end_at=get_today() + timedelta(days=364)
        )
        fiscal_months = fiscal_year.fiscal_months.order_by('month_index')
        master_setting = MasterSettingFactory(
            organization=self.organization,
            admin_can_assign=True,
            paid=True,
            effective_from=get_today() - timedelta(days=100),
            effective_till=None,
        )
        self.leave_type = LeaveTypeFactory(
            master_setting=master_setting,
            name="penalty deduction",
            category=CREDIT_HOUR
        )
        leave_rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            max_balance="840.0",
            name="new rule"
        )
        LeaveAccountFactory(
            rule=leave_rule,
            user=self.created_users[1],
            balance=300,
            usable_balance=300
        )
        user = self.created_users[1]
        email_type = LEAVE_DEDUCTION_ON_PENALTY

        EmailNotificationSetting.objects.create(
            organization=self.organization,
            email_type=email_type,
            send_email=True,
            allow_unsubscribe=True
        )
        first_fiscal_month = fiscal_months.order_by(
            'month_index').first()
        breakout_penalty_setting = BreakOutPenaltySetting.objects.create(
            organization=self.organization,
            title='AxC',
        )
        rule = PenaltyRule.objects.create(
            penalty_setting=breakout_penalty_setting,
            penalty_duration_in_days=1,
            penalty_counter_value=1,
            penalty_counter_unit=MONTH,
            calculation_type=FREQUENCY,
            tolerated_duration_in_minutes=1,
            tolerated_occurrences=0,
            consider_late_in=False,
            consider_early_out=False,
            consider_in_between_breaks=False,
            penalty_accumulates=True
        )
        self.user_penalty = TimeSheetUserPenaltyFactory(
            loss_accumulated=timedelta(seconds=8400),
            lost_days_count=3,
            penalty_accumulated=3.0,
            fiscal_month=first_fiscal_month,
            start_date=first_fiscal_month.start_at,
            end_date=first_fiscal_month.end_at,
            user=user,
            rule=rule
        )
        BreakoutPenaltyLeaveDeductionSetting.objects.create(leave_type_to_reduce=self.leave_type,
                                                            penalty_setting=breakout_penalty_setting)

        attendance_setting, _ = IndividualAttendanceSetting.objects.update_or_create(
            user=user,
            penalty_setting=breakout_penalty_setting
        )
        shift = WorkShiftFactory2(work_days=7, organization=user.detail.organization)
        applicable_from = first_fiscal_month.start_at
        IndividualUserShift.objects.create(
            individual_setting=attendance_setting,
            shift=shift,
            applicable_from=applicable_from
        )
        WorkDay.objects.filter(shift=shift).update(applicable_from=applicable_from)
        populate_timesheet_for_user(user,
                                    fiscal_year.start_at, fiscal_year.end_at)

    def make_request(self):
        self.client.force_login(self.created_users[0])
        mail.outbox = []
        url = reverse(
            "api_v1:attendance:timesheet-penalty-report-perform-bulk-action",
            kwargs={"organization_slug": self.organization.slug},
        ) + '?as=hr'
        payload = [{
            "penalty": self.user_penalty.id,
            "remarks": "2021-05-10T10:00",
            "status": "Confirmed",
        }]

        return self.client.post(url, data=payload, format="json")

    def test_email_on_penalty(self):
        response = self.make_request()
        emails = mail.outbox
        user = self.created_users[1]
        self.assertEqual(response.status_code, self.status.HTTP_200_OK)
        self.assertEqual(len(emails), 2)
        hr_subject = f"Leave balance deduction of {user.full_name}"
        user_subject = "Leave balance is deducted due to penalty"
        hr_text = (
            f"Leave balance of {user.full_name} has decremented by "
            f"{self.user_penalty.penalty_accumulated} due to penalty."
        )
        user_text = (
            f"Your Leave balance for {self.leave_type.name} has decremented by {self.user_penalty.penalty_accumulated} due to penalty."
        )
        self.assertEqual(emails[0].to, [user.email])
        self.assertEqual(emails[0].subject, user_subject)
        self.assertEqual(emails[0].body, user_text)

        self.assertEqual(emails[1].to, [self.created_users[0].email])
        self.assertEqual(emails[1].subject, hr_subject)
        self.assertEqual(emails[1].body, hr_text)
