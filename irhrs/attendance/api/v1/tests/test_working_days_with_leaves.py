from datetime import time, timedelta
from dateutil.rrule import DAILY, rrule
from django.urls import reverse
from irhrs.attendance.api.v1.tests.factory import (
    IndividualAttendanceSettingFactory,
    IndividualUserShiftFactory,
    WorkDayFactory,
    WorkShiftFactory,
    WorkTimingFactory,
)
from irhrs.attendance.models.attendance import TimeSheet
from irhrs.attendance.tasks.timesheets import populate_timesheets
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import (
    LeaveAccountFactory,
    LeaveRuleFactory,
    LeaveTypeFactory,
    MasterSettingFactory,
)
from irhrs.leave.models.request import LeaveRequest
from irhrs.users.models.supervisor_authority import UserSupervisor
from irhrs.attendance.utils.payroll import get_worked_days


class TestLeaveCoefficients(RHRSTestCaseWithExperience):
    organization_name = "Google"
    users = [
        ("admin@email.com", "password", "Male", "Developer"),
        ("normal@email.com", "password", "Male", "Developer"),
    ]
    tomorrow = (get_today() + timedelta(days=1)).strftime("%Y-%m-%d")

    def create_shift(self, name, working_minutes, start_time, end_time):
        shift = WorkShiftFactory(name=name, work_days=7, organization=self.organization)
        shift.work_days.all().delete()
        for day in range(2, 7):
            work_day = WorkDayFactory(
                shift=shift, day=day, applicable_from=get_today() - timedelta(days=60)
            )
            work_day.timings.all().delete()
            WorkTimingFactory(
                working_minutes=working_minutes,
                work_day=work_day,
                start_time=start_time,
                end_time=end_time,
            )
        return shift

    def setUp(self):
        super().setUp()
        month_start = get_today().replace(day=1)
        self.last_month_end = month_start - timedelta(days=1)
        self.last_month_start = self.last_month_end.replace(day=1)

        self.user = self.created_users[1]
        UserSupervisor.objects.create(
            user=self.user,
            supervisor=self.admin,
            authority_order=1,
            approve=True,
            deny=True,
        )
        self.master_settings = MasterSettingFactory(
            organization=self.organization,
            half_shift_leave=True,
            holiday_inclusive=True,
            effective_from=get_today() - timedelta(days=60),
            effective_till=get_today() + timedelta(days=60),
        )
        self.leave_type = LeaveTypeFactory(master_setting=self.master_settings)
        self.leave_rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            employee_can_apply=True,
            can_apply_half_shift=True,
            holiday_inclusive=True,
            inclusive_leave="Include Holiday And Off Day",
            is_paid=False,
            inclusive_leave_number=0,
        )
        self.leave_account = LeaveAccountFactory(
            user=self.user, rule=self.leave_rule, balance=10, usable_balance=10
        )
        self.shift1 = self.create_shift(
            name="shift1",
            working_minutes=420.0,
            start_time=time(hour=10, minute=0),
            end_time=time(hour=17, minute=0),
        )

        self.ias = IndividualAttendanceSettingFactory(
            user=self.user, work_shift=self.shift1
        )
        self.ius = IndividualUserShiftFactory(
            shift=self.shift1,
            individual_setting=self.ias,
            applicable_from=get_today() - timedelta(days=60),
        )
        self.leave_start =self.last_month_start
        self.leave_end = self.last_month_start + timedelta(days=8)

    @property
    def payload(self):
        return {
            "leave_account": self.leave_account.id,
            "details": "leave coefficient",
            "part_of_day": "full",
            "start": self.leave_start,
            "end": self.leave_end,
        }

    @property
    def leave_request_url(self):
        return reverse(
            "api_v1:leave:leave-request-list",
            kwargs={"organization_slug": self.organization.slug},
        )

    @property
    def leave_detail_url(self):
        return (
            reverse(
                "api_v1:leave:leave-request-detail",
                kwargs={
                    "organization_slug": self.organization.slug,
                    "pk": LeaveRequest.objects.get().id,
                },
            )
        )

    def test_workdays_for_unpaid_leave(self):
        self.client.force_login(self.user)
        response = self.client.post(self.leave_request_url, data=self.payload)
        self.assertEqual(response.status_code, 201)
        self.client.force_login(self.admin)
        response = self.client.patch(
            self.leave_detail_url + "?as=hr",
            data={"supervisor_remarks": "approved leave", "status": "Approved"},
        )
        self.assertEqual(response.status_code, 200, self.leave_detail_url)

        last_month_dates = [
            dt.date()
            for dt in rrule(
                DAILY, dtstart=self.last_month_start, until=self.last_month_end
            )
        ]

        for date in last_month_dates:
            populate_timesheets(date.strftime("%Y-%m-%d"))

        TimeSheet.objects.filter(leave_coefficient="No Leave", coefficient=1).update(
            is_present=True
        )

        no_of_days = get_worked_days(
            self.created_users[1],
            start=last_month_dates[0],
            end=last_month_dates[-1],
            count_offday_holiday_as_worked=True,
        )
        leave_days = (self.leave_end - self.leave_start).days + 1
        month_days = (last_month_dates[-1] - last_month_dates[0]).days + 1
        self.assertEqual(no_of_days, month_days - leave_days)
