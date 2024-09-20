from datetime import time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    WorkShiftFactory2
from irhrs.attendance.api.v1.tests.utils import force_balance
from irhrs.attendance.constants import HOLIDAY, WORKDAY, OFFDAY
from irhrs.attendance.models import IndividualUserShift
from irhrs.attendance.tasks.timesheets import populate_timesheet_for_user
from irhrs.common.api.tests.common import RHRSAPITestCase, BaseTestCase
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import LeaveAccountFactory, LeaveRuleFactory, \
    LeaveTypeFactory, MasterSettingFactory, LeaveRequestFactory
from irhrs.leave.constants.model_constants import APPROVED, INCLUDE_HOLIDAY_AND_OFF_DAY
from irhrs.leave.models import LeaveAccount, LeaveRequest
from irhrs.leave.models.account import AdjacentTimeSheetOffdayHolidayPenalty
from irhrs.leave.models.rule import AdjacentLeaveReductionTypes, PriorApprovalRule
from irhrs.leave.utils.leave_request import apply_leave_on_behalf_by_system_if_applicable
from irhrs.notification.models import Notification
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models import UserSupervisor

USER = get_user_model()


class TestOfflineLeaveRequest(RHRSAPITestCase):
    organization_name = 'ALPL'
    users = [
        ('hr@email.com', 'password', 'Female'),
        ('supervisorone@email.com', 'password', 'Female'),
        ('supervisortwo@email.com', 'password', 'Male'),
        ('normal@email.com', 'password', 'Male'),
    ]

    @property
    def normal(self):
        return USER.objects.get(email='normal@email.com')

    @property
    def supervisor1(self):
        return USER.objects.get(email='supervisorone@email.com')

    @property
    def supervisor2(self):
        return USER.objects.get(email='supervisortwo@email.com')

    def setUp(self):
        super().setUp()
        self.client.login(username=self.users[0][0], password=self.users[0][1])
        self.master_settings = MasterSettingFactory(
            organization=self.organization,
            occurrences=True,
            depletion_required=True,
            require_prior_approval=True,
            require_time_period=True,
            require_document=True,
            continuous=True,
            leave_limitations=True
        )
        self.leave_type = LeaveTypeFactory(master_setting=self.master_settings)
        IndividualAttendanceSettingFactory(
            user=self.normal
        )

    def url(self):
        return reverse(
            'api_v1:leave:request-on-behalf-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def payload(self, account):
        end_date = (get_today(with_time=True) + timedelta(days=10)).date()
        return {
            "user": self.normal.id,
            "leave_account": account.id,
            "details": "test for supervisor notification",
            "start": get_today() + timedelta(days=3),
            "end": end_date
        }

    def assign_supervisor(self):
        supervisors = [
            UserSupervisor(
                user=self.normal,
                supervisor=self.supervisor1,
                authority_order=1,
                approve=True, deny=True, forward=False
            ),
            UserSupervisor(
                user=self.normal,
                supervisor=self.supervisor2,
                authority_order=2,
                approve=True, deny=True, forward=False
            )
        ]
        UserSupervisor.objects.bulk_create(supervisors)

    '''
        Testing validation while HR request leave on behalf of user.
        Validation list tested:
            1. Require Document
            2. Occurrence/Frequencies
            3. Leave Limitations
            4. Require Time - Period
            5. Require Prior Approval
            6. Continuous
            7. Depletion Required
    '''
    def test_start_date_greater_than_end_date(self):
        rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            is_paid=False,
            employee_can_apply=False,
            admin_can_assign=False,
            require_prior_approval=False,
        )
        self.assign_supervisor()
        account = LeaveAccountFactory(user=self.normal, rule=rule)
        payload = self.payload(account)
        start = get_today()
        payload['start'] = start.isoformat()
        payload['end'] = (start - timedelta(days=1)).isoformat()
        with patch(
            'irhrs.leave.utils.balance.get_leave_balance', return_value=(5, None)
        ), patch(
            'irhrs.leave.utils.leave_request.validate_can_request_assign', return_value=True
        ):
            bad_response = self.client.post(self.url(), payload)
        self.assertEqual(bad_response.status_code, 400)
        error = {"non_field_errors":["Start date must be smaller than end date."]}
        self.assertEqual(bad_response.json(), error)

    def test_require_docs_validation(self):
        rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            is_paid=False,
            employee_can_apply=False,
            admin_can_assign=False,
            require_prior_approval=False,
            require_docs=True,
            require_docs_for=2,
        )
        account = LeaveAccountFactory(user=self.normal, rule=rule)
        with patch(
            'irhrs.leave.utils.leave_request.get_shift_start',
            return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.leave_request.get_shift_end', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.balance.get_leave_balance', return_value=(5, None)
        ), patch(
            'irhrs.leave.utils.leave_request.validate_can_request_assign', return_value=True
        ), patch(
            'irhrs.leave.utils.balance.validate_sufficient_leave_balance', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_sheet.create_leave_sheets', return_value=None
        ):
            self.assign_supervisor()
            url_with_hr_params = self.url() + '?as=hr&bypass_validation=True'
            bad_response = self.client.post(
                    self.url(),
                    data=self.payload(account)
                )
            self.assertEqual(
                bad_response.status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                bad_response.json().get('non_field_errors'),
                ['A valid attachment is required to apply for this leave for more than 2.0 balance']
            )
            response = self.client.post(
                    url_with_hr_params,
                    data=self.payload(account)
                )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED
            )

    def test_occurrence_validation(self):
        rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            is_paid=False,
            employee_can_apply=False,
            admin_can_assign=False,
            require_prior_approval=False,
            limit_leave_occurrence=2,
            limit_leave_occurrence_duration=3,
            limit_leave_occurrence_duration_type="Months"
        )
        account = LeaveAccountFactory(user=self.normal, rule=rule)
        for i in range(0, 3):
            LeaveRequestFactory(
                user=self.normal,
                recipient=self.supervisor1,
                leave_rule=rule,
                leave_account=account,
                start=timezone.now() + timezone.timedelta(days=i),
                end=timezone.now() + timezone.timedelta(days=i + 1),
                balance=1
            )
        with patch(
            'irhrs.leave.utils.leave_request.get_shift_start',
            return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.leave_request.get_shift_end', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.balance.get_leave_balance', return_value=(5, None)
        ), patch(
            'irhrs.leave.utils.leave_request.validate_can_request_assign', return_value=True
        ), patch(
            'irhrs.leave.utils.balance.validate_sufficient_leave_balance', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_sheet.create_leave_sheets', return_value=None
        ):
            self.assign_supervisor()
            url_with_hr_params = self.url() + '?as=hr&bypass_validation=True'
            bad_response = self.client.post(
                    self.url(),
                    data=self.payload(account)
                )
            self.assertEqual(
                bad_response.status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                bad_response.json().get('non_field_errors'),
                ['The leave for this range already exists']
            )
            response = self.client.post(
                    url_with_hr_params,
                    data=self.payload(account)
                )
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                bad_response.json().get('non_field_errors'),
                ['The leave for this range already exists']
            )

    def test_continuous_leave_validation(self):
        rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            is_paid=False,
            employee_can_apply=False,
            admin_can_assign=False,
            require_prior_approval=False,
            maximum_continuous_leave_length=2.0,
            minimum_continuous_leave_length=1.0,
        )
        account = LeaveAccountFactory(user=self.normal, rule=rule)
        with patch(
            'irhrs.leave.utils.leave_request.get_shift_start',
            return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.leave_request.get_shift_end', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.balance.get_leave_balance', return_value=(5, None)
        ), patch(
            'irhrs.leave.utils.leave_request.validate_can_request_assign', return_value=True
        ), patch(
            'irhrs.leave.utils.balance.validate_sufficient_leave_balance', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_sheet.create_leave_sheets', return_value=None
        ):
            self.assign_supervisor()
            url_with_hr_params = self.url() + '?as=hr&bypass_validation=True'
            bad_response = self.client.post(
                    self.url(),
                    data=self.payload(account)
                )
            self.assertEqual(
                bad_response.status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                bad_response.json().get('non_field_errors'),
                ['This leave request consumes 5. This leave allows leave between 1.0 and 2.0.']
            )
            response = self.client.post(
                    url_with_hr_params,
                    data=self.payload(account)
                )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED
            )

    def test_limit_limitation_validation(self):
        rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            is_paid=False,
            employee_can_apply=False,
            admin_can_assign=False,
            require_prior_approval=False,
            limit_leave_to=2.0,
            limit_leave_duration=3,
            limit_leave_duration_type="Months"
        )
        account = LeaveAccountFactory(user=self.normal, rule=rule)
        with patch(
            'irhrs.leave.utils.leave_request.get_shift_start',
            return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.leave_request.get_shift_end', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.balance.get_leave_balance', return_value=(5, None)
        ), patch(
            'irhrs.leave.utils.leave_request.validate_can_request_assign', return_value=True
        ), patch(
            'irhrs.leave.utils.balance.validate_sufficient_leave_balance', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_sheet.create_leave_sheets', return_value=None
        ):
            self.assign_supervisor()
            url_with_hr_params = self.url() + '?as=hr&bypass_validation=True'
            bad_response = self.client.post(
                    self.url(),
                    data=self.payload(account)
                )
            self.assertEqual(
                bad_response.status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                bad_response.json().get('non_field_errors'),
                ['The total allowed balance in 3 Months is 2.0. You cannot apply']
            )
            response = self.client.post(
                    url_with_hr_params,
                    data=self.payload(account)
                )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED
            )

    def test_require_time_period_validation(self):
        rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            is_paid=False,
            employee_can_apply=False,
            admin_can_assign=False,
            require_prior_approval=False,
            start_date=get_today() + timedelta(days=8),
            end_date=get_today() - timedelta(days=8),
        )
        account = LeaveAccountFactory(user=self.normal, rule=rule)
        with patch(
            'irhrs.leave.utils.leave_request.get_shift_start',
            return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.leave_request.get_shift_end', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.balance.get_leave_balance', return_value=(5, None)
        ), patch(
            'irhrs.leave.utils.leave_request.validate_can_request_assign', return_value=True
        ), patch(
            'irhrs.leave.utils.balance.validate_sufficient_leave_balance', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_sheet.create_leave_sheets', return_value=None
        ):
            self.assign_supervisor()
            url_with_hr_params = self.url() + '?as=hr&bypass_validation=True'
            bad_response = self.client.post(
                    self.url(),
                    data=self.payload(account)
                )
            self.assertEqual(
                bad_response.status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                bad_response.json().get('non_field_errors'),
                [[f'The leave must be applied after {get_today() + timedelta(days=8)}',
                 f'The leave must be applied before {get_today() - timedelta(days=8)}']]
            )
            response = self.client.post(
                    url_with_hr_params,
                    data=self.payload(account)
                )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED
            )

    def test_require_prior_approval_validation(self):
        rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            is_paid=False,
            employee_can_apply=False,
            admin_can_assign=False,
            require_prior_approval=True
        )
        PriorApprovalRule.objects.create(
            rule=rule,
            prior_approval_request_for=2,
            prior_approval=2,
            prior_approval_unit="Days"
        )
        account = LeaveAccountFactory(user=self.normal, rule=rule)
        with patch(
            'irhrs.leave.utils.leave_request.get_shift_start',
            return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.leave_request.get_shift_end', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.balance.get_leave_balance', return_value=(5, None)
        ), patch(
            'irhrs.leave.utils.leave_request.validate_can_request_assign', return_value=True
        ), patch(
            'irhrs.leave.utils.balance.validate_sufficient_leave_balance', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_sheet.create_leave_sheets', return_value=None
        ):
            self.assign_supervisor()
            url_with_hr_params = self.url() + '?as=hr&bypass_validation=True'
            bad_response = self.client.post(
                    self.url(),
                    data=self.payload(account)
                )
            self.assertEqual(
                bad_response.status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                bad_response.json().get('non_field_errors'),
                ['The leave request must be sent 2 days before.']
            )
            data = self.payload(account)
            data.update({
                "start_time": time(0, 0),
                "end_time": time(0, 0)
            })
            response = self.client.post(
                    url_with_hr_params,
                    data=data
                )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED
            )

    def test_depletion_required_validation(self):
        leave_type = LeaveTypeFactory(master_setting=self.master_settings)
        leave_type1 = LeaveTypeFactory(master_setting=self.master_settings)
        rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            is_paid=False,
            employee_can_apply=False,
            admin_can_assign=False,
            require_prior_approval=False,
            depletion_required=True,
            depletion_leave_types=leave_type
        )
        rule1 = LeaveRuleFactory(
            leave_type=leave_type,
            is_paid=False,
            employee_can_apply=False,
            admin_can_assign=False,
            require_prior_approval=False,
            depletion_required=True,
            depletion_leave_types=leave_type1
        )
        account = LeaveAccountFactory(user=self.normal, rule=rule)
        account1 = LeaveAccountFactory(user=self.normal, rule=rule1)
        with patch(
            'irhrs.leave.utils.leave_request.get_shift_start',
            return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.leave_request.get_shift_end', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.balance.get_leave_balance', return_value=(5, None)
        ), patch(
            'irhrs.leave.utils.leave_request.validate_can_request_assign', return_value=True
        ), patch(
            'irhrs.leave.utils.balance.validate_sufficient_leave_balance', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_sheet.create_leave_sheets', return_value=None
        ):
            self.assign_supervisor()
            url_with_hr_params = self.url() + '?as=hr&bypass_validation=True'
            bad_response = self.client.post(
                    self.url(),
                    data=self.payload(account)
                )
            self.assertEqual(
                bad_response.status_code,
                status.HTTP_400_BAD_REQUEST
            )
            depletion_leave_types = LeaveAccount.objects.last().rule.depletion_leave_types.all()
            name = ', '.join(
                list(depletion_leave_types.values_list('name', flat=True))
            )
            self.assertEqual(
                bad_response.json().get('non_field_errors'),
                [f'The leave request on this account requires balance from the following '
                 f'accounts to be consumed: {name}']
            )
            response = self.client.post(
                    url_with_hr_params,
                    data=self.payload(account)
                )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED
            )

    def test_offline_attendance_notification(self):
        rule = LeaveRuleFactory(leave_type=self.leave_type)
        account = LeaveAccountFactory(user=self.normal, rule=rule)
        with patch(
            'irhrs.leave.utils.leave_request.get_shift_start', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.leave_request.get_shift_end', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.balance.get_leave_balance', return_value=(0, None)
        ), patch(
            'irhrs.leave.utils.leave_request.validate_can_request_assign', return_value=True
        ), patch(
            'irhrs.leave.utils.balance.validate_sufficient_leave_balance', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_sheet.create_leave_sheets', return_value=None
        ):
            url_with_hr_params = self.url() + '?as=hr&bypass_validation=True'
            self.assign_supervisor()
            self.client.post(
                url_with_hr_params,
                data=self.payload(account)
            )
            text = f"{self.admin} has approved {self.normal}'s leave from {get_today()} to {get_today()}"
            supervisor1 = Notification.objects.filter(
                recipient=self.supervisor1,
                text=text
            ).first().recipient
            supervisor2 = Notification.objects.filter(
                recipient=self.supervisor2,
                text=text
            ).first().recipient
            self.assertEqual(supervisor1, self.supervisor1)
            self.assertEqual(supervisor2, self.supervisor2)


class TestOfflineLeaveRequestForSupervisor(RHRSAPITestCase):
    organization_name = 'ALPL'
    users = [
        ('hr@email.com', 'password', 'Female'),
        ('supervisorone@email.com', 'password', 'Female'),
        ('supervisortwo@email.com', 'password', 'Male'),
        ('supervisorthree@email.com', 'password', 'Male'),
        ('normal@email.com', 'password', 'Male'),
    ]

    @property
    def normal(self):
        return USER.objects.get(email='normal@email.com')

    @property
    def supervisor1(self):
        return USER.objects.get(email='supervisorone@email.com')

    @property
    def supervisor2(self):
        return USER.objects.get(email='supervisortwo@email.com')

    @property
    def supervisor3(self):
        return USER.objects.get(email='supervisorthree@email.com')

    def setUp(self):
        super().setUp()
        self.client.login(username=self.users[2][0], password=self.users[2][1])
        self.master_settings = MasterSettingFactory(
            organization=self.organization,
            occurrences=True,
            depletion_required=True,
            require_prior_approval=True,
            require_time_period=True,
            require_document=True,
            continuous=True,
            leave_limitations=True
        )
        self.leave_type = LeaveTypeFactory(master_setting=self.master_settings)
        self.rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            is_paid=False,
            employee_can_apply=False,
            admin_can_assign=False,
            require_prior_approval=False,
            require_docs=True,
            require_docs_for=2,
            limit_leave_occurrence=2,
            limit_leave_occurrence_duration=3,
            limit_leave_occurrence_duration_type="Months",
            maximum_continuous_leave_length=2.0,
            minimum_continuous_leave_length=1.0,
            limit_leave_to=2.0,
            limit_leave_duration=3,
            limit_leave_duration_type="Months",
            start_date=get_today() + timedelta(days=8),
            end_date=get_today() - timedelta(days=8)
        )
        IndividualAttendanceSettingFactory(
            user=self.normal
        )

    def payload(self, account):
        end_date = (get_today(with_time=True) + timedelta(days=10)).date()
        return {
            "user": self.normal.id,
            "leave_account": account.id,
            "details": "test for supervisor notification",
            "start": get_today(),
            "end": end_date
        }

    def url(self):
        return reverse(
            'api_v1:leave:request-on-behalf-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def assign_supervisor(self):
        supervisors = [
            UserSupervisor(
                user=self.normal,
                supervisor=self.supervisor1,
                authority_order=1,
                approve=True, deny=True, forward=False
            ),
            UserSupervisor(
                user=self.normal,
                supervisor=self.supervisor2,
                authority_order=2,
                approve=True, deny=True, forward=False
            ),
            UserSupervisor(
                user=self.normal,
                supervisor=self.supervisor3,
                authority_order=3,
                approve=True, deny=True, forward=False
            )
        ]
        UserSupervisor.objects.bulk_create(supervisors)

    @staticmethod
    def output():
        return {
            'non_field_errors': [
                [f'The leave must be applied after {get_today() + timedelta(days=8)}',
                 f'The leave must be applied before {get_today() - timedelta(days=8)}'],
                 'A valid attachment is required to apply for this leave for more than 2.0 balance',
                 'This leave request consumes 5. This leave allows leave between 1.0 and 2.0.',
                 'The total allowed balance in 3 Months is 2.0. You cannot apply'
            ]
        }

    def test_supervisor_offline_attendance(self):
        with patch(
            'irhrs.leave.utils.leave_request.get_shift_start',
            return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.leave_request.get_shift_end', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.balance.get_leave_balance', return_value=(5, None)
        ), patch(
            'irhrs.leave.utils.leave_request.validate_can_request_assign', return_value=True
        ), patch(
            'irhrs.leave.utils.balance.validate_sufficient_leave_balance', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_sheet.create_leave_sheets', return_value=None
        ):
            self.assign_supervisor()
            url_with_supervisor_params = self.url() + '?as=supervisor&bypass_validation=True'
            account = LeaveAccountFactory(user=self.normal, rule=self.rule)
            bad_response = self.client.post(
                self.url(),
                data=self.payload(account)
            )
            self.assertEqual(
                bad_response.status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                bad_response.json(),
                self.output()
            )
            response = self.client.post(
                url_with_supervisor_params,
                data=self.payload(account)
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED
            )

    def test_offline_attendance_notification(self):
        rule = LeaveRuleFactory(leave_type=self.leave_type)
        account = LeaveAccountFactory(user=self.normal, rule=rule)
        with patch(
            'irhrs.leave.utils.leave_request.get_shift_start', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.leave_request.get_shift_end', return_value=get_today(with_time=True)
        ), patch(
            'irhrs.leave.utils.balance.get_leave_balance', return_value=(0, None)
        ), patch(
            'irhrs.leave.utils.leave_request.validate_can_request_assign', return_value=True
        ), patch(
            'irhrs.leave.utils.balance.validate_sufficient_leave_balance', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_sheet.create_leave_sheets', return_value=None
        ):
            url_with_supervisor_params = self.url() + '?as=supervisor&bypass_validation=True'
            self.assign_supervisor()
            response = self.client.post(
                url_with_supervisor_params,
                data=self.payload(account)
            )
            text = f"{self.supervisor2} has approved {self.normal}'s leave from {get_today()} to {get_today()}"
            supervisor1 = Notification.objects.filter(
                text=text,
                actor=self.supervisor2
            ).first().recipient
            normal = Notification.objects.filter(
                text=f"{self.supervisor2} has approved your leave for {get_today()}",
                actor=self.supervisor2
            ).first().recipient
            self.assertEqual(
                supervisor1,
                self.supervisor1
            )
            self.assertEqual(
                normal,
                self.normal
            )


class TestLeaveRequestAutoApply(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.leave_rule2 = LeaveRuleFactory()
        self.leave_rule = LeaveRuleFactory(
            adjacent_offday_inclusive=True,
            adjacent_offday_inclusive_type=INCLUDE_HOLIDAY_AND_OFF_DAY,
            inclusive_leave=INCLUDE_HOLIDAY_AND_OFF_DAY,
            inclusive_leave_number=0
        )
        self.user = UserFactory()
        UserSupervisor.objects.create(authority_order=1, user=self.user, supervisor=UserFactory())
        setting = IndividualAttendanceSettingFactory(
            user=self.user,
        )
        work_shift = WorkShiftFactory2(work_days=7)
        IndividualUserShift.objects.create(
            individual_setting=setting,
            shift=work_shift,
            applicable_from=timezone.now()-timezone.timedelta(days=100)
        )
        AdjacentLeaveReductionTypes.objects.create(
            leave_rule=self.leave_rule, leave_type=self.leave_rule2.leave_type
        )
        self.leave_account = LeaveAccountFactory(user=self.user, rule=self.leave_rule)
        self.leave_account2 = LeaveAccountFactory(user=self.user, rule=self.leave_rule2)

    def test_leave_request_with_no_additional_cuts(self):
        leave_request = LeaveRequestFactory(
            start=timezone.now() - timezone.timedelta(1),
            end=timezone.now() - timezone.timedelta(1),
            user=self.user,
            leave_account=self.leave_account,
            leave_rule=self.leave_rule
        )
        populate_timesheet_for_user(
            self.user,
            leave_request.start - timedelta(5),
            leave_request.end + timedelta(5),
            notify='true', authority=1
        )
        # leave_request = LeaveRequestFactory(
        #     user=self.user,
        #     leave_account=self.leave_account,
        #     leave_rule=self.leave_rule
        # )
        leave_request.status = APPROVED
        leave_request.save()
        leave_request.refresh_from_db()
        apply_leave_on_behalf_by_system_if_applicable(leave_request)
        self.assertEqual(
            set(self.user.leave_requests.values_list('start__date', flat=True)),
            {
                leave_request.start.date(),
            }
        )
        self.assertEqual(self.user.leave_requests.count(), 1)

    def test_leave_request_with_holiday_after_end(self):
        leave_request = LeaveRequestFactory(
            start=timezone.now() - timezone.timedelta(5),
            end=timezone.now() - timezone.timedelta(3),
            user=self.user,
            leave_account=self.leave_account,
            leave_rule=self.leave_rule
        )
        populate_timesheet_for_user(
            self.user,
            leave_request.start - timedelta(5),
            leave_request.end + timedelta(5),
            notify='true', authority=1
        )
        leave_request.status = APPROVED
        leave_request.save()
        leave_request.refresh_from_db()

        def get_coefficient(user, date_):
            ret = [
                leave_request.start.date() - timedelta(1),
                (leave_request.end.date() + timedelta(1))
            ]
            if date_ in ret:
                return HOLIDAY
            return WORKDAY

        with patch(
            'irhrs.leave.utils.leave_request.get_coefficient',
            new=get_coefficient
        ):
            apply_leave_on_behalf_by_system_if_applicable(leave_request)
            self.assertEqual(self.user.leave_requests.count(), 3)  # 2 additional.
        leave_account = leave_request.leave_account
        leave_account.refresh_from_db()
        self.assertEqual(
            set(self.user.leave_requests.values_list('start__date', flat=True)),
            {
                leave_request.start.date(),
                leave_request.start.date() - timedelta(1),
                leave_request.end.date() + timedelta(1),
            }
        )
        self.assertEqual(leave_account.usable_balance, 8)  # leave from factory does not reduce

    def test_leave_request_with_offday_after_end(self):
        leave_request = LeaveRequestFactory(
            status=APPROVED,
            start=timezone.now() - timezone.timedelta(15),
            end=timezone.now() - timezone.timedelta(13),
            user=self.user,
            leave_account=self.leave_account,
            leave_rule=self.leave_rule
        )
        populate_timesheet_for_user(
            self.user,
            leave_request.start - timedelta(15),
            leave_request.end + timedelta(15),
            notify='true', authority=1
        )

        def get_coefficient(user, date_):
            ret = [
                leave_request.start.date() - timedelta(1),
                (leave_request.end.date() + timedelta(1))
            ]
            if date_ in ret:
                return OFFDAY
            return WORKDAY

        with patch(
            'irhrs.leave.utils.leave_request.get_coefficient',
            new=get_coefficient
        ):
            apply_leave_on_behalf_by_system_if_applicable(leave_request)
            self.assertEqual(self.user.leave_requests.count(), 3)  # 2 additional.
        leave_account = leave_request.leave_account
        leave_account.refresh_from_db()
        # print_leave_histories(leave_account)
        self.assertEqual(
            set(self.user.leave_requests.values_list('start__date', flat=True)),
            {
                leave_request.start.date(),
                leave_request.start.date() - timedelta(1),
                leave_request.end.date() + timedelta(1),
            }
        )
        self.assertEqual(leave_account.usable_balance, 8)  # leave from factory does not reduce

    def test_leave_request_with_two_holidays_after_end(self):
        leave_request = LeaveRequestFactory(
            status=APPROVED,
            start=timezone.now() - timezone.timedelta(20),
            end=timezone.now() - timezone.timedelta(17),
            user=self.user,
            leave_account=self.leave_account,
            leave_rule=self.leave_rule
        )
        populate_timesheet_for_user(
            self.user,
            leave_request.start - timedelta(15),
            leave_request.end + timedelta(15),
            notify='true', authority=1
        )

        def get_coefficient(user, date_):
            ret = [
                leave_request.end.date() + timedelta(1),
                (leave_request.end.date() + timedelta(2))
            ]
            if date_ in ret:
                return OFFDAY
            return WORKDAY

        with patch(
            'irhrs.leave.utils.leave_request.get_coefficient',
            new=get_coefficient
        ):
            apply_leave_on_behalf_by_system_if_applicable(leave_request)
            self.assertEqual(self.user.leave_requests.count(), 3)  # 2 additional.
        leave_account = leave_request.leave_account
        leave_account.refresh_from_db()
        self.assertEqual(
            set(self.user.leave_requests.values_list('start__date', flat=True)),
            {
                leave_request.start.date(),
                leave_request.end.date() + timedelta(1),
                leave_request.end.date() + timedelta(2),
            }
        )
        self.assertEqual(leave_account.usable_balance, 8)  # leave from factory does not reduce

    def test_leave_request_applied_from_multiple_leave_types(self):
        leave_request = LeaveRequestFactory(
            status=APPROVED,
            start=timezone.now() - timezone.timedelta(25),
            end=timezone.now() - timezone.timedelta(23),
            user=self.user,
            leave_account=self.leave_account,
            leave_rule=self.leave_rule
        )
        leave_account = self.leave_account
        force_balance(leave_account, -leave_account.usable_balance)
        populate_timesheet_for_user(
            self.user,
            leave_request.start - timedelta(15),
            leave_request.end + timedelta(15),
            notify='true', authority=1
        )

        def get_coefficient(user, date_):
            ret = [
                leave_request.end.date() + timedelta(1),
                (leave_request.end.date() + timedelta(2))
            ]
            if date_ in ret:
                return OFFDAY
            return WORKDAY

        with patch(
            'irhrs.leave.utils.leave_request.get_coefficient',
            new=get_coefficient
        ):
            apply_leave_on_behalf_by_system_if_applicable(leave_request)
            # self.assertEqual(self.user.leave_requests.count(), 3)  # 2 additional.
        leave_account = leave_request.leave_account
        leave_account.refresh_from_db()
        self.assertEqual(
            set(self.user.leave_requests.values_list('start__date', flat=True)),
            {
                leave_request.start.date(),
                leave_request.end.date() + timedelta(1),
                leave_request.end.date() + timedelta(2),
            }
        )
        self.assertEqual(leave_account.usable_balance, 0)  # leave from factory does not reduce

    def test_leave_request_applied_with_not_enough_balance_adds_to_payroll(self):
        leave_request = LeaveRequestFactory(
            status=APPROVED,
            start=timezone.now() - timezone.timedelta(45),
            end=timezone.now() - timezone.timedelta(40),
            user=self.user,
            leave_account=LeaveAccountFactory(user=self.user, rule=self.leave_rule),
            leave_rule=self.leave_rule
        )
        leave_account = leave_request.leave_account
        force_balance(leave_account, -leave_account.usable_balance)
        populate_timesheet_for_user(
            self.user,
            leave_request.start - timedelta(15),
            leave_request.end + timedelta(15),
            notify='true', authority=1
        )

        def get_coefficient(user, date_):
            ret = [
                leave_request.end.date() + timedelta(1),
                leave_request.end.date() + timedelta(2),
                leave_request.end.date() + timedelta(3),
                leave_request.start.date() + timedelta(-1),
                leave_request.start.date() + timedelta(-2),
                leave_request.start.date() + timedelta(-3),
            ]
            if date_ in ret:
                return OFFDAY
            return WORKDAY

        leave_account.rule.reduction_leave_types.all().delete()
        with patch(
            'irhrs.leave.utils.leave_request.get_coefficient',
            new=get_coefficient
        ):
            apply_leave_on_behalf_by_system_if_applicable(leave_request)
            # self.assertEqual(self.user.leave_requests.count(), 3)  # 2 additional.
        leave_account = leave_request.leave_account
        leave_account.refresh_from_db()
        self.assertEqual(
            set(self.user.leave_requests.values_list('start__date', flat=True)),
            {
                leave_request.start.date(),
            }
        )
        self.assertEqual(leave_account.usable_balance, 0)  # leave from factory does not reduce
        # there should be 6 days to reduce. However, due to insufficient balance,
        # 6 entries for each dates should be prepared to be sent to payroll

        self.assertEqual(
            6.0,
            AdjacentTimeSheetOffdayHolidayPenalty.objects.filter(
                leave_account__user=self.leave_account.user
            ).aggregate(
                sum_penalty=Sum('penalty')
            )['sum_penalty']
        )

    def test_leave_request_applied_with_unpaid_account_adds_to_payroll(self):
        leave_request = LeaveRequestFactory(
            status=APPROVED,
            start=timezone.now() - timezone.timedelta(45),
            end=timezone.now() - timezone.timedelta(40),
            user=self.user,
            leave_account=LeaveAccountFactory(user=self.user, rule=self.leave_rule),
            leave_rule=self.leave_rule
        )
        leave_account = leave_request.leave_account
        force_balance(leave_account, -leave_account.usable_balance)
        populate_timesheet_for_user(
            self.user,
            leave_request.start - timedelta(15),
            leave_request.end + timedelta(15),
            notify='true', authority=1
        )

        ret = [
            leave_request.end.date() + timedelta(1),
            leave_request.end.date() + timedelta(2),
            leave_request.end.date() + timedelta(3),
            leave_request.start.date() + timedelta(-1),
            leave_request.start.date() + timedelta(-2),
            leave_request.start.date() + timedelta(-3),
        ]

        def get_coefficient(user, date_):
            if date_ in ret:
                return OFFDAY
            return WORKDAY

        with patch(
            'irhrs.leave.utils.leave_request.get_coefficient',
            new=get_coefficient
        ):
            apply_leave_on_behalf_by_system_if_applicable(leave_request)
            # self.assertEqual(self.user.leave_requests.count(), 3)  # 2 additional.
        leave_account = leave_request.leave_account
        leave_account.refresh_from_db()
        self.assertEqual(
            set(self.user.leave_requests.values_list('start__date', flat=True)),
            {
                leave_request.start.date(),
                *ret
            }
        )
        self.assertEqual(leave_account.usable_balance, 0)  # leave from factory does not reduce
        # there should be 6 days to reduce. However, due to insufficient balance,
        # 6 entries for each dates should be prepared to be sent to payroll

        self.assertEqual(
            6.0,
            AdjacentTimeSheetOffdayHolidayPenalty.objects.filter(
                leave_account__user=self.leave_account.user
            ).aggregate(
                sum_penalty=Sum('penalty')
            )['sum_penalty']
        )
