from datetime import timedelta, datetime
from rest_framework import status
from django.urls import reverse

from irhrs.attendance.api.v1.tests.factory import CreditHourSettingFactory, \
    IndividualAttendanceSettingFactory, WorkShiftFactory
from irhrs.attendance.constants import CREDIT_HOUR, REQUESTED
from irhrs.attendance.models import CreditHourRequest
from irhrs.attendance.utils.credit_hours import get_credit_leave_account_for_user
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today, get_tomorrow
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, LeaveAccountFactory
from irhrs.leave.models import LeaveAccountHistory, LeaveAccount
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory


class CreditHourBulkRequestValidation(RHRSAPITestCase):
    users = [
        ("admin@gmail.com", "admin", "Male"),
        ("user@gmail.com", "user", "Male")
    ]
    organization_name = "Aayubank"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.created_users[1])
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
            max_balance="840.0",
            name="new rule"
        )
        credit_hour_setting = CreditHourSettingFactory(
            organization=self.organization
        )
        self.assign_supervisor()
        attendance_setting = IndividualAttendanceSettingFactory(
            user=self.created_users[1],
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
            "api_v1:attendance:credit-hour-request-request-bulk",
            kwargs={
                'organization_slug': self.organization.slug
            }
        )
        self.payload = {
            "requests": [
                {
                    "credit_hour_date": get_today() + timedelta(days=2),
                    "credit_hour_duration": "02:00:00",
                    "remarks": "requested"
                },
                {
                    "credit_hour_date": get_today() + timedelta(days=3),
                    "credit_hour_duration": "05:00:00",
                    "remarks": "requested"
                }
            ]
        }

        self.leave_account = LeaveAccount.objects.create(
            user=self.created_users[1],
            rule=self.leave_rule,
            balance=360,
            usable_balance=360
        )

    def assign_supervisor(self):
        user = self.created_users[1]
        supervisor = self.created_users[0]
        user.supervisors.create(supervisor=supervisor)

    def test_user_having_no_leave_account(self):
        self.leave_account.delete()
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.json()['non_field_errors'],
            ['User does not have a valid Credit Leave Account']
        )

    def test_invalid_credit_hour_bulk_request_validation(self):
        self.leave_account.balance=480
        self.leave_account.usable_balance=480
        self.leave_account.save()
        
        CreditHourRequest.objects.create(**{
            'request_remarks': 'remarks',
            'credit_hour_duration': "5:00:00",
            'credit_hour_date': get_tomorrow(),
            'status': REQUESTED,
            'sender': self.created_users[1],
            'recipient': self.created_users[1],
        })

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.json()['requests'][0]['credit_hour_duration'],
            ['The selected duration 02:00:00 exceeds max balance 14:00:00. '
             'Existing: 08:00:00. Pending 05:00:00']
        )
        self.assertEqual(
            response.json()['requests'][1]['credit_hour_duration'],
            ['The selected duration 05:00:00 exceeds max balance 14:00:00. '
             'Existing: 08:00:00. Pending 05:00:00']
        )

    def test_valid_credit_hour_bulk_request_validation(self):
        self.leave_account.balance=0
        self.leave_account.usable_balance=0
        self.leave_account.save()

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json()['success'],
            "Credit hours request sent successfully."
        )

    def test_credit_hour_request(self):
        # single credit hour request
        self.leave_account.balance=4800
        self.leave_account.usable_balance=4800
        self.leave_account.save()
        payload = {
            "requests": [
                {
                    "credit_hour_date": get_today() + timedelta(days=2),
                    "credit_hour_duration": "02:00:00",
                    "remarks": "requested"
                }
            ]
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.json()['requests'][0]['credit_hour_duration'],
            ['The selected duration 02:00:00 exceeds max balance 14:00:00.'
             ' Existing: 80:00:00. Pending 00:00:00']
        )

    def test_credit_hour_request_after_declined(self):
        self.leave_account
        CreditHourRequest.objects.create(**{
            'request_remarks': 'new',
            'credit_hour_duration': "5:00:00",
            'credit_hour_date': get_tomorrow(),
            'status': REQUESTED,
            'sender': self.created_users[1],
            'recipient': self.created_users[1],
        })

        credit_request = CreditHourRequest.objects.create(**{
            'request_remarks': 'remarks',
            'credit_hour_duration': "4:00:00",
            'credit_hour_date': get_tomorrow() + timedelta(days=3),
            'status': REQUESTED,
            'sender': self.created_users[1],
            'recipient': self.created_users[1],
        })

        credit_request.status = "Declined"
        credit_request.save()

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['requests'][1]['credit_hour_duration'],
            ['The selected duration 05:00:00 exceeds max balance 14:00:00.'
             ' Existing: 06:00:00. Pending 05:00:00']
        )

    def test_valid_credit_hour_request_after_cancelled_or_declined(self):
        # If max limit has not exceeded after declining or cancelling the
        # requested credit hour request the user can again request up to max limit.
        self.leave_account
        CreditHourRequest.objects.create(**{
            'request_remarks': 'valid',
            'credit_hour_duration': "1:00:00",
            'credit_hour_date': get_tomorrow(),
            'status': REQUESTED,
            'sender': self.created_users[1],
            'recipient': self.created_users[1],
        })

        credit_request = CreditHourRequest.objects.create(**{
            'request_remarks': 'remarks',
            'credit_hour_duration': "4:00:00",
            'credit_hour_date': get_tomorrow() + timedelta(days=3),
            'status': REQUESTED,
            'sender': self.created_users[1],
            'recipient': self.created_users[1],
        })

        credit_request.status = "Cancelled"
        credit_request.save()
        
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()['success'],
            "Credit hours request sent successfully."
        )
