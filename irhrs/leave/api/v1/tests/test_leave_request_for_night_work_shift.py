from datetime import time

from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    WorkShiftFactory, IndividualUserShiftFactory, WorkDayFactory, WorkTimingFactory
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, LeaveAccountFactory
from irhrs.leave.constants.model_constants import FULL_DAY, FIRST_HALF, SECOND_HALF
from irhrs.leave.models import LeaveAccount, LeaveRequest
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models import UserSupervisor
from irhrs.core.utils.common import get_today


class TestLeaveRequestForNightWorkShift(RHRSAPITestCase):
    organization_name = 'Google'
    users = [
        ('normal@email.com', 'password', 'Male'),
    ]

    def setUp(self):
        super().setUp()
        next_week = get_today() + timedelta(days=7)
        last_week = get_today() - timedelta(days=7)
        self.master_settings = MasterSettingFactory(
            organization=self.organization,
            effective_from=last_week,
            effective_till=next_week,
            half_shift_leave=True
        )
        self.leave_type = LeaveTypeFactory(master_setting=self.master_settings)
        self.rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            employee_can_apply=True,
            can_apply_half_shift=True
        )
        self.account = LeaveAccountFactory(user=self.created_users[0], rule=self.rule)
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

    @property
    def leave_request_url(self):
        return reverse(
            'api_v1:leave:leave-request-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    @property
    def payload(self):
        return {
            "leave_account": self.account.id,
            "details": "Night work shift",
            "part_of_day": FULL_DAY,
            "start": "2021-07-26",
            "end": "2021-07-28"
        }

    @property
    def payload2(self):
        return {
            "leave_account": self.account.id,
            "details": "Night work shift",
            "part_of_day": FULL_DAY,
            "start": "2021-08-02",
            "end": "2021-08-02"
        }

    @property
    def first_half_payload(self):
        return {
            "leave_account": self.account.id,
            "details": "First Half Leave",
            "part_of_day": FIRST_HALF,
            "start": "2021-07-29",
            "end": "2021-07-29"
        }

    @property
    def first_half_payload2(self):
        return {
            "leave_account": self.account.id,
            "details": "First Half Leave",
            "part_of_day": FIRST_HALF,
            "start": "2021-08-02",
            "end": "2021-08-02"
        }

    @property
    def second_half_payload(self):
        return {
            "leave_account": self.account.id,
            "details": "Second Half Leave",
            "part_of_day": SECOND_HALF,
            "start": "2021-07-29",
            "end": "2021-07-29"
        }

    @property
    def second_half_payload2(self):
        return {
            "leave_account": self.account.id,
            "details": "Second Half Leave",
            "part_of_day": SECOND_HALF,
            "start": "2021-08-02",
            "end": "2021-08-02"
        }

    def test_leave_request_for_night_work_shift(self):
        for day in range(1, 8):
            self.work_day = WorkDayFactory(shift=self.shift, day=day, applicable_from="2021-07-20")
            self.work_day.timings.all().delete()
            self.work_timing = WorkTimingFactory(
                work_day=self.work_day,
                start_time=time(hour=21, minute=0),
                end_time=time(hour=6, minute=0),
                extends=True
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
        response = self.client.post(
            self.leave_request_url,
            self.payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(
            response.json().get('part_of_day'),
            FULL_DAY
        )
        self.assertEqual(
            response.json().get('balance'),
            3
        )
        self.assertEqual(
            LeaveAccount.objects.first().usable_balance,
            7
        )
        self.assertEqual(
            LeaveRequest.objects.get(part_of_day=FULL_DAY).start.date().strftime('%Y-%m-%d'),
            "2021-07-26"
        )
        self.assertEqual(
            LeaveRequest.objects.get(part_of_day=FULL_DAY).end.date().strftime('%Y-%m-%d'),
            "2021-07-29"
        )

        response = self.client.post(
            self.leave_request_url,
            self.first_half_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.json().get('part_of_day'),
            FIRST_HALF
        )
        self.assertEqual(
            LeaveAccount.objects.first().usable_balance,
            6.5
        )
        self.assertEqual(
            response.json().get('balance'),
            0.5
        )
        self.assertEqual(
            LeaveRequest.objects.get(part_of_day=FIRST_HALF).start.date().strftime('%Y-%m-%d'),
            "2021-07-29"
        )

        response = self.client.post(
            self.leave_request_url,
            self.second_half_payload,
            format='json'
        )
        self.assertEqual(
            response.json().get('part_of_day'),
            SECOND_HALF
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(
            LeaveAccount.objects.first().usable_balance,
            6
        )
        self.assertEqual(
            response.json().get('balance'),
            0.5
        )
        self.assertEqual(
            LeaveRequest.objects.get(part_of_day=SECOND_HALF).start.date().strftime('%Y-%m-%d'),
            "2021-07-29"
        )

        response = self.client.post(
            self.leave_request_url,
            self.payload2,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(
            response.json().get('part_of_day'),
            FULL_DAY
        )
        self.assertEqual(
            response.json().get('balance'),
            1
        )
        self.assertEqual(
            LeaveAccount.objects.first().usable_balance,
            5
        )
        self.assertEqual(
            LeaveRequest.objects.filter(
                part_of_day=FULL_DAY,
            ).first().start.date().strftime('%Y-%m-%d'),
            "2021-08-02"
        )
        self.assertEqual(
            LeaveRequest.objects.filter(
                part_of_day=FULL_DAY
            ).first().end.date().strftime('%Y-%m-%d'),
            "2021-08-03"
        )

        response = self.client.post(
            self.leave_request_url,
            self.first_half_payload2,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json().get('non_field_errors'),
            ['The leave for this range already exists']
        )

    def test_leave_request_for_night_work_shift_v2(self):
        for day in range(1, 8):
            self.work_day = WorkDayFactory(shift=self.shift, day=day, applicable_from="2021-07-20")
            self.work_day.timings.all().delete()
            self.work_timing = WorkTimingFactory(
                work_day=self.work_day,
                start_time=time(hour=18, minute=0),
                end_time=time(hour=3, minute=0),
                extends=True
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

        response = self.client.post(
            self.leave_request_url,
            self.payload2,
            format='json'
        )
        self.assertEqual(
            response.json().get('part_of_day'),
            FULL_DAY
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(
            response.json().get('balance'),
            1
        )
        self.assertEqual(
            LeaveAccount.objects.first().usable_balance,
            9
        )
        self.assertEqual(
            LeaveRequest.objects.filter(
                part_of_day=FULL_DAY,
            ).first().start.date().strftime('%Y-%m-%d'),
            "2021-08-02"
        )
        self.assertEqual(
            timezone.localtime(LeaveRequest.objects.filter(
                part_of_day=FULL_DAY
            ).first().end).date().strftime('%Y-%m-%d'),
            "2021-08-03"
        )

        response = self.client.post(
            self.leave_request_url,
            self.first_half_payload2,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json().get('non_field_errors'),
            ['The leave for this range already exists']
        )

        response = self.client.post(
            self.leave_request_url,
            self.second_half_payload2,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json().get('non_field_errors'),
            ['The leave for this range already exists']
        )
