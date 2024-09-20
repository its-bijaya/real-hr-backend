from datetime import time
from django.utils import timezone
from django.urls import reverse
from irhrs.attendance.api.v1.tests.factory import(
    IndividualAttendanceSettingFactory, IndividualUserShiftFactory, 
    WorkDayFactory, WorkShiftFactory, WorkTimingFactory
)
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import(
    LeaveTypeFactory, MasterSettingFactory, LeaveRuleFactory, LeaveAccountFactory

)
from irhrs.leave.constants.model_constants import FULL_DAY
from irhrs.leave.models.request import LeaveRequest
from irhrs.users.models.supervisor_authority import UserSupervisor 

class TestAlternateLeaveAccountsApply(RHRSAPITestCase):
    users = [
        ("admin@gmail.com", "admin", "Male"),
        ("user@gmail.com", "user", "Male"),
        ("supervisor@gmail.com", "supervisor", "Male")
    ]

    organization_name = "aayu"

    def setUp(self):
        super().setUp()
        self.master_settings = MasterSettingFactory(
            organization=self.organization,
            effective_from=get_today() - timezone.timedelta(days=100),
            effective_till=None,
            admin_can_assign=True
        )
        self.leave_type = LeaveTypeFactory(
            master_setting=self.master_settings
        )
        self.sick_leave = LeaveRuleFactory(
            leave_type=self.leave_type,
            employee_can_apply=True,
            admin_can_assign=True,
            can_apply_half_shift=False
        )
        self.penalty_leave = LeaveRuleFactory(
            leave_type=self.leave_type,
            employee_can_apply=True,
            admin_can_assign=True,
            can_apply_half_shift=False
        )
        self.sick_leave_account = LeaveAccountFactory(
            user=self.created_users[1],
            rule=self.sick_leave,
            balance=2,
            usable_balance=2
        )
        self.penalty_leave_account = LeaveAccountFactory(
            user=self.created_users[1],
            rule=self.penalty_leave,
            balance=3,
            usable_balance=3
        )
        self.shift = WorkShiftFactory(
            name="Standard Shift",
            work_days=7,
            organization=self.organization,
        )
        
        UserSupervisor.objects.create(
            user=self.created_users[1],
            supervisor=self.created_users[2],
            authority_order=1,
            approve=True,
            deny=True,
            forward=False
        )
        for day in range(1, 8):
            self.work_day = WorkDayFactory(shift=self.shift, day=day, applicable_from="2021-08-01")
            self.work_day.timings.all().delete()
            self.work_timing = WorkTimingFactory(
                work_day=self.work_day,
                start_time=time(hour=9, minute=0),
                end_time=time(hour=18, minute=0),
                extends=False
            )
        self.ias = IndividualAttendanceSettingFactory(
            user=self.created_users[1],
            work_shift=self.shift
        )
        self.ius = IndividualUserShiftFactory(
            shift=self.shift,
            individual_setting=self.ias,
            applicable_from="2021-08-01"
        )
       
        self.on_behalf_url = reverse(
            "api_v1:leave:request-on-behalf-list",
            kwargs={
                "organization_slug": self.organization.slug
            }
        )
        self.payload = {
            "user": self.created_users[1].id,
            "leave_account": self.sick_leave_account.id,
            "details": "insufficient balance",
            "part_of_day": FULL_DAY,
            "start": "2021-08-20",
            "end": "2021-08-22"
        }

        self.alternate_leave_apply_url = reverse(
            'api_v1:leave:leave-request-alternate-leave-accounts-apply',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )
        multiple_leave_accounts = [
            self.sick_leave_account.id,
            self.penalty_leave_account.id
        ]
        self.alternate_payload = {
            "user": self.created_users[1].id,
            "leave_accounts": multiple_leave_accounts,
            "details": "insufficient balance",
            "part_of_day": FULL_DAY,
            "start_date": "2021-08-20",
            "end_date": "2021-08-22"
        }
    
    def test_leave_request_having_insufficient_leave_balance_as_supervisor(self):
        # Requesting leave on behalf as supervisor having insufficient leave balance
        self.client.force_login(self.created_users[2])
        url = self.on_behalf_url + f"?as=supervisor"
        response = self.client.post(url, self.payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json().get('error_type'), ['insufficient_balance']
        )
        self.assertEqual(
            response.json().get('error'), 
            ['The user does not have sufficient balance, and credit leave is not allowed']
        )
    
    def test_alternate_leave_apply_with_multiple_leave_accounts_as_supervisor(self):
        """
        scenario => alternate leave apply with multiple leave accounts as supervisor 
                    if user has insufficient balance
        result => leave should be requested successfully and approved
        """
        self.client.force_login(self.created_users[2])
        url = self.alternate_leave_apply_url + f"?as=supervisor"
        
        response = self.client.post(url, self.alternate_payload, format="json")
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(
            response.json().get('message'), 'Successfully requested leave.'
        )

        actual_outcome = LeaveRequest.objects.all().values_list('status', flat=True)
        expected_outcome = [item for item in actual_outcome]
        self.assertEqual(
            set(actual_outcome), set(expected_outcome)
        )
        self.assertEqual(actual_outcome.count(), 2)
    
    def test_leave_request_having_insufficient_leave_balance_as_hr(self):
        # Requesting leave on behalf as hr having insufficient leave balance
        self.client.force_login(self.created_users[0])
        url = self.on_behalf_url + f"?as=hr"
        response = self.client.post(url, self.payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json().get('error_type'), ['insufficient_balance']
        )
        self.assertEqual(
            response.json().get('error'), 
            ['The user does not have sufficient balance, and credit leave is not allowed']
        )
    
    def test_alternate_leave_apply_with_multiple_leave_accounts_as_hr(self):
        """
        scenario => alternate leave apply with multiple leave accounts as hr
                    if user has insufficient balance
        result => leave should be requested successsfully and approved
        """
        self.client.force_login(self.created_users[0])
        url = self.alternate_leave_apply_url + f"?as=hr"
        
        response = self.client.post(url, self.alternate_payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json().get('message'), 'Successfully requested leave.'
        )
        actual_outcome = LeaveRequest.objects.all().values_list('status', flat=True)
        expected_outcome = [item for item in actual_outcome]
        self.assertEqual(
            set(actual_outcome), set(expected_outcome)
        )
        self.assertEqual(actual_outcome.count(), 2)
