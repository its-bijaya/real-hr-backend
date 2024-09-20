from datetime import timedelta
from django.urls import reverse
from rest_framework import status
from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    CreditHourSettingFactory, WorkShiftFactory, OvertimeSettingFactory
from irhrs.attendance.models import PreApprovalOvertime
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.users.models import UserSupervisor


class TestActionOnPreApprovalOvertime(RHRSAPITestCase):
    users = [
        ("admin@gmail.com", "admin", "Male"),
        ("supervisor@gmail.com", "supervisor", "Female"),
        ("user@gmail.com", "user", "Female")
    ]
    organization_name = "Aayubank"

    def setUp(self):
        super().setUp()
        FiscalYearFactory(
            organization=self.organization,
            start_at=get_today(),
            end_at=get_today() + timedelta(days=365)
        )
        credit_hour_setting = CreditHourSettingFactory(
            organization=self.organization
        )
        self.ot_setting = OvertimeSettingFactory(
            daily_overtime_limit_applicable=True,
            daily_overtime_limit=120,
            weekly_overtime_limit_applicable=True,
            weekly_overtime_limit=180,
            require_prior_approval=True,
            allow_edit_of_pre_approved_overtime=True,
            reduce_ot_if_actual_ot_lt_approved_ot=True,
            actual_ot_if_actual_gt_approved_ot=True,
            off_day_overtime_limit=120,
            paid_holiday_affect_overtime=False,
            holiday_overtime_limit=None,
            leave_affect_overtime=False,
            leave_overtime_limit=None
        )
        attendance_setting = IndividualAttendanceSettingFactory(
            user=self.created_users[2],
            credit_hour_setting=credit_hour_setting,
            enable_credit_hour=True,
            overtime_setting=self.ot_setting,
            enable_overtime=True,
            enable_approval=True
        )
        work_shift = WorkShiftFactory()
        date = get_today() - timedelta(days=20)
        attendance_setting.individual_setting_shift.create(
            shift=work_shift,
            applicable_from=date
        )
        attendance_setting.credit_hour_setting = credit_hour_setting
        attendance_setting.save()
        self.url = reverse(
            "api_v1:attendance:pre-approval-overtime-list",
            kwargs={
                "organization_slug": self.organization.slug
            }
        )
        self.payload = {
            "overtime_date": get_today() + timedelta(days=2),
            "overtime_duration": "01:00:00",
            "remarks": "requested"
        }
        self.pre_approval = PreApprovalOvertime.objects.create(
            sender=self.created_users[2],
            recipient=self.created_users[1],
            status="Requested",
            overtime_date=get_today() + timedelta(days=3),
            overtime_duration="01:00:00",
            request_remarks='request',
            action_remarks='action'
        )
        UserSupervisor.objects.create(
            user=self.created_users[2],
            supervisor=self.created_users[1],
            authority_order=1,
            approve=True,
            forward=False,
            deny=True
        )

    def weekly_ot_setting(self):
        self.client.force_login(self.created_users[2])
        self.pre_approval.delete()
        self.ot_setting.daily_overtime_limit = 0
        self.ot_setting.daily_overtime_limit_applicable = False
        self.ot_setting.off_day_overtime = False
        self.ot_setting.off_day_overtime_limit = 0
        self.ot_setting.save()

    def test_pre_approval_overtime_request(self):
        self.client.force_login(self.created_users[2])
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json().get('status'), 'Requested')

    def test_invalid_pre_approval_overtime_request(self):
        self.client.force_login(self.created_users[2])
        bad_payload = {
            "overtime_date": get_today() + timedelta(days=4),
            "overtime_duration": "04:00:00",
            "remarks": "requested"
        }
        response = self.client.post(self.url, bad_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get('overtime_duration')[0],
            'The daily limit for Overtime is 02:00:00. Requested: 04:00:00'
        )

    def test_action_performed_on_pre_approval_overtime(self):
        self.client.force_login(self.created_users[1])
        IndividualAttendanceSettingFactory(
            user=self.created_users[1]
        )

        url = reverse(
            "api_v1:attendance:pre-approval-overtime-perform-action",
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': self.pre_approval.id,
                'action': 'approve'
            }
        ) + f'?as=supervisor'

        payload = {
            "remarks": "Approved request"
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('action_remarks'), 'Approved request')

        # Test Case for approved pre overtime count
        get_url = reverse(
            "api_v1:attendance:pre-approval-overtime-list",
            kwargs={
                "organization_slug": self.organization.slug
            }
        ) + (f'?status=Requested&user=&as=supervisor&start_date={get_today() - timedelta(days=4)}'
             f'&end_date={get_today() + timedelta(days=20)}')
        response = self.client.get(get_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('statistics')['Approved'], 1)

    def test_valid_weekly_pre_approval_overtime_request(self):
        self.weekly_ot_setting()
        valid_payload = {
            "overtime_date": get_today(),
            "overtime_duration": "03:00:00",
            "remarks": "weekly overtime"
        }
        response = self.client.post(self.url, valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.json().get('status'), 'Requested'
        )
        self.assertEqual(
            response.json().get('overtime_duration'), '03:00:00'
        )
        self.assertEqual(
            response.json().get('request_remarks'), 'weekly overtime'
        )

    def test_invalid_weekly_pre_approval_overtime_request(self):
        self.weekly_ot_setting()
        bad_payload = {
            "overtime_date": get_today(),
            "overtime_duration": "04:00:00",
            "remarks": "requested"
        }
        response = self.client.post(self.url, bad_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get('overtime_duration')[0],
            'The weekly limit for Overtime is 03:00:00. Existing : 00:00:00. Requested : 04:00:00'
        )

        # Can apply for credit hour request if credit hour setting is assigned
        self.assertEqual(
            response.json().get('redirect')['payload']['credit_hour_duration'], '4:00:00'
        )
        self.assertEqual(
            response.json().get('redirect')['redirect'], 'True'
        )






