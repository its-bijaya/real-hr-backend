import datetime
from datetime import timedelta

from django.utils import timezone
from django.urls import reverse

from irhrs.core.utils.common import get_today
from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    WorkShiftFactory, IndividualUserShiftFactory, WorkDayFactory, WorkTimingFactory
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, LeaveAccountFactory
from irhrs.leave.constants.model_constants import CREDIT_HOUR
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models import UserSupervisor



class TestCreditHourLeaveRequests(RHRSAPITestCase):
    organization_name = "BMW"
    users = [
        ('example@hotmail.com', 'password', 'Male'),
    ]

    def setUp(self):
        super().setUp()
        self.client.force_login(self.created_users[0])
        self.master_settings = MasterSettingFactory(
            organization=self.organization,
            half_shift_leave=True,
            effective_from=get_today() - timezone.timedelta(days=30),
            effective_till=get_today() + timezone.timedelta(days=30),
        )
        self.leave_type = LeaveTypeFactory(
            master_setting=self.master_settings,
            category=CREDIT_HOUR,
        )
        self.leave_rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            employee_can_apply=True,
            admin_can_assign=True,
        )
        self.leave_account = LeaveAccountFactory(
            user=self.created_users[0],
            rule=self.leave_rule,
            balance=2000,
            usable_balance=2000
        )
        UserSupervisor.objects.create(
            user=self.created_users[0],
            supervisor=UserFactory(),
            authority_order=1,
            approve=True,
            deny=True,
            forward=False
        )
        self.shift = WorkShiftFactory(
            name='Standard Shift',
            organization=self.organization,
        )
        self.ias = IndividualAttendanceSettingFactory(
            user=self.created_users[0],
            work_shift=self.shift,
        )
        self.ius = IndividualUserShiftFactory(
            shift=self.shift,
            individual_setting=self.ias,
            applicable_from="1999-10-10"
        )
        self.date_time = datetime.datetime.now() + timedelta(2, 10)
        for day in range(1, 8):
            self.work_day = WorkDayFactory(shift=self.shift, day=day, applicable_from="2021-07-20")
            self.work_day.timings.all().delete()
            self.work_timing = WorkTimingFactory(
                work_day=self.work_day,
            )
        self.url = reverse(
            'api_v1:leave:leave-request-list',

            kwargs={
                'organization_slug': self.organization.slug
            }
        )
        self.payload = {
            'user': self.created_users[0].id,
            'leave_account': self.leave_account.id,
            'start': datetime.date(2023, 3, 13) + timedelta(days=2),
            'end': datetime.date(2023, 3, 13) + timedelta(days=2),
            'balance': 2000,
            'details': "Partial Leave for today",
            'leave_type': "Credit Hour",
            'leave_type_category': "Credit Hour"
        }

    def test_leave_request_without_start_time_and_end_time(self):
        response = self.client.post(
            self.url,
            self.payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            201, response.json()
        )
        self.assertEqual(
            response.json()['balance'], 540.0
        )

    def test_leave_request_without_end_time(self):
        self.payload['start_time'] = self.date_time.strftime('%H:%M:%S')
        payload = self.payload
        response = self.client.post(
            self.url,
            payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.json()['end_time'], ['End Time is required.']
        )

    def test_leave_request_without_start_time(self):
        self.payload['end_time'] = self.date_time.strftime('%H:%M:%S')
        payload = self.payload
        response = self.client.post(
            self.url,
            payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.json()['start_time'], ['Start Time is required.']
        )
