from django.test.utils import override_settings
from django.urls import reverse
from django.core import mail

from irhrs.users.models.supervisor_authority import UserSupervisor
from irhrs.organization.models.settings import EmailNotificationSetting

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.attendance.api.v1.tests.factory import TimeSheetFactory

from irhrs.attendance.models.adjustments import AttendanceAdjustment
from irhrs.attendance.models.attendance import IndividualAttendanceSetting

from irhrs.core.constants.organization import (
    ATTENDANCE_ADJUSTMENT_REQUEST_EMAIL,
    ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_BY_SUPERVISOR_EMAIL,
    ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_DELETED_BY_HR_EMAIL,
)

from irhrs.attendance.constants import DECLINED, APPROVED

APPROVE = "approve"
DENY = "deny"
FORWARD = "forward"


class AdjustmentEmailTest(RHRSTestCaseWithExperience):
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
        IndividualAttendanceSetting.objects.create(user=self.created_users[4])

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
            ATTENDANCE_ADJUSTMENT_REQUEST_EMAIL,
            ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_BY_SUPERVISOR_EMAIL,
            ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_DELETED_BY_HR_EMAIL,
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

        self.timesheet = TimeSheetFactory(timesheet_user=self.created_users[4])

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_ATTENDANCE_ADJUSTMENT=True)
    def make_request(self):
        """
        user sends an adjustment request
        the obtained response is returned for assertion
        """
        self.client.login(email=self.users[4][0], password=self.users[4][1])
        url = reverse(
            "api_v1:attendance:adjustments-bulk-list",
            kwargs={"organization_slug": self.organization.slug},
        )
        payload = {
            "adjustments": [
                {
                    "timesheet": self.timesheet.id,
                    "timestamp": "2021-05-10T10:00",
                    "category": "Punch In",
                    "description": "back to the office rabin",
                }
            ]
        }
        response = self.client.post(url, data=payload, format="json")
        self.client.logout()
        return response

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_ATTENDANCE_ADJUSTMENT=True)
    def action_on_adjustment(self, user, action=APPROVE, actor="supervisor"):
        """
        creates a user request and then
        performs an action on adjustment (either hr or supervisor)
        """
        self.make_request()
        mail.outbox = []
        self.client.force_login(user)
        payload = [
            {
                "adjustment": AttendanceAdjustment.objects.first().id,
                "remark": "fasdfasdf",
                "action": action,
            }
        ]
        url = (
            reverse(
                "api_v1:attendance:adjustments-bulk-action",
                kwargs={"organization_slug": self.organization.slug},
            )
            + f"?as={actor}"
        )

        response = self.client.post(url, data=payload, format="json")
        self.client.logout()
        return response

    def test_email_for_adjustment_requested_by_user(self):
        """
        receivers: supervisor,hr
        """
        response = self.make_request()
        emails = mail.outbox

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(emails), 2)

        expected_subject = "Attendance entry adjustment requested"
        hr_text = (
            f"{self.created_users[4].full_name} has requested "
            "their attendance entry adjustment "
            f"for {self.timesheet.timesheet_for}."
        )
        sup_text = (
            f"{self.created_users[4].full_name} "
            "requested attendance entry adjustment "
            f"for {self.timesheet.timesheet_for}."
        )

        self.assertEqual(emails[0].to, [self.users[0][0]])
        self.assertEqual(emails[0].subject, expected_subject)
        self.assertEqual(emails[0].body, hr_text)

        self.assertEqual(emails[1].to, [self.users[1][0]])
        self.assertEqual(emails[1].subject, expected_subject)
        self.assertEqual(emails[1].body, sup_text)

    def test_email_for_adjustment_forwarded_by_supervisor(self):
        """
        receiver: next level supervisor
        """

        response = self.action_on_adjustment(self.created_users[1], FORWARD)
        emails = mail.outbox

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(emails), 1)

        expected_subject = "Attendance entry adjustment forwarded"
        supervisor2_text = (
            f"{self.created_users[1].full_name} "
            f"forwarded {self.created_users[4].full_name}'s "
            "attendance entry adjustment request "
            f"for {self.timesheet.timesheet_for}."
        )

        self.assertEqual(emails[0].to, [self.users[2][0]])
        self.assertEqual(emails[0].subject, expected_subject)
        self.assertEqual(emails[0].body, supervisor2_text)

    def test_email_for_adjustment_approval_or_denial_by_supervisor(self):
        """
        receiver: requesting user, hr
        """

        for action in [APPROVED, DECLINED]:
            status = action.lower()
            payload_action = APPROVE if action == APPROVED else DENY
            response = self.action_on_adjustment(self.created_users[1], payload_action)
            emails = mail.outbox

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(emails), 2)

            expected_subject = f"Attendance entry adjustment {status}"

            hr_text = (
                f"{self.created_users[1].full_name} has {status} "
                f"{self.created_users[4].full_name}'s "
                "attendance entry adjustment request "
                f"for {self.timesheet.timesheet_for}."
            )
            user_text = (
                f"{self.created_users[1].full_name} has {status} "
                f"your adjust attendance entry request "
                f"for {self.timesheet.timesheet_for}."
            )

            self.assertEqual(emails[0].to, [self.users[0][0]])
            self.assertEqual(emails[1].to, [self.users[4][0]])

            self.assertEqual(emails[0].subject, expected_subject)
            self.assertEqual(emails[1].subject, expected_subject)

            self.assertEqual(emails[0].body, hr_text)
            self.assertEqual(emails[1].body, user_text)

    def test_email_for_adjustment_approval_or_denial_by_hr(self):
        """
        receiver: requesting user
        """

        for action in [APPROVED, DECLINED]:
            status = action.lower()
            payload_action = APPROVE if action == APPROVED else DENY
            response = self.action_on_adjustment(
                self.created_users[0], payload_action, actor="hr"
            )
            emails = mail.outbox

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(emails), 1)

            expected_subject = f"Attendance entry adjustment {status}"
            user_text = (
                f"{self.created_users[0].full_name} has {status} "
                f"your adjust attendance entry request for {self.timesheet.timesheet_for}."
            )

            self.assertEqual(emails[0].to, [self.users[4][0]])
            self.assertEqual(emails[0].subject, expected_subject)
            self.assertEqual(emails[0].body, user_text)

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_ATTENDANCE_ADJUSTMENT=True)
    def test_email_for_adjustment_delete_request_by_user(self):
        """
        receiver: supervisor, hr
        """

        self.make_request()
        self.action_on_adjustment(self.created_users[1])
        self.client.force_login(self.created_users[4])

        url = reverse(
            "api_v1:attendance:update-entries-list",
            kwargs={
                "adjustment_action": "delete",
                "organization_slug": self.organization.slug,
            },
        )

        payload = {
            "timesheet": self.timesheet.id,
            "timesheet_entry": self.timesheet.timesheet_entries.first().id,
            "description": "This field is required now."
        }

        mail.outbox = []
        response = self.client.post(url, data=payload, format="json")
        self.client.logout()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 2)

        expected_subject = "Attendance entry delete request"
        hr_text = (
            f"{self.created_users[4].full_name} has "
            "sent their attendance entry delete request "
            f"for {self.timesheet.timesheet_for}."
        )
        sup_text = (
            f"{self.created_users[4].full_name} has sent "
            "attendance entry delete request "
            f"for {self.timesheet.timesheet_for}."
        )

        emails = mail.outbox
        self.assertEqual(emails[0].to, [self.users[0][0]])
        self.assertEqual(emails[0].subject, expected_subject)
        self.assertEqual(emails[0].body, hr_text)

        self.assertEqual(emails[1].to, [self.users[1][0]])
        self.assertEqual(emails[1].subject, expected_subject)
        self.assertEqual(emails[1].body, sup_text)

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_ATTENDANCE_ADJUSTMENT=True)
    def test_email_is_send_after_timesheet_entry_is_deleted_by_hr(self):
        self.make_request()
        self.action_on_adjustment(self.created_users[0], action=APPROVE, actor="hr")
        self.client.force_login(self.created_users[0])

        mail.outbox = []
        timesheet_entry = self.timesheet.timesheet_entries.first()
        url = reverse(
            "api_v1:attendance:timesheet-entry-delete",
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': self.timesheet.id,
                'timesheet_entry_id': timesheet_entry.id
            },
        )

        response = self.client.post(url, {"description": "Now this field is required."})
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        self.assertEqual(len(mail.outbox), 1)

        expected_subject = "Timesheet Entry Deleted"
        deleted_by = timesheet_entry.modified_by
        user_text = (
            f"Your timesheet entry for {self.timesheet.timesheet_for} has been deleted"
            f" by {deleted_by}"
        )
        emails = mail.outbox
        self.assertEqual(emails[0].to, [self.users[4][0]])
        self.assertEqual(emails[0].subject, expected_subject)
        self.assertEqual(emails[0].body, user_text)
