from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from irhrs.attendance.api.v1.tests.factory import (
    OvertimeSettingFactory,
    TimeSheetFactory,
)
from irhrs.attendance.constants import (
    REQUESTED,
    APPROVED,
    FORWARDED,
    DECLINED,
    CONFIRMED,
)
from irhrs.attendance.models import OvertimeEntry, OvertimeClaim
from irhrs.common.api.tests.common import RHRSAPITestCase, RHRSTestCaseWithExperience
from django.core import mail

from irhrs.users.models.supervisor_authority import UserSupervisor


USER = get_user_model()


def can_send_email(user, email_type):
    return True


class OverTimeClaimBulkActionTest(RHRSAPITestCase):
    organization_name = "ALPL"
    users = [
        ("hr@email.com", "password", "Female"),
        ("supervisorone@email.com", "password", "Female"),
        ("supervisortwo@email.com", "password", "Male"),
        ("normal@email.com", "password", "Male"),
    ]

    @property
    def normal(self):
        return USER.objects.get(email="normal@email.com")

    @property
    def supervisor1(self):
        return USER.objects.get(email="supervisorone@email.com")

    @property
    def supervisor2(self):
        return USER.objects.get(email="supervisortwo@email.com")

    @property
    def hr(self):
        return self.admin

    def setUp(self):
        super().setUp()
        ot_setting = OvertimeSettingFactory(organization=self.organization)

        for i in range(1, 4):
            ot_entry = OvertimeEntry.objects.create(
                overtime_settings=ot_setting,
                timesheet=TimeSheetFactory(
                    timesheet_user=self.normal,
                    timesheet_for=timezone.now() - timezone.timedelta(days=i),
                ),
                user=self.normal,
            )
            OvertimeClaim.objects.create(
                overtime_entry=ot_entry,
                status=REQUESTED,
                description="blah",
                recipient=self.supervisor1,
                is_archived=False,
            )
        self.bulk_action_url = reverse(
            "api_v1:attendance:overtime-claims-bulk-action",
            kwargs={"organization_slug": self.organization.slug},
        )

    def get_ot_claim_qs(self):
        return OvertimeClaim.objects.filter(overtime_entry__user=self.normal)

    def get_valid_data(self):
        data = [
            {
                "overtime_claim": ot_claim.id,
                "action": ["approve", "forward", "deny"][index],
                "remark": ["Approved", "Forwarded", "Denied"][index],
            }
            for index, ot_claim in enumerate(self.get_ot_claim_qs())
        ]
        return data

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_OVERTIME=True)
    def test_valid_action(self):
        with patch(
            "irhrs.core.utils.subordinates.authority_exists", return_value=True
        ), patch(
            "irhrs.attendance.utils.helpers.get_overtime_recipient",
            return_value=self.supervisor2,
        ), patch(
            "irhrs.users.managers.UserQueryset.current",
            return_value=USER.objects.all(),  # all users are current
        ):
            self.client.force_login(self.supervisor1)
            with patch("irhrs.core.utils.email.can_send_email", can_send_email):
                response = self.client.post(
                    path=f"{self.bulk_action_url}?as=supervisor",
                    data=self.get_valid_data(),
                    format="json",
                )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(mail.outbox), 6)
            mail_instance = mail.outbox[0]

            receiver = "hr@email.com"
            self.assertEqual(mail_instance.to[0], receiver)

            expected_subject = "Overtime claim request has been approved"
            self.assertEqual(mail_instance.subject, expected_subject)

            text = mail_instance.body.split(" ")
            date = text[-1]
            expected_emailText = (
                f"supervisorone supervisorone has approved normal normal's "
                f"system generated overtime for "
                f"{date}"
            )
            self.assertEqual(mail_instance.body, expected_emailText)

            mail_instance = mail.outbox[1]
            receiver = "normal@email.com"
            self.assertEqual(mail_instance.to[0], receiver)

            expected_subject = "Overtime claim request has been approved"
            self.assertEqual(mail_instance.subject, expected_subject)

            text = mail_instance.body.split(" ")
            date = text[-1]
            expected_emailText = (
                f"supervisorone supervisorone has Approved your overtime request for "
                f"{date}"
            )
            self.assertEqual(mail_instance.body, expected_emailText)

            mail_instance = mail.outbox[2]
            receiver = "hr@email.com"
            self.assertEqual(mail_instance.to[0], receiver)

            expected_subject = "Overtime claim Forwarded"
            self.assertEqual(mail_instance.subject, expected_subject)

            text = mail_instance.body.split(" ")
            date = text[-1]
            expected_emailText = (
                f"supervisorone supervisorone has forwarded normal normal's "
                f"system generated overtime for {date}"
            )
            self.assertEqual(mail_instance.body, expected_emailText)

            mail_instance = mail.outbox[3]
            receiver = "supervisortwo@email.com"
            self.assertEqual(mail_instance.to[0], receiver)

            expected_subject = "Overtime claim Forwarded"
            self.assertEqual(mail_instance.subject, expected_subject)

            text = mail_instance.body.split(" ")
            date = text[-1]
            expected_emailText = (
                f"supervisorone supervisorone forwarded normal normal's "
                f"overtime for {date}"
            )
            self.assertEqual(mail_instance.body, expected_emailText)

            self.assertEqual(self.get_ot_claim_qs().filter(status=APPROVED).count(), 1)
            self.assertEqual(self.get_ot_claim_qs().filter(status=FORWARDED).count(), 1)
            self.assertEqual(self.get_ot_claim_qs().filter(status=DECLINED).count(), 1)
            self.assertEqual(
                self.get_ot_claim_qs().filter(status=FORWARDED).first().recipient,
                self.supervisor2,
            )

    @override_settings(SHADOW_NOTIFY_ORGANIZATION_OVERTIME=True)
    def test_hr_confirm_request(self):
        with patch(
            "irhrs.users.managers.UserQueryset.current",
            return_value=USER.objects.all(),  # all users are current
        ):

            self.client.force_login(self.hr)
            with patch("irhrs.core.utils.email.can_send_email", can_send_email):
                response = self.client.post(
                    path=f"{self.bulk_action_url}?as=hr",
                    data=[
                        {
                            "overtime_claim": self.get_ot_claim_qs().first().id,
                            "action": "confirm",
                            "remark": "confirm",
                        }
                    ],
                    format="json",
                )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(mail.outbox), 2)
            mail_instance = mail.outbox[0]

            receiver = "hr@email.com"
            self.assertEqual(mail_instance.to[0], receiver)

            expected_subject = "Overtime Confirmed"
            self.assertEqual(mail_instance.subject, expected_subject)

            text = mail_instance.body.split(" ")
            date = text[-1]
            expected_emailText = (
                f"hr hr has confirmed normal normal's "
                f"system generated overtime for {date}"
            )
            self.assertEqual(mail_instance.body, expected_emailText)

            self.assertEqual(self.get_ot_claim_qs().filter(status=CONFIRMED).count(), 1)

    def test_not_allowed_actions(self):

        with patch(
            "irhrs.core.utils.subordinates.authority_exists", return_value=False
        ), patch(
            "irhrs.attendance.utils.helpers.get_overtime_recipient",
            return_value=self.supervisor2,
        ), patch(
            "irhrs.users.managers.UserQueryset.current",
            return_value=USER.objects.all(),  # all users are current
        ):
            self.client.force_login(self.supervisor1)
            with patch("irhrs.core.utils.email.can_send_email", can_send_email):
                response = self.client.post(
                    path=f"{self.bulk_action_url}?as=supervisor",
                    data=self.get_valid_data(),
                    format="json",
                )
            self.assertEqual(response.status_code, 400)

            self.assertEqual(len(mail.outbox), 0)

            self.assertEqual(self.get_ot_claim_qs().filter(status=APPROVED).count(), 0)
            self.assertEqual(self.get_ot_claim_qs().filter(status=FORWARDED).count(), 0)
            self.assertEqual(self.get_ot_claim_qs().filter(status=DECLINED).count(), 0)


class OverTimeClaimBulkForwardTest(RHRSTestCaseWithExperience):
    organization_name = "ALPL"
    users = [
        ("hr@email.com", "password", "Female", "hr"),
        ("supervisorone@email.com", "password", "Female", "supervisor"),
        ("supervisortwo@email.com", "password", "Male", "supervisor"),
        ("supervisorthree@email.com", "password", "Female", "supervisor"),
        ("normal@email.com", "password", "Male", "intern"),
    ]

    def setUp(self):
        super().setUp()
        ot_setting = OvertimeSettingFactory(organization=self.organization)

        for i in range(1, 4):
            ot_entry = OvertimeEntry.objects.create(
                overtime_settings=ot_setting,
                timesheet=TimeSheetFactory(
                    timesheet_user=self.normal,
                    timesheet_for=timezone.now() - timezone.timedelta(days=i),
                ),
                user=self.normal,
            )
            OvertimeClaim.objects.create(
                overtime_entry=ot_entry,
                status=REQUESTED,
                description="blah",
                recipient=self.supervisor1,
                is_archived=False,
            )
        self.bulk_action_url = reverse(
            "api_v1:attendance:overtime-claims-bulk-action",
            kwargs={"organization_slug": self.organization.slug},
        )

    @property
    def normal(self):
        return USER.objects.get(email="normal@email.com")

    @property
    def supervisor1(self):
        return USER.objects.get(email="supervisorone@email.com")

    @property
    def supervisor2(self):
        return USER.objects.get(email="supervisortwo@email.com")

    @property
    def supervisor3(self):
        return USER.objects.get(email="supervisorthree@email.com")

    def get_ot_claim_qs(self):
        return OvertimeClaim.objects.filter(overtime_entry__user=self.normal)

    def test_overtimeclaim_bulk_forward(self):
        UserSupervisor.objects.bulk_create(
            [
                UserSupervisor(
                    user=self.normal,
                    supervisor=self.created_users[i],
                    authority_order=i,
                    approve=True,
                    deny=True,
                    forward=True,
                )
                for i in range(1, 4)
            ]
        )
        url = (
            reverse(
                "api_v1:attendance:overtime-claims-bulk-action",
                kwargs={"organization_slug": self.organization.slug},
            )
            + "?as=supervisor"
        )
        ot_claim = self.get_ot_claim_qs().first()
        self.client.force_login(self.supervisor1)
        payload = [
            {"overtime_claim": ot_claim.id, "action": "forward", "remark": "forward"}
        ]
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 200, response.json)

        ot_claim.refresh_from_db()
        self.assertEqual(ot_claim.status, "Forwarded")
        self.assertEqual(ot_claim.recipient, self.supervisor2)

        self.client.force_login(self.supervisor2)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 200)

        ot_claim.refresh_from_db()
        self.assertEqual(ot_claim.status, "Forwarded")
        self.assertEqual(ot_claim.recipient, self.supervisor3)

    def test_overtimeclaim_cannot_forward(self):
        UserSupervisor(
            user=self.normal,
            supervisor=self.supervisor1,
            authority_order=1,
            approve=True,
            deny=False,
            forward=True,
        )
        url = (
            reverse(
                "api_v1:attendance:overtime-claims-bulk-action",
                kwargs={"organization_slug": self.organization.slug},
            )
            + "?as=supervisor"
        )

        ot_claim = self.get_ot_claim_qs().first()
        self.client.force_login(self.supervisor1)
        self.created_users[2].delete()
        payload = [
            {"overtime_claim": ot_claim.id, "action": "forward", "remark": "confirm"}
        ]

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()[0]['action'][0],
            'You can not forward this request.',
        )
