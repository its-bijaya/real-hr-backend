from datetime import timedelta
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from irhrs.attendance.api.v1.tests.factory import (
    CreditHourSettingFactory, IndividualAttendanceSettingFactory, 
    WorkShiftFactory
)
from irhrs.attendance.models.credit_hours import CreditHourDeleteRequest, CreditHourRequest
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.constants.organization import (
    CREDIT_HOUR_DELETE_REQUEST_IS_APPROVED_DECLINED_EMAIL, 
    CREDIT_HOUR_DELETE_REQUEST_IS_REQUESTED_FORWARDED_EMAIL,
    CREDIT_HOUR_REQUEST_ON_BEHALF
)
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory, FiscalYearMonthFactory
from irhrs.organization.models.settings import EmailNotificationSetting
from irhrs.users.models.supervisor_authority import UserSupervisor
from irhrs.attendance.constants import APPROVED, DECLINED
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, LeaveAccountFactory
from irhrs.attendance.constants import CREDIT_HOUR

FORWARD = "forward"


class TestCreditHourDeleteRequest(RHRSTestCaseWithExperience):
    users = [
        ("admin@gmail.com", "admin", "Female", "admin"),
        ("firstsupervisor@gmail.com", "first", "Female", "supervisor"),
        ("secondsupervisor@gmail.com", "second", "Female", "supervisor"),
        ("user@gmail.com", "user", "Female", "trainee")
    ]

    organization_name = "Aayu bank"

    def setUp(self):
        super().setUp()
        self.credit_hour_date = get_today() + timedelta(days=7)
        fiscal_year = FiscalYearFactory(
            organization=self.organization,
            start_at=get_today() - timedelta(days=365),
            end_at=get_today() + timedelta(days=365)
        )
        FiscalYearMonthFactory(
            fiscal_year=fiscal_year,
            month_index=1,
            start_at=get_today() - timedelta(days=365),
            end_at=get_today() + timedelta(days=365)
        )
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
            user=self.created_users[3],
            balance=300,
            usable_balance=300
        )

        user = self.created_users[3]
        credit_hour_setting = CreditHourSettingFactory(
            organization=self.organization,
            require_prior_approval=True
        )
        attendance_setting = IndividualAttendanceSettingFactory(
            user=user,
            enable_credit_hour=True,
            credit_hour_setting=credit_hour_setting
        )
        w_shift = WorkShiftFactory()
        date = get_today() - timedelta(days=100)
        attendance_setting.individual_setting_shift.create(
            shift=w_shift,
            applicable_from=date,
        )
        attendance_setting.credit_hour_setting = credit_hour_setting
        attendance_setting.save()
        
        UserSupervisor.objects.bulk_create(
            [
                UserSupervisor(
                    user=self.created_users[3],
                    supervisor=self.created_users[i],
                    authority_order=i,
                    approve=True,
                    deny=True,
                    forward=False if i == 2 else True
                )
                for i in range(1, 3)
            ]
        )

        email_types = [
            CREDIT_HOUR_DELETE_REQUEST_IS_REQUESTED_FORWARDED_EMAIL,
            CREDIT_HOUR_DELETE_REQUEST_IS_APPROVED_DECLINED_EMAIL,
            CREDIT_HOUR_REQUEST_ON_BEHALF
        ]

        EmailNotificationSetting.objects.bulk_create(
            [
                EmailNotificationSetting(
                    organization=self.organization,
                    email_type=email_type,
                    send_email=True,
                    allow_unsubscribe=True
                )
                for email_type in email_types
            ]
        )

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_CREDIT_REQUEST=True)
    def create_credit_hour_request(self, credit_hour_date):
        self.client.force_login(self.created_users[3])
        url = reverse(
            'api_v1:attendance:credit-hour-request-request-bulk',
            kwargs={
                "organization_slug": self.organization.slug,
            }
        )
        payload = {
            "requests": [
                {
                    "credit_hour_date": credit_hour_date,
                    "credit_hour_duration": "02:00:00",
                    "remarks": "request"
                }
            ] 
        }
        self.client.post(url, payload, format='json')
        return CreditHourRequest.objects.filter(
            credit_hour_date=credit_hour_date, 
            sender=self.created_users[3]).first()

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_CREDIT_REQUEST=True)
    def create_credit_hour_delete_request(self, status="Requested"):
        self.client.force_login(self.created_users[3])
        credit_hour_request = self.create_credit_hour_request(
            credit_hour_date=self.credit_hour_date,
        )
        credit_hour_request.status = "Approved"
        credit_hour_request.save()

        url = reverse(
            "api_v1:attendance:credit-hour-request-detail",
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': credit_hour_request.id
            }
        )

        payload = {
            "remarks": "delete"
        }

        response = self.client.delete(url, payload, format='json')
        self.assertEqual(response.status_code, 204)

        return CreditHourDeleteRequest.objects.filter(
            status=status
        ).first()

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_CREDIT_REQUEST=True)
    def action_on_credit_hour_delete_request(self, user, action=APPROVED, actor="supervisor"):
        credit_hour_delete_request = self.create_credit_hour_delete_request(status="Requested")
        
        mail.outbox = []
        self.client.force_login(user)
        
        url = (
            reverse(
                "api_v1:attendance:credit-hour-delete-requests-perform-action",
                kwargs={
                    "organization_slug": self.organization.slug,
                    "pk": credit_hour_delete_request.id,
                    "action": action
                },  
            ) 
            + f"?as={actor}"
        )
            
        payload = {
            "remarks": action,
        }

        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, 200, response.json())

    def test_credit_hour_delete_request_requested_by_user(self):
        self.create_credit_hour_delete_request()
        emails = mail.outbox
        self.assertEqual(len(emails), 2)

        email_subject = "Credit hour delete request"
        text_hr = (
            f"{self.created_users[3].full_name} has requested their credit hour "
            f"delete request for {self.credit_hour_date}"
        )
        
        self.assertEqual(emails[0].to, [self.users[0][0]])
        self.assertEqual(emails[0].subject, email_subject)
        self.assertEqual(emails[0].body, text_hr)

        text_supervisor = (
            f"{self.created_users[3].full_name} sent credit hour delete request "
            f"for {self.credit_hour_date}."
        )
       
        self.assertEqual(emails[1].to, [self.users[1][0]])
        self.assertEqual(emails[1].subject, email_subject)
        self.assertEqual(emails[1].body, text_supervisor)
    
    def test_credit_hour_delete_request_forwarded_by_supervisor(self):
        self.action_on_credit_hour_delete_request(
            self.created_users[1], FORWARD)
        emails = mail.outbox
        self.assertEqual(len(emails), 1)

        email_subject = "Credit hour delete request"
        text_supervisor_second = (
            f"{self.created_users[1].full_name} forwarded "
            f"{self.created_users[3].full_name}'s"
            f" credit hour delete request for {self.credit_hour_date}."
        )

        self.assertEqual(emails[0].to, [self.users[2][0]])
        self.assertEqual(emails[0].subject, email_subject)
        self.assertEqual(emails[0].body, text_supervisor_second)
    
    def test_credit_hour_delete_request_approved_by_supervisor(self):
        action = APPROVED
        status = action.lower()
        payload_action = "approve"
        self.action_on_credit_hour_delete_request(
            self.created_users[1], payload_action)
        emails = mail.outbox
        self.assertEqual(len(emails), 2)

        email_subject = f"Credit hour delete request has been {status}"
        text_hr = (
            f"{self.created_users[1].full_name} has {status} {self.created_users[3].full_name}'s "
            f"credit hour delete request for {self.credit_hour_date}"
        )

        self.assertEqual(emails[0].to, [self.users[0][0]])
        self.assertEqual(emails[0].subject, email_subject)
        self.assertEqual(emails[0].body, text_hr)

        text_user = (
            f"{self.created_users[1].full_name} has {action} your "
            f" credit hour delete request for {self.credit_hour_date}."
        )
    
        self.assertEqual(emails[1].to, [self.users[3][0]])
        self.assertEqual(emails[1].subject, email_subject)
        self.assertEqual(emails[1].body, text_user)

    def test_credit_hour_delete_request_declined_by_supervisor(self):
        action = DECLINED
        status = action.lower()
        payload_action = "decline"
        self.action_on_credit_hour_delete_request(
            self.created_users[1], payload_action
        )
        emails = mail.outbox
        self.assertEqual(len(emails), 2)

        email_subject = f"Credit hour delete request has been {status}"
        text_hr = (
            f"{self.created_users[1].full_name} has {status} {self.created_users[3].full_name}'s "
            f"credit hour delete request for {self.credit_hour_date}"
        )

        self.assertEqual(emails[0].to, [self.users[0][0]])
        self.assertEqual(emails[0].subject, email_subject)
        self.assertEqual(emails[0].body, text_hr)

        text_user = (
            f"{self.created_users[1].full_name} has {action} your "
            f" credit hour delete request for {self.credit_hour_date}."
        )
    
        self.assertEqual(emails[1].to, [self.users[3][0]])
        self.assertEqual(emails[1].subject, email_subject)
        self.assertEqual(emails[1].body, text_user)

    def test_credit_hour_delete_request_approved_by_hr(self):
        action = APPROVED
        status = action.lower()
        payload_action = "approve" 
        self.action_on_credit_hour_delete_request(
            self.created_users[0], payload_action, actor="hr"
        )
        emails = mail.outbox
        self.assertEqual(len(emails), 1)

        email_subject = f"Credit hour delete request has been {status}"
        text_user = (
            f"{self.created_users[0].full_name} has {action} your "
            f" credit hour delete request for {self.credit_hour_date}."
        )

        self.assertEqual(emails[0].to, [self.users[3][0]])
        self.assertEqual(emails[0].subject, email_subject)
        self.assertEqual(emails[0].body, text_user)

    def test_credit_hour_delete_request_declined_by_hr(self):
        action = DECLINED
        status = action.lower()
        payload_action = "decline" 
        self.action_on_credit_hour_delete_request(
            self.created_users[0], payload_action, actor="hr"
        )
        emails = mail.outbox
        self.assertEqual(len(emails), 1)

        email_subject = f"Credit hour delete request has been {status}"
        text_user = (
            f"{self.created_users[0].full_name} has {action} your "
            f" credit hour delete request for {self.credit_hour_date}."
        )

        self.assertEqual(emails[0].to, [self.users[3][0]])
        self.assertEqual(emails[0].subject, email_subject)
        self.assertEqual(emails[0].body, text_user)

    def test_credit_hour_request_on_behalf_by_hr(self):
        self.client.force_login(self.created_users[0])
        url = reverse(
            "api_v1:attendance:credit-hour-request-request-on-behalf",
            kwargs={
                "organization_slug": self.organization.slug
            }
        ) + f"?as=hr"

        payload = {
            "requests": [
                {
                    "credit_hour_date": get_today() - timedelta(days=5),
                    "credit_hour_duration": "02:00:00",
                    "remarks": "on behalf"
                }
            ],
            "user_id": self.created_users[3].id

        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 200, response.json())

        emails = mail.outbox
        self.assertEqual(len(emails), 1)

        email_subject = f"Credit hour request on behalf"
        text_user = (
            f"{self.created_users[0].full_name} has request and approved "
            f"{self.created_users[3]}'s credit hour for {get_today() - timedelta(days=5)}."
        )

        self.assertEqual(emails[0].to, [self.users[3][0], self.users[0][0]])
        self.assertEqual(emails[0].subject, email_subject)
        self.assertEqual(emails[0].body, text_user)

