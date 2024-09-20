from datetime import timedelta
from django.core import mail
from django.test.utils import override_settings
from django.urls.base import reverse
from irhrs.attendance.models.travel_attendance import TravelAttendanceSetting, \
    TravelAttendanceRequest
from irhrs.core.constants.organization import (
    TRAVEL_ATTENDANCE_REQUEST_EMAIL,
    TRAVEL_ATTENDANCE_IS_APPROVED_DECLINED,
)
from irhrs.core.utils.common import get_today
from irhrs.notification.models.notification import (
    Notification,
    OrganizationNotification,
)
from irhrs.users.models.supervisor_authority import UserSupervisor
from irhrs.organization.models.settings import EmailNotificationSetting

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.attendance.api.v1.tests.factory import WorkShiftFactory

from irhrs.attendance.models.attendance import (
    IndividualAttendanceSetting,
    IndividualUserShift,
)
from irhrs.attendance.models.travel_attendance import TravelAttendanceDeleteRequest

from irhrs.attendance.constants import APPROVED, DECLINED

APPROVE = "approve"
DECLINE = "decline"
FORWARD = "forward"

status_map = {APPROVE: APPROVED, DECLINE: DECLINED}


class TestTravelAttendanceEmail(RHRSTestCaseWithExperience):
    organization_name = "Organization"
    users = [
        ("admin@email.com", "admin", "Male", "admin"),
        ("supa@email.com", "supervisor", "Female", "jrdev"),
        ("supb@email.com", "supervisor", "Male", "dev"),
        ("supc@email.com", "supervisor", "Male", "srdev"),
        ("user@example.com", "user", "Male", "intern"),
    ]

    def setUp(self):
        super().setUp()
        user_setting = IndividualAttendanceSetting.objects.create(
            user=self.created_users[4]
        )
        shift = WorkShiftFactory(organization=self.organization)

        self.start_datetime = get_today(with_time=True)
        self.end_datetime = self.start_datetime + timedelta(days=2)
        self.start, self.start_time = self.start_datetime.isoformat().split("T")
        self.end, self.end_time = self.end_datetime.isoformat().split("T")

        IndividualUserShift.objects.create(
            individual_setting=user_setting,
            shift=shift,
            applicable_from=get_today() - timedelta(days=2),
            applicable_to=get_today() + timedelta(days=2),
        )
        UserSupervisor.objects.bulk_create(
            [
                UserSupervisor(
                    user=self.created_users[4],
                    supervisor=self.created_users[i],
                    authority_order=i,
                    approve=True,
                    deny=True,
                    forward=False if i == 3 else True,
                )
                for i in range(1, 4)
            ]
        )

        email_types = [
            TRAVEL_ATTENDANCE_REQUEST_EMAIL,
            TRAVEL_ATTENDANCE_IS_APPROVED_DECLINED,
        ]

        EmailNotificationSetting.objects.bulk_create(
            [
                EmailNotificationSetting(
                    organization=self.organization,
                    email_type=email_type,
                    send_email=True,
                    allow_unsubscribe=False,
                )
                for email_type in email_types
            ]
        )
        TravelAttendanceSetting.objects.create(
            organization=self.organization,
            can_apply_in_offday=True,
            can_apply_in_holiday=True,
        )
    @property
    def payload(self):
        return {
            "working_time": "Full Day",
            "start": self.start,
            "start_time": self.start_time,
            "end": self.end,
            "end_time": self.end_time,
            "request_remarks": "hello",
        }

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_TRAVEL_ATTENDANCE=True)
    def send_travel_attendance_request(self, payload=None) -> None:
        self.client.force_login(self.created_users[4])
        url = reverse(
            "api_v1:attendance:travel-attendance-list",
            kwargs={"organization_slug": self.organization.slug},
        )
        payload = payload or self.payload
        response = self.client.post(url, data=payload, format="json")
        self.client.logout()
        self.assertEqual(response.status_code, 201)

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_TRAVEL_ATTENDANCE=True)
    def act_on_travel_attendance_request(
        self, action: str = APPROVE, mode: str = "supervisor"
    ) -> None:
        actor = {"hr": self.created_users[0], "supervisor": self.created_users[1]}[mode]
        self.client.force_login(actor)
        url = (
            reverse(
                "api_v1:attendance:travel-attendance-perform-action",
                kwargs={
                    "organization_slug": self.organization.slug,
                    "pk": f"{self.created_users[4].travel_requests.first().id}",
                    "status": action,
                },
            )
            + f"?as={mode}"
        )

        response = self.client.put(url, data={"action_remarks": "action remarks"})
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_TRAVEL_ATTENDANCE=True)
    def send_travel_delete_request(self) -> None:
        """
        To make travel delete request, first travel attendance days for
        the travel request has to be created. Then the days we want to
        apply for delete request has to be sent as list of ids of
        attendance days.
        """
        self.client.force_login(self.created_users[4])
        travel_request = self.created_users[4].travel_requests.first()

        deleted_days = travel_request.travel_attendances.values_list("id", flat=True)

        url = reverse(
            "api_v1:attendance:travel-attendance-delete-request-list",
            kwargs={"organization_slug": self.organization.slug},
        )

        payload = {
            "travel_attendance": travel_request.id,
            "request_remarks": "request remarks",
            "deleted_days": deleted_days,
        }
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.client.logout()

        return len(deleted_days)

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_TRAVEL_ATTENDANCE=True)
    def act_on_travel_attendance_delete_request(
        self, action: str = APPROVE, mode: str = "supervisor"
    ) -> None:
        actor = {"hr": self.created_users[0], "supervisor": self.created_users[1]}[mode]
        self.client.force_login(actor)
        url = (
            reverse(
                "api_v1:attendance:travel-attendance-delete-request-perform-action",
                kwargs={
                    "organization_slug": self.organization.slug,
                    "pk": TravelAttendanceDeleteRequest.objects.first().id,
                    "status": action,
                },
            )
            + f"?as={mode}"
        )

        response = self.client.put(url, data={"action_remarks": "action remark"})
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def check_supervisor_action_on_travel_request(self, action: str) -> None:
        self.send_travel_attendance_request()
        mail.outbox = []
        self.act_on_travel_attendance_request(action=action, mode="supervisor")
        emails = mail.outbox
        self.assertEqual(len(emails), 2)
        subject = f"Travel Attendance Request {status_map[action]}"
        user_text = (
            f"{self.created_users[1].full_name} has {action}d your travel"
            f" request from {self.start} to {self.end}."
        )
        hr_text = (
            f"{self.created_users[1].full_name} has {action}d"
            f" {self.created_users[4]}'s travel"
            f" request from {self.start} to {self.end}."
        )
        self.assertEqual(emails[0].to, [self.users[4][0]])
        self.assertEqual(emails[0].subject, subject)
        self.assertEqual(emails[0].body, user_text)

        self.assertEqual(emails[1].to, [self.users[0][0]])
        self.assertEqual(emails[1].subject, subject)
        self.assertEqual(emails[1].body, hr_text)

    def check_supervisor_action_on_travel_delete_request(self, action: str) -> None:
        self.send_travel_attendance_request()
        self.act_on_travel_attendance_request()
        self.send_travel_delete_request()
        mail.outbox = []
        self.act_on_travel_attendance_delete_request(action=action)
        emails = mail.outbox
        self.assertEqual(len(emails), 2)
        subject = f"Travel Attendance Delete Request {status_map[action]}"
        user_text = (
            f"Your travel attendance delete request has been"
            f" {action}d by {self.created_users[1]}."
        )
        hr_text = (
            f"{self.created_users[4]}'s travel attendance delete request has"
            f" been {action}d by {self.created_users[1]}."
        )

        self.assertEqual(emails[0].to, [self.users[4][0]])
        self.assertEqual(emails[0].subject, subject)
        self.assertEqual(emails[0].body, user_text)

        self.assertEqual(emails[1].to, [self.users[0][0]])
        self.assertEqual(emails[1].subject, subject)
        self.assertEqual(emails[1].body, hr_text)

    def check_hr_action_on_travel_request(self, action: str) -> None:
        self.send_travel_attendance_request()
        mail.outbox = []
        self.act_on_travel_attendance_request(action=action, mode="hr")
        emails = mail.outbox
        self.assertEqual(len(emails), 1)
        subject = f"Travel Attendance Request {status_map[action]}"
        email_text = (
            f"{self.created_users[0].full_name} has {action}d your travel"
            f" request from {self.start} to {self.end}."
        )
        self.assertEqual(emails[0].to, [self.users[4][0]])
        self.assertEqual(emails[0].subject, subject)
        self.assertEqual(emails[0].body, email_text)

    def check_hr_action_on_travel_delete_request(self, action: str) -> None:
        self.send_travel_attendance_request()
        self.act_on_travel_attendance_request()
        self.client.force_login(self.created_users[0])
        self.send_travel_delete_request()

        mail.outbox = []
        self.act_on_travel_attendance_delete_request(action=action, mode="hr")
        email = mail.outbox

        self.assertEqual(len(email), 1)
        subject = f"Travel Attendance Delete Request {status_map[action]}"
        email_text = (
            f"Your travel attendance delete request has been"
            f" {action}d by {self.created_users[0]}."
        )
        self.assertEqual(email[0].to, [self.users[4][0]])
        self.assertEqual(email[0].subject, subject)
        self.assertEqual(email[0].body, email_text)

    def test_email_for_travel_attendance_requested_by_user(self):
        mail.outbox = []
        self.send_travel_attendance_request()
        emails = mail.outbox
        self.assertEqual(len(emails), 2)

        subject = "Travel Attendance Request"
        supervisor_text = (
            f"{self.created_users[4].full_name} has requested a travel request"
            f" from {self.start} to {self.end}."
        )
        hr_text = (
            f"{self.created_users[4].full_name} has requested their travel request"
            f" from {self.start} to {self.end}."
        )

        self.assertEqual(emails[0].to, [self.users[1][0]])
        self.assertEqual(emails[0].subject, subject)
        self.assertEqual(emails[0].body, supervisor_text)

        self.assertEqual(emails[1].to, [self.users[0][0]])
        self.assertEqual(emails[1].subject, subject)
        self.assertEqual(emails[1].body, hr_text)

    def test_email_for_travel_attendance_approved_by_supervisor(self):
        self.check_supervisor_action_on_travel_request(APPROVE)

    def test_email_for_travel_attendance_declined_by_supervisor(self):
        self.check_supervisor_action_on_travel_request(DECLINE)

    def test_email_for_travel_attendance_forwarded_by_supervisor(self):
        self.send_travel_attendance_request()
        mail.outbox = []
        self.act_on_travel_attendance_request(action=FORWARD, mode="supervisor")
        emails = mail.outbox
        self.assertEqual(len(emails), 1)

        subject = "Travel Attendance Request"
        email_text = (
            f"{self.created_users[1]} has forwarded {self.created_users[4]}'s"
            f" travel request from {self.start} to {self.end}."
        )
        self.assertEqual(emails[0].to, [self.users[2][0]])
        self.assertEqual(emails[0].subject, subject)
        self.assertEqual(emails[0].body, email_text)

    def test_email_for_travel_attendance_approved_by_hr(self):
        self.check_hr_action_on_travel_request(APPROVE)

    def test_email_for_travel_attendance_declined_by_hr(self):
        self.check_hr_action_on_travel_request(DECLINE)

    def test_email_for_travel_attendance_delete_request_by_user(self):
        self.send_travel_attendance_request()
        self.act_on_travel_attendance_request()
        mail.outbox = []
        self.send_travel_delete_request()
        emails = mail.outbox
        self.assertEqual(len(emails), 2)

        subject = "Travel Attendance Delete Request"
        email_text = (
            f"{self.created_users[4]} has sent travel attendance delete request."
        )

        self.assertEqual(emails[0].to, [self.users[1][0]])
        self.assertEqual(emails[0].subject, subject)
        self.assertEqual(emails[0].body, email_text)

        self.assertEqual(emails[1].to, [self.users[0][0]])
        self.assertEqual(emails[1].subject, subject)
        self.assertEqual(emails[1].body, email_text)

    def test_email_for_travel_attendance_delete_request_approved_by_supervisor(self):
        self.check_supervisor_action_on_travel_delete_request(APPROVE)

    def test_email_for_travel_attendance_delete_request_declined_by_supervisor(self):
        self.check_supervisor_action_on_travel_delete_request(DECLINE)

    def test_email_for_travel_attendance_delete_request_forwarded_by_supervisor(self):
        self.send_travel_attendance_request()
        self.act_on_travel_attendance_request()
        self.send_travel_delete_request()
        mail.outbox = []
        self.act_on_travel_attendance_delete_request(action=FORWARD, mode="supervisor")
        emails = mail.outbox
        self.assertEqual(len(emails), 1)
        subject = "Travel Attendance Delete Request"
        email_text = (
            f"{self.created_users[4]} has sent travel attendance " f"delete request."
        )
        self.assertEqual(emails[0].to, [self.users[2][0]])
        self.assertEqual(emails[0].subject, subject)
        self.assertEqual(emails[0].body, email_text)

    def test_email_for_travel_attendance_delete_request_approved_by_hr(self):
        self.check_hr_action_on_travel_delete_request(APPROVE)

    def test_email_for_travel_attendance_delete_request_decliined_by_hr(self):
        self.check_hr_action_on_travel_delete_request(DECLINE)

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_TRAVEL_ATTENDANCE=True)
    def test_travel_attendance_delete_request_notification(self):
        self.client.force_login(self.created_users[4])

        self.send_travel_attendance_request()
        self.act_on_travel_attendance_request(action=APPROVE, mode="supervisor")
        deleted_days = self.send_travel_delete_request()

        notification = Notification.objects.first()
        expected_notification_text = (
            f"{self.created_users[4]} has requested "
            f"a travel attendance delete request for {deleted_days} day(s)."
        )

        self.assertEqual(notification.text, expected_notification_text)

        organization_notification = OrganizationNotification.objects.first()
        organization_notification_text = (
            f"{self.created_users[4]} has requested "
            f"their travel attendance delete request for {deleted_days} day(s)."
        )

        self.assertEqual(organization_notification.text, organization_notification_text)

    def test_travel_request_on_request_deleted_days(self):
        self.send_travel_attendance_request()
        self.act_on_travel_attendance_request()
        self.send_travel_delete_request()
        self.act_on_travel_attendance_delete_request()
        payload = self.payload
        payload['request_remarks'] = 're-requesting'
        self.send_travel_attendance_request(payload=payload)
        self.assertTrue(
            TravelAttendanceRequest.objects.filter(
                request_remarks=payload['request_remarks'],
                start=self.payload['start'],
                end=self.payload['end']
            ).exists()
        )
        self.assertTrue(
            TravelAttendanceRequest.objects.filter(
                request_remarks=self.payload['request_remarks'],
                start=self.payload['start'],
                end=self.payload['end']
            ).exists()
        )

