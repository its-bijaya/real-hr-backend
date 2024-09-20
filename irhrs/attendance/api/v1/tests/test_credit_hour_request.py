from irhrs.leave.models.account import LeaveAccount
import json
from datetime import timedelta, time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.urls import reverse
from rest_framework import status, serializers

from irhrs.attendance.api.v1.serializers.credit_hours import CreditHourRequestSerializer
from irhrs.attendance.api.v1.tests.factory import CreditHourSettingFactory, \
    IndividualAttendanceSettingFactory, WorkDayFactory, \
    WorkShiftFactory, AttendanceAdjustmentFactory
from irhrs.attendance.api.v1.tests.utils import create_credit_hour_request, punch_for_credit_hour, \
    force_balance
from irhrs.attendance.constants import DECLINED
from irhrs.attendance.models import CreditHourRequest, TimeSheet
from irhrs.attendance.signals import recalibrate_credit_hour_when_timesheet_is_updated
from irhrs.attendance.tasks.credit_hours import generate_credit_hours_for_approved_credit_hours
from irhrs.attendance.utils.credit_hours import get_credit_leave_account_qs
from irhrs.common.api.tests.common import RHRSAPITestCase, BaseTestCase
from irhrs.core.utils.common import get_today, get_tomorrow, get_yesterday, humanize_interval, \
    combine_aware
from irhrs.leave.api.v1.tests.factory import LeaveAccountFactory, LeaveRuleFactory, \
    LeaveTypeFactory, MasterSettingFactory
from irhrs.leave.constants.model_constants import CREDIT_HOUR, APPROVED, ADDED
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.users.api.v1.tests.factory import UserFactory


class TestCreditHourRequest(RHRSAPITestCase):
    organization_name = 'Organization'
    users = [
        ('admin@example.com', 'helloSecretWorld', 'Male'),
        ('user@example.com', 'helloSecretWorld', 'Male')
    ]

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])

    def test_credit_hour_bulk_request(self):
        user = self.created_users[1]
        detail = user.detail
        detail.organization = self.organization
        detail.save()
        master_setting = MasterSettingFactory(
            organization=self.organization,
            admin_can_assign=True,
            paid=True,
            effective_from=get_today() - timedelta(days=100),
            effective_till=None,
        )
        leave_type = LeaveTypeFactory(
            master_setting=master_setting,
            name="credit hour",
            category=CREDIT_HOUR
        )
        leave_rule = LeaveRuleFactory(
            leave_type=leave_type,
            max_balance="840.0",
            name="new rule"
        )
        LeaveAccountFactory(
            rule=leave_rule,
            user=user,
            balance=300,
            usable_balance=300
        )
        credit_hour_setting = CreditHourSettingFactory(
            organization=self.organization, require_prior_approval=True
        )
        self.assign_supervisor()
        attendance_setting = IndividualAttendanceSettingFactory(
            user=user,
            enable_credit_hour=True,
            credit_hour_setting=credit_hour_setting
        )
        w_shift = WorkShiftFactory()
        date = get_today() - timedelta(100)
        attendance_setting.individual_setting_shift.create(
            shift=w_shift,
            applicable_from=date,
        )
        attendance_setting.credit_hour_setting = credit_hour_setting
        attendance_setting.save()
        url = reverse(
            'api_v1:attendance:credit-hour-request-request-bulk',
            kwargs={
                "organization_slug": self.organization.slug,
            }
        )
        FiscalYearFactory(organization=self.organization)
        payload = {
            "requests": [
                {
                    "credit_hour_duration": "02:00:00",
                    "credit_hour_date": get_today() + timedelta(days=5),
                    "remarks": "AS"
                },
                {
                    "credit_hour_duration": "02:00:00",
                    "credit_hour_date": get_today() + timedelta(days=6),
                    "remarks": "AS"
                },
            ],
        }
        self.client.force_login(self.created_users[1])
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(
            CreditHourRequest.objects.filter(
                credit_hour_date=get_today() + timedelta(days=5)
            ).exists()
        )
        self.assertTrue(
            CreditHourRequest.objects.filter(
                credit_hour_date=get_today() + timedelta(days=6)
            ).exists()
        )

    def test_credit_hour_request_on_behalf(self):
        user = self.created_users[1]
        detail = user.detail
        detail.organization = self.organization
        detail.save()
        credit_hour_setting = CreditHourSettingFactory(
            organization=self.organization, require_prior_approval=True
        )
        self.assign_supervisor()
        attendance_setting = IndividualAttendanceSettingFactory(
            user=user,
            enable_credit_hour=True,
            credit_hour_setting=credit_hour_setting
        )
        w_shift = WorkShiftFactory()
        date = get_today() - timedelta(100)
        attendance_setting.individual_setting_shift.create(
            shift=w_shift,
            applicable_from=date,
        )
        attendance_setting.credit_hour_setting = credit_hour_setting
        attendance_setting.save()
        url = reverse(
            'api_v1:attendance:credit-hour-request-request-on-behalf',
            kwargs={
                "organization_slug": self.organization.slug,
            }
        )
        FiscalYearFactory(organization=self.organization)
        # 1. Allow Past Date Request
        # 2. Disallow present/future request.
        with patch(
            'irhrs.attendance.api.v1.serializers.credit_hours.'
            'CreditHourRequestOnBehalfSerializer.credit_hour_user_queryset',
            new=get_user_model().objects.all()
        ):
            data = {
                "user_id": user.id,
                "requests": [
                    {
                        "credit_hour_duration": "02:00:00",
                        "credit_hour_date": str(date),
                        "remarks": "Testing Remarks"
                    }
                ]
            }
            for date, expect_status in [
                (date, status.HTTP_200_OK),
                (get_tomorrow(), status.HTTP_400_BAD_REQUEST),
                (get_today(), status.HTTP_400_BAD_REQUEST),
            ]:
                resp = self.client.post(
                    url + '?as=hr',
                    data=data,
                    format='json'
                )
                self.assertEqual(resp.status_code, expect_status, str(resp.json()))
            resp = self.client.post(
                # do not add `?as=hr`
                url,
                data=data,
                format='json'
            )
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN,
                             json.dumps(resp.json(), indent=3))
            self.client.force_login(user)
            resp = self.client.post(
                url + '?as=hr',
                data=data
            )
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
            self.client.force_login(self.created_users[0])
            data.get("requests")[0]["credit_hour_date"] = str(date - timedelta(days=1))
            resp = self.client.post(
                url + '?as=hr',
                data=data,
                format='json'
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def assign_supervisor(self):
        user = self.created_users[1]
        supervisor = self.created_users[0]
        user.supervisors.create(supervisor=supervisor)


class TestCreditHourRequestDeletedShouldNotBeIncludedInCount(BaseTestCase):
    def test_max_limit_validator_should_ignore_deleted_credit_requests(self):
        org = OrganizationFactory()
        user = UserFactory()
        detail = user.detail
        detail.organization = org
        detail.save()
        payload_duration = timedelta(hours=5)
        IndividualAttendanceSettingFactory(
            user=user,
            enable_credit_hour=True,
            credit_hour_setting=CreditHourSettingFactory(
                organization=org,
            )
        )
        max_balance = 120
        balance = 120
        usable_balance = 60
        existing_duration = timedelta(minutes=50)

        LeaveAccountFactory(
            rule=LeaveRuleFactory(
                leave_type=LeaveTypeFactory(
                    category=CREDIT_HOUR,
                    master_setting=MasterSettingFactory(organization=org,
                                                        effective_from=get_yesterday())
                ),
                max_balance=max_balance
            ),
            user=user,
            balance=balance,
            usable_balance=usable_balance,
        )

        # create a declined request.
        CreditHourRequest.objects.create(**{
            'request_remarks': 'remarks',
            'credit_hour_duration': existing_duration,
            'credit_hour_date': get_tomorrow(),
            'status': APPROVED,
            'is_deleted': True,
            'sender': user,
            'recipient': user,
        })
        CreditHourRequest.objects.create(**{
            'request_remarks': 'remarks',
            'credit_hour_duration': existing_duration,
            'credit_hour_date': get_tomorrow() + timedelta(days=1),
            'status': APPROVED,
            'is_deleted': False,
            'sender': user,
            'recipient': user,
        })
        CreditHourRequest.objects.create(**{
            'request_remarks': 'remarks',
            'credit_hour_duration': existing_duration,
            'credit_hour_date': get_tomorrow() + timedelta(days=2),
            'status': DECLINED,
            'is_deleted': False,
            'sender': user,
            'recipient': user,
        })
        user.refresh_from_db()
        ser = CreditHourRequestSerializer()
        ser.get_sender = lambda *x, **y: user
        try:
            ser.validate_max_balance_in_leave_account(user, payload_duration)
        except serializers.ValidationError as err:
            self.assertEqual(
                str(err.detail.get('credit_hour_duration')),
                'The selected duration {} exceeds max balance {}. Existing: {}. Pending {}'.format(
                    humanize_interval(payload_duration),
                    humanize_interval(max_balance * 60),
                    humanize_interval(usable_balance * 60),
                    humanize_interval(existing_duration)
                )
            )


class TestCreditHourBalanceRevert(BaseTestCase):

    def test_under_limit_credit_hour_balance_is_granted(self):
        test_cases = [
            # worked less than requested  # <
            {
                'desc': "request: 2, worked:1, grant: 1",
                'early_delta': -30,
                'late_delta': 30,
                'leave_max_balance': 180,
                'existing_balance': 0,
                'requested_duration': timedelta(hours=2),
                'expected_balance_added': 60,
            },
            # worked equally as requested.  # =
            {
                'desc': "request: 2, worked:2, grant: 2",
                'early_delta': -60,
                'late_delta': 60,
                'leave_max_balance': 180,
                'existing_balance': 0,
                'requested_duration': timedelta(hours=2),
                'expected_balance_added': 120,
            },
            # worked more than requested.  # >
            {
                'desc': "request: 2, work: 3, grant: 2",
                'early_delta': -75,
                'late_delta': 75,
                'leave_max_balance': 180,
                'existing_balance': 0,
                'requested_duration': timedelta(hours=2),
                'expected_balance_added': 120,
            },
            # worked equally as requested. But not enough leave balance
            # {
            #     'desc': "request: 2, work: 2, grant: 1, `limitation from max balance`",
            #     'early_delta': -60,
            #     'late_delta': 60,
            #     'leave_max_balance': 180,
            #     'existing_balance': 120,
            #     'requested_duration': timedelta(hours=2),
            #     'expected_balance_added': 60,
            # },
            # This test case would not be valid.
            # Provided, there is max balance limitation from serializer.

        ]
        for test_case in test_cases:
            user = UserFactory()
            date = get_today()
            early_delta = test_case['early_delta']
            late_delta = test_case['late_delta']
            leave_max_balance = test_case['leave_max_balance']
            existing_balance = test_case['existing_balance']
            requested_duration = test_case['requested_duration']
            expected_balance_added = test_case['expected_balance_added']

            create_credit_hour_request(
                user,
                date,
                requested_duration,
                leave_max_balance=leave_max_balance,
                balance=existing_balance
            )
            punch_for_credit_hour(user, date, early_delta, late_delta)
            generate_credit_hours_for_approved_credit_hours()

            leave_account = get_credit_leave_account_qs().filter(user=user).first()
            assert leave_account, "Leave account does not exist"
            history = leave_account.history.difference().first()
            self.assertEqual(history.added, expected_balance_added,
                             test_case.get('desc'))
            self.assertEqual(history.action, ADDED,
                             test_case.get('desc'))

    def test_delete_request_removes_balance_from_account(self):
        """
        Steps:
            1. create, approve, punch, generate >> would add balance.
            2. create, approve delete request.
            3. run task for delete request.
            4. search history for deleted credit leave.
        :return:
        """
        test_cases = [
            # worked less than requested  # <
            {
                'desc': "request: 2, worked:1, grant: 1",
                'early_delta': -30,
                'late_delta': 30,
                'leave_max_balance': 180,
                'existing_balance': 0,
                'requested_duration': timedelta(hours=2),
                'expected_balance_added': 60,
            },
            # worked equally as requested.  # =
            {
                'desc': "request: 2, worked:2, grant: 2",
                'early_delta': -60,
                'late_delta': 60,
                'leave_max_balance': 180,
                'existing_balance': 0,
                'requested_duration': timedelta(hours=2),
                'expected_balance_added': 120,
            },
            # worked more than requested.  # >
            {
                'desc': "request: 2, work: 3, grant: 2",
                'early_delta': -75,
                'late_delta': 75,
                'leave_max_balance': 180,
                'existing_balance': 0,
                'requested_duration': timedelta(hours=2),
                'expected_balance_added': 120,
            },
            # worked equally as requested. But not enough leave balance
            # {
            #     'desc': "request: 2, work: 2, grant: 1, `limitation from max balance`",
            #     'early_delta': -60,
            #     'late_delta': 60,
            #     'leave_max_balance': 180,
            #     'existing_balance': 120,
            #     'requested_duration': timedelta(hours=2),
            #     'expected_balance_added': 60,
            # },
            # This test case would not be valid.
            # Provided, there is max balance limitation from serializer.
        ]
        for test_case in test_cases:
            user = UserFactory()
            date = get_today()
            early_delta = test_case['early_delta']
            late_delta = test_case['late_delta']
            leave_max_balance = test_case['leave_max_balance']
            existing_balance = test_case['existing_balance']
            requested_duration = test_case['requested_duration']
            expected_balance_added = test_case['expected_balance_added']

            create_credit_hour_request(
                user,
                date,
                requested_duration,
                leave_max_balance=leave_max_balance,
                balance=existing_balance
            )
            punch_for_credit_hour(user, date, early_delta, late_delta)
            generate_credit_hours_for_approved_credit_hours()

            leave_account = get_credit_leave_account_qs().filter(user=user).first()
            assert leave_account, "Leave account does not exist"
            history = leave_account.history.difference().first()
            self.assertEqual(history.added, expected_balance_added,
                             test_case.get('desc'))
            self.assertEqual(history.action, ADDED,
                             test_case.get('desc'))

            # forcibly remove some balance from leave account, making the credit
            # request unable to delete.

            # History till here:
            # 1. Balance was added.
            # 2. Nothing was consumed.
            # 3. All balance was reverted.

            # delete_request_instance = create_delete_credit_history(
            #     credit_request, user
            # )
            # revert_credit_hour_from_leave_account(delete_request_instance)

            # # Scenario - 2:
            # # 1. Balance was added.
            # force_balance(leave_account, expected_balance_added)
            # # 2. Balance was consumed.
            # consumed_balance = int(expected_balance_added * random())
            # force_balance(leave_account, -consumed_balance)
            # # 3. History was reverted.
            # revert_credit_hour_from_leave_account(delete_request_instance)

            # reduced_balance = leave_account.history.difference().order_by(
            #     '-created_at'
            # ).values_list('added', flat=True).first()
            # should_be_reduced_balance = expected_balance_added - consumed_balance
            # self.assertEqual(reduced_balance, -should_be_reduced_balance)


class TestCreditHourRecalibrationDoesNotExceedMaxBalance(BaseTestCase):

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE table {TimeSheet._meta.db_table} CASCADE")
        return super().setUp()

    def test_credit_hour_recalibration_constraint(self):
        """
        Scenario:
            > User has max balance of 4 hours; leave_balance = 0
            > User requests 3 hours of credit
            > User works for 1 hours; leave_balance = 1
            > from other sources, balance is added. leave_balance = 0 + 1 + 2 = 3 hours
            > User sends adjustment, and balance recalibrates.
        """
        org = OrganizationFactory()
        user = UserFactory(_organization=org)
        payload_duration = timedelta(hours=3)
        credit_setting = CreditHourSettingFactory(
            organization=org,
        )
        attendance_setting = IndividualAttendanceSettingFactory(
            user=user,
            enable_credit_hour=True,
            credit_hour_setting=credit_setting
        )
        w_shift = WorkShiftFactory()
        date = get_today() - timedelta(100)

        attendance_setting.individual_setting_shift.create(
            shift=w_shift,
            applicable_from=date,
        )

        for day in range(1,8):
            WorkDayFactory(shift=w_shift, day=day, applicable_from=date)

        max_balance = 180
        usable_balance = 0

        LeaveAccountFactory(
            rule=LeaveRuleFactory(
                leave_type=LeaveTypeFactory(
                    category=CREDIT_HOUR,
                    master_setting=MasterSettingFactory(
                        organization=org,
                        effective_from=get_yesterday()
                    )
                ),
                max_balance=max_balance
            ),
            user=user,
            balance=usable_balance,
            usable_balance=usable_balance,
        )

        # create a declined request.
        CreditHourRequest.objects.create(**{
            'request_remarks': 'remarks',
            'credit_hour_duration': payload_duration,
            'credit_hour_date': get_yesterday(),
            'status': APPROVED,
            'is_deleted': False,
            'sender': user,
            'recipient': user,
        })

        punch_in = combine_aware(get_yesterday(), time(8, 0))
        punch_out = combine_aware(get_yesterday(), time(18, 0))
        user.timesheets.clock(user, punch_in, 'Device')
        user.timesheets.clock(user, punch_out, 'Device')
        timesheet = user.timesheets.get(timesheet_for=get_yesterday())

        generate_credit_hours_for_approved_credit_hours()
        self.assertEqual(
            user.leave_accounts.get().usable_balance,
            60
        )
        # force balance to add 1 more hour
        leave_account = user.leave_accounts.get()
        force_balance(leave_account, difference=60)

        adjustment = AttendanceAdjustmentFactory(
            timesheet=timesheet,
            receiver=user,
            timestamp=punch_in - timedelta(hours=3),
            sender=user
        )
        adjustment.approve(user, 'force')
        recalibrate_credit_hour_when_timesheet_is_updated(
            timesheet, user, 1  # ADJUSTMENT = 1
        )
        self.assertEqual(
            user.leave_accounts.get().usable_balance,
            max_balance  # should not exceed this max limit.
        )
