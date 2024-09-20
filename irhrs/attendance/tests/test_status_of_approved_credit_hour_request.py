from datetime import time, timedelta
from rest_framework import status
from django.urls import reverse
from irhrs.attendance.api.v1.tests.factory import (
    AttendanceAdjustmentFactory, CreditHourSettingFactory,
    IndividualAttendanceSettingFactory, WorkShiftFactory
)
from irhrs.attendance.constants import APPROVED, CREDIT_HOUR, NOT_ADDED
from irhrs.attendance.models.credit_hours import CreditHourRequest
from irhrs.attendance.tasks.credit_hours import generate_credit_hours_for_approved_credit_hours
from irhrs.attendance.tasks.overtime import generate_daily_overtime
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import combine_aware, get_today, get_yesterday
from irhrs.leave.api.v1.tests.factory import LeaveRuleFactory, LeaveTypeFactory, MasterSettingFactory
from irhrs.leave.models.account import LeaveAccount
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory


class TestCreditHourApprovedStatus(RHRSTestCaseWithExperience):

    users = [
        ("admin@gmail.com", "admin", "Female", "hr"),
        ("user@gmail.com", "user", "Male", "assistant")
    ]

    organization_name = "Aayulogic"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.created_users[0])
        self.user = self.created_users[1]
        FiscalYearFactory(
            organization=self.organization,
            start_at=get_today(),
            end_at=get_today() + timedelta(days=365)
        )
        self.master_setting = MasterSettingFactory(
            organization=self.organization,
            admin_can_assign=True,
            paid=True,
            effective_from=get_today() - timedelta(days=100),
            effective_till=None,
        )
        self.leave_type = LeaveTypeFactory(
            master_setting=self.master_setting,
            name="credit hour",
            category=CREDIT_HOUR
        )
        self.leave_rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            max_balance="600.0",
            name="credit rule"
        )
        credit_hour_setting = CreditHourSettingFactory(
            organization=self.organization
        )
        attendance_setting = IndividualAttendanceSettingFactory(
            user=self.user,
            credit_hour_setting=credit_hour_setting,
            enable_credit_hour=True
        )
        work_shift = WorkShiftFactory()
        date = get_today() - timedelta(days=100)
        attendance_setting.individual_setting_shift.create(
            shift=work_shift,
            applicable_from=date,
        )
        attendance_setting.credit_hour_setting = credit_hour_setting
        attendance_setting.save()

        self.url = reverse(
            "api_v1:attendance:credit-hour-request-list",
            kwargs={
                "organization_slug": self.organization.slug
            }
        )
        self.payload = {
            "results": [
                {
                    "remarks": "Application for 2 hours credit.",
                    "credit_hour_duration": "02:00:00",
                    "credit_hour_date": get_today() + timedelta(days=2)
                }
            ]
        }
        self.leave_account = LeaveAccount.objects.create(
            user=self.user,
            rule=self.leave_rule,
            balance=360,
            usable_balance=360
        )
        CreditHourRequest.objects.create(**{
            'request_remarks': 'remarks',
            'credit_hour_duration': "3:00:00",
            'credit_hour_date': get_today() - timedelta(days=1),
            'status': APPROVED,
            'sender': self.user,
            'recipient': self.user,
        })

    def test_status_of_approved_credit_hour_requests(self):
        self.client.force_login(self.user)
        punch_in = combine_aware(get_yesterday(), time(8, 0))
        punch_out = combine_aware(get_yesterday(), time(18, 0))
        self.user.timesheets.clock(self.user, punch_in, 'Device')
        self.user.timesheets.clock(self.user, punch_out, 'Device')
        timesheet = self.user.timesheets.get(timesheet_for=get_yesterday())

        generate_credit_hours_for_approved_credit_hours()
        adjustment = AttendanceAdjustmentFactory(
            timesheet=timesheet,
            receiver=self.user,
            timestamp=punch_in - timedelta(hours=3),
            sender=self.user
        )
        adjustment.approve(self.user, 'force')
        generate_daily_overtime(success_date=str(get_today()))

        response = self.client.get(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json()['results'][0]['credit_hour_status'], "Added"
        )
        account = LeaveAccount.objects.last()
        self.assertEqual(
            account.usable_balance, 540.0
        )

    def test_invalid_status_for_approved_credit_hour_request(self):
        self.client.force_login(self.user)

        generate_credit_hours_for_approved_credit_hours()
        generate_daily_overtime(success_date=str(get_today()))

        response = self.client.get(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json()['results'][0]['credit_hour_status'], NOT_ADDED
        )
        account = LeaveAccount.objects.first()
        self.assertEqual(
            account.usable_balance, 360.0
        )
