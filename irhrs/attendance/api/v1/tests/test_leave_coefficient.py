from datetime import time, timedelta
from django.urls import reverse
from irhrs.attendance.api.v1.tests.factory import (
    IndividualAttendanceSettingFactory,
    IndividualUserShiftFactory,
    WorkDayFactory,
    WorkShiftFactory,
    WorkTimingFactory
)
from irhrs.attendance.models.attendance import TimeSheet
from irhrs.attendance.tasks.timesheets import (
    correct_leave_timesheets,
    populate_timesheets
)
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import (
    LeaveAccountFactory,
    LeaveRuleFactory,
    LeaveTypeFactory,
    MasterSettingFactory
)
from irhrs.leave.models.request import LeaveRequest
from irhrs.users.models.supervisor_authority import UserSupervisor


class TestLeaveCoefficients(RHRSAPITestCase):
    organization_name = "Google"
    users = [
        ("admin@email.com", "password", "Male"),
        ("normal@email.com", "password", "Male")
    ]
    tomorrow = (get_today() + timedelta(days=1)).strftime("%Y-%m-%d")

    def create_shift(self, name, working_minutes, start_time, end_time):
        shift = WorkShiftFactory(
            name=name,
            work_days=7,
            organization=self.organization
        )
        shift.work_days.all().delete()
        for day in range(1, 8):
            work_day = WorkDayFactory(
                shift=shift, day=day,
                applicable_from=get_today() - timedelta(days=30)
            )
            work_day.timings.all().delete()
            WorkTimingFactory(
                working_minutes=working_minutes,
                work_day=work_day,
                start_time=start_time,
                end_time=end_time
            )
        return shift

    def setUp(self):
        super().setUp()
        self.user = self.created_users[1]
        UserSupervisor.objects.create(
            user=self.user,
            supervisor=self.admin,
            authority_order=1,
            approve=True,
            deny=True
        )
        self.master_settings = MasterSettingFactory(
            organization=self.organization,
            half_shift_leave=True,
            effective_from=get_today() - timedelta(days=30),
            effective_till=get_today() + timedelta(days=30)
        )
        self.leave_type = LeaveTypeFactory(master_setting=self.master_settings)
        self.leave_rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            employee_can_apply=True,
            can_apply_half_shift=True
        )
        self.leave_account = LeaveAccountFactory(
            user=self.user, rule=self.leave_rule, balance=3, usable_balance=3
        )
        self.shift1 = self.create_shift(
            name="shift1",
            working_minutes=420.0,
            start_time=time(hour=10, minute=0),
            end_time=time(hour=17, minute=0)
        )

        self.shift2 = self.create_shift(
            name="shift2",
            working_minutes=420.0,
            start_time=time(hour=11, minute=0),
            end_time=time(hour=18, minute=0)
        )

        self.ias = IndividualAttendanceSettingFactory(
            user=self.user, work_shift=self.shift1
        )
        self.ius = IndividualUserShiftFactory(
            shift=self.shift1,
            individual_setting=self.ias,
            applicable_from=get_today() - timedelta(days=30)
        )

    def payload(self, part_of_day):
        return {
            "leave_account": self.leave_account.id,
            "details": "leave coefficient",
            "part_of_day": part_of_day,
            "start": self.tomorrow,
            "end": self.tomorrow
        }

    @property
    def leave_request_url(self):
        return reverse(
            "api_v1:leave:leave-request-list",
            kwargs={"organization_slug": self.organization.slug}
        )

    def test_leave_coefficient(self):
        self.client.force_login(self.user)
        response = self.client.post(self.leave_request_url, data=self.payload("first"))
        self.assertEqual(response.status_code, 201)
        response = self.client.post(self.leave_request_url, data=self.payload("second"))
        self.assertEqual(response.status_code, 201)

        self.client.force_login(self.created_users[0])
        LeaveRequest.objects.update(status="Approved")

        self.ius.shift1 = self.shift2
        self.ius.save()

        populate_timesheets(self.tomorrow)
        correct_leave_timesheets(self.tomorrow)

        self.assertEqual(
            list(TimeSheet.objects.values_list("leave_coefficient", flat=True)),
            ["Full Leave"]
        )
