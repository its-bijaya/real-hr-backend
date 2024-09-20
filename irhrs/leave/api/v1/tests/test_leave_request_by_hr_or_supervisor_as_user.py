from datetime import timedelta, time
from django.urls import reverse
from irhrs.attendance.api.v1.tests.factory import (
    IndividualAttendanceSettingFactory, 
    IndividualUserShiftFactory, WorkDayFactory, 
    WorkShiftFactory, 
    WorkTimingFactory
)
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import (
    LeaveAccountFactory,
    LeaveRuleFactory,
    LeaveTypeFactory,
    MasterSettingFactory,
)
from irhrs.leave.constants.model_constants import FULL_DAY
from rest_framework import status
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models.supervisor_authority import UserSupervisor


class TestLeaveRequestByHR(RHRSAPITestCase):
    users = [
        ("admin@gmail.com", "admin", "Female")
    ]

    organization_name = "Aayu"

    def setUp(self):
        super().setUp()
        next_week = get_today() + timedelta(days=7)
        last_week = get_today() - timedelta(days=7)
        self.master_settings = MasterSettingFactory(
            organization=self.organization,
            effective_from=last_week,
            effective_till=next_week,
            employees_can_apply = False,
            admin_can_assign = True
        )
        self.leave_type = LeaveTypeFactory(
            master_setting=self.master_settings
        )
        self.leave_rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            employee_can_apply=False,
            admin_can_assign = True
        )
        self.account = LeaveAccountFactory(
            user=self.created_users[0], rule=self.leave_rule
        )
        self.shift = WorkShiftFactory(
            name="Night Shift",
            work_days=7,
            organization=self.organization,
            start_time_grace=time(hour=0, minute=0, second=0),
            end_time_grace=time(hour=0, minute=0, second=0)
        )
        self.shift.work_days.all().delete()
        self.client.force_login(self.created_users[0])
        UserSupervisor.objects.create(
            user=self.created_users[0],
            supervisor=UserFactory(),
            authority_order=1,
            approve=True,
            deny=True,
            forward=False
        )

        for day in range(1, 8):
            self.work_day = WorkDayFactory(shift=self.shift, day=day, applicable_from="2021-07-20")
            self.work_day.timings.all().delete()
            self.work_timing = WorkTimingFactory(
                work_day=self.work_day,
                start_time=time(hour=9, minute=0),
                end_time=time(hour=17, minute=0),
            )
        self.ias = IndividualAttendanceSettingFactory(
            user=self.created_users[0],
            work_shift=self.shift
        )
        self.ius = IndividualUserShiftFactory(
            shift=self.shift,
            individual_setting=self.ias,
            applicable_from="2021-07-20"
        )
        self.mastersettings = MasterSettingFactory(
            organization=self.organization,
            effective_from=last_week,
            effective_till=next_week,
            half_shift_leave=True,
            employees_can_apply = True,
            admin_can_assign = True
        )
        self.assign_leave_type = LeaveTypeFactory(
            master_setting=self.mastersettings
        )
        self.assign_leave_rule = LeaveRuleFactory(
            leave_type=self.assign_leave_type,
            employee_can_apply=True,
            admin_can_assign = True,
            can_apply_half_shift=True
        )
        self.leave_account = LeaveAccountFactory(
            user=self.created_users[0], rule=self.assign_leave_rule
        )
    @property
    def url(self):
        return reverse(
            "api_v1:leave:leave-request-list",
            kwargs={"organization_slug": self.organization.slug},
        ) 

    def test_invalid_leave_request_by_hr_or_supervisor_as_user(self):
        payload = {
            "leave_account": self.account.id,
            "details": "Night work shift",
            "part_of_day": FULL_DAY,
            "start": "2021-07-26",
            "end": "2021-07-28"
        }
        response = self.client.post(
            self.url, data=payload, format="json"
        )
        
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json().get('non_field_errors')[0],
            "You cannot request this leave."
        )

    def test_valid_leave_request_by_hr_or_supervisor_as_user(self):
        payload = {
            "leave_account": self.leave_account.id,
            "details": "Night work shift",
            "part_of_day": FULL_DAY,
            "start": "2021-07-22",
            "end": "2021-07-22"
        }
        response = self.client.post(
            self.url, data=payload, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED
        )
        self.assertEqual(
            response.json().get('balance'), 1.0
        )
