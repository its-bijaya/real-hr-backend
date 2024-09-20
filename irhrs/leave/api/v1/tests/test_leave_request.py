from datetime import time, timedelta

from django.utils import timezone
from django.urls import reverse
from rest_framework import status

from irhrs.core.utils.common import get_today
from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    WorkShiftFactory, IndividualUserShiftFactory, WorkDayFactory, WorkTimingFactory
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.leave.models import LeaveRequest
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, LeaveAccountFactory
from irhrs.leave.constants.model_constants import FULL_DAY
from irhrs.leave.constants.model_constants import (
    INCLUDE_HOLIDAY_AND_OFF_DAY,
    EXCLUDE_HOLIDAY_AND_OFF_DAY
)
from irhrs.leave.models.rule import PriorApprovalRule
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models import UserSupervisor
from irhrs.leave.constants.model_constants import (
    INSUFFICIENT_BALANCE
)


class TestLeaveRequests(RHRSAPITestCase):
    organization_name = 'Google'
    users = [
        ('normal@email.com', 'password', 'Male'),
    ]

    def setUp(self):
        super().setUp()
        self.master_settings = MasterSettingFactory(
            organization=self.organization,
            half_shift_leave=True,
            effective_from=get_today() - timezone.timedelta(days=30),
            effective_till=get_today() + timezone.timedelta(days=30),
            require_prior_approval=True
        )
        self.leave_type = LeaveTypeFactory(master_setting=self.master_settings)
        self.inclusive_sick_leave = LeaveRuleFactory(
            leave_type=self.leave_type,
            employee_can_apply=True,
            can_apply_half_shift=True,
            inclusive_leave=INCLUDE_HOLIDAY_AND_OFF_DAY
        )
        self.exclusive_sick_leave = LeaveRuleFactory(
            leave_type=self.leave_type,
            employee_can_apply=True,
            can_apply_half_shift=True,
            inclusive_leave=EXCLUDE_HOLIDAY_AND_OFF_DAY,
        )
        self.inclusive_sick_leave_account = LeaveAccountFactory(
            user=self.created_users[0],
            rule=self.inclusive_sick_leave,
            balance=3,
            usable_balance=3
        )
        self.exclusive_sick_leave_account = LeaveAccountFactory(
            user=self.created_users[0],
            rule=self.exclusive_sick_leave,
            balance=3,
            usable_balance=3
        )
        self.shift = WorkShiftFactory(
            name="Day Shift",
            work_days=7,
            organization=self.organization,
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
            self.work_day = WorkDayFactory(shift=self.shift, day=day, applicable_from="2021-07-01")
            self.work_day.timings.all().delete()
            self.work_timing = WorkTimingFactory(
                work_day=self.work_day,
                start_time=time(hour=9, minute=0),
                end_time=time(hour=18, minute=0),
                extends=False
            )
        self.ias = IndividualAttendanceSettingFactory(
            user=self.created_users[0],
            work_shift=self.shift
        )
        self.ius = IndividualUserShiftFactory(
            shift=self.shift,
            individual_setting=self.ias,
            applicable_from="2021-07-01"
        )
        self.prior_approval_leave_rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            require_prior_approval=True,
            employee_can_apply=True
        )
        self.prior_approval_leave_account = LeaveAccountFactory(
            rule=self.prior_approval_leave_rule, user=self.created_users[0],

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
    def leave_request_data(self):
        return {
            'start': get_today() + timedelta(days=1),
            'end': get_today() + timedelta(days=1),
            'details': "Sick leave",
            'part_of_day': FULL_DAY,
            'leave_account': self.prior_approval_leave_account.id
        }

    @property
    def prior_rules(self):
        return [
            PriorApprovalRule(
                rule=self.prior_approval_leave_rule,
                prior_approval_request_for=2,
                prior_approval=2,
                prior_approval_unit="Days"
            ),
            PriorApprovalRule(
                rule=self.prior_approval_leave_rule,
                prior_approval_request_for=5,
                prior_approval=5,
                prior_approval_unit="Days"
            )
        ]
    
    def test_leave_request_from_multiple_leave_accounts(self):
        leave_accounts = [
            self.exclusive_sick_leave_account.id,
            self.inclusive_sick_leave_account.id
        ]

        ten_day_leave_payload = {
            "details": "6 days leave",
            "part_of_day": FULL_DAY,
            "start_date": "2021-07-20",
            "end_date": "2021-07-25",
            'leave_accounts': leave_accounts
        }
        self.leave_req_with_alt_accounts = reverse(
            'api_v1:leave:leave-request-alternate-leave-accounts-apply',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )
        response = self.client.post(
            self.leave_req_with_alt_accounts,
            ten_day_leave_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            LeaveRequest.objects.all().count(),
            2
        )
        self.assertEqual(
            LeaveRequest.objects.all().count(),
            2
        )
        self.assertEqual(
            LeaveRequest.objects.filter(balance=3).count(),
            2
        )

    def test_leave_request_with_insufficient_balance_from_multiple_leave_accounts(self):
        leave_accounts = [
            self.exclusive_sick_leave_account.id,
            self.inclusive_sick_leave_account.id
        ]

        ten_day_leave_payload = {
            "details": "6 days leave",
            "part_of_day": FULL_DAY,
            "start_date": "2021-07-20",
            "end_date": "2021-07-28",
            'leave_accounts': leave_accounts
        }
        self.leave_req_with_alt_accounts = reverse(
            'api_v1:leave:leave-request-alternate-leave-accounts-apply',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )
        response = self.client.post(
            self.leave_req_with_alt_accounts,
            ten_day_leave_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json().get('error_type'),
            [INSUFFICIENT_BALANCE]
        )
        self.assertEqual(
            LeaveRequest.objects.all().count(),
            0
        )

    def test_leave_request_with_smaller_end_date_than_start_date(self):
        leave_accounts = [
            self.exclusive_sick_leave_account.id,
            self.inclusive_sick_leave_account.id
        ]

        ten_day_leave_payload = {
            "details": "6 days leave",
            "part_of_day": FULL_DAY,
            "start_date": "2021-07-10",
            "end_date": "2021-07-05",
            'leave_accounts': leave_accounts
        }
        self.leave_req_with_alt_accounts = reverse(
            'api_v1:leave:leave-request-alternate-leave-accounts-apply',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )
        response = self.client.post(
            self.leave_req_with_alt_accounts,
            ten_day_leave_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json().get('non_field_errors'),
            ['Start date must be smaller than end date.']
        )

    def test_two_days_leave_request_for_prior_approval(self):
        start = (get_today() + timedelta(days=2)).strftime("%Y-%m-%d")
        end = (get_today() + timedelta(days=3)).strftime("%Y-%m-%d")
        two_days_leave_payload = {
            "start": start,
            "end": end,
            "details": "2 days leave",
            "part_of_day": FULL_DAY,
            'leave_account': self.prior_approval_leave_account.id
        }

        PriorApprovalRule.objects.bulk_create(self.prior_rules)

        response = self.client.post(
            self.leave_request_url, two_days_leave_payload, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )

        self.assertEqual(
            response.json().get('balance'), 2.0
        )

    def test_invalid_two_days_leave_request_for_prior_approval(self):
        start = get_today().strftime("%Y-%m-%d")
        end = (get_today() + timedelta(days=3)).strftime("%Y-%m-%d")
        two_days_leave_payload = {
            "start": start,
            "end": end,
            "details": "2 days leave",
            "part_of_day": FULL_DAY,
            'leave_account': self.prior_approval_leave_account.id
        }

        PriorApprovalRule.objects.bulk_create(self.prior_rules)
        response = self.client.post(
            self.leave_request_url, two_days_leave_payload, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data
        )

        self.assertEqual(
            response.json()['non_field_errors'][0],
            'The leave request must be sent 2 days before.'
        )

    def test_five_days_leave_request_prior_approval(self):
        start = (get_today() + timedelta(days=5)).strftime("%Y-%m-%d")
        end = (get_today() + timedelta(days=9)).strftime("%Y-%m-%d")
        five_days_leave_payload = {
            "start": start,
            "end": end,
            "details": "5 days leave",
            "part_of_day": FULL_DAY,
            'leave_account': self.prior_approval_leave_account.id
        }

        PriorApprovalRule.objects.bulk_create(self.prior_rules)

        response = self.client.post(
            self.leave_request_url, five_days_leave_payload, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )

        self.assertEqual(
            response.json().get('balance'), 5.0
        )

    def test_invalid_five_days_leave_request_for_prior_approval(self):
        start = get_today().strftime("%Y-%m-%d")
        end = (get_today() + timedelta(days=5)).strftime("%Y-%m-%d")
        five_days_leave_payload = {
            "start": start,
            "end": end,
            "details": "5 days leave",
            "part_of_day": FULL_DAY,
            'leave_account': self.prior_approval_leave_account.id
        }

        PriorApprovalRule.objects.bulk_create(self.prior_rules)

        response = self.client.post(
            self.leave_request_url, five_days_leave_payload, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data
        )

        self.assertEqual(
            response.json()['non_field_errors'][0],
            'The leave request must be sent 5 days before.'
        )
        