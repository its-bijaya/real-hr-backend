from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from irhrs.attendance.api.v1.tests.factory import AttendanceAdjustmentFactory, TimeSheetFactory
from irhrs.attendance.constants import APPROVED, FORWARDED, DECLINED
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import DummyObject

USER = get_user_model()


class AttendanceAdjustmentBulkActionTest(RHRSAPITestCase):
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

    @property
    def hr(self):
        return self.admin

    def setUp(self):
        super().setUp()
        for i in range(0, 3):
            timesheet = TimeSheetFactory(timesheet_user=self.normal)
            AttendanceAdjustmentFactory(
                timesheet=timesheet,
                receiver=self.supervisor1,
                new_punch_in=timezone.now(),
                sender=self.normal
            )
        self.bulk_action_url = reverse(
            'api_v1:attendance:adjustments-bulk-action',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    @staticmethod
    def _new_approve(s, *args, **kwargs):
        s.status = APPROVED
        s.save()

    def get_valid_data(self):
        data = [
            {
                "adjustment": adj.id,
                "action": ["approve", "forward", "deny"][index],
                "remark": ["Approved", "Forwarded", "Denied"][index]
            }
            for index, adj in enumerate(self.normal.adjustment_requests.all())
        ]
        return data

    def test_valid_action(self):

        with patch(
            'irhrs.attendance.models.adjustments.AttendanceAdjustment.approve',
            self._new_approve
        ), patch(
            'irhrs.attendance.utils.attendance.get_adjustment_request_forwarded_to',
            return_value=DummyObject(supervisor=self.supervisor2)
        ), patch(
            'irhrs.core.utils.subordinates.authority_exists', return_value=True
        ):
            self.client.force_login(self.supervisor1)
            response = self.client.post(
                path=f"{self.bulk_action_url}?as=supervisor",
                data=self.get_valid_data(),
                format='json'
            )

            self.assertEqual(response.status_code, 200)

            self.assertEqual(
                self.normal.adjustment_requests.filter(status=APPROVED).count(),
                1
            )
            self.assertEqual(
                self.normal.adjustment_requests.filter(status=FORWARDED).count(),
                1
            )
            self.assertEqual(
                self.normal.adjustment_requests.filter(status=DECLINED).count(),
                1
            )
            self.assertEqual(
                self.normal.adjustment_requests.filter(status=FORWARDED).first().receiver,
                self.supervisor2
            )

    def test_bulk_action_with_action_not_permitted(self):
        with patch(
            'irhrs.attendance.models.adjustments.AttendanceAdjustment.approve',
            self._new_approve
        ), patch(
            'irhrs.attendance.utils.attendance.get_adjustment_request_forwarded_to',
            return_value=DummyObject(supervisor=self.supervisor2)
        ), patch(
            'irhrs.core.utils.subordinates.authority_exists', return_value=False
        ):
            self.client.force_login(self.supervisor1)
            response = self.client.post(
                path=f"{self.bulk_action_url}?as=supervisor",
                data=self.get_valid_data(),
                format='json'
            )

            self.assertEqual(response.status_code, 400)

            self.assertEqual(
                self.normal.adjustment_requests.filter(status=APPROVED).count(),
                0
            )
            self.assertEqual(
                self.normal.adjustment_requests.filter(status=FORWARDED).count(),
                0
            )
            self.assertEqual(
                self.normal.adjustment_requests.filter(status=DECLINED).count(),
                0
            )

    def test_forward_with_no_forwarded_to(self):
        with patch(
            'irhrs.attendance.utils.attendance.get_adjustment_request_forwarded_to',
            return_value=None
        ), patch(
            'irhrs.core.utils.subordinates.authority_exists', return_value=True
        ):
            data = [{
              'adjustment': self.normal.adjustment_requests.first().id,
              'action': 'forward',
              'remark': 'Forwarded'
            }]

            self.client.force_login(self.supervisor1)
            response = self.client.post(
                path=f"{self.bulk_action_url}?as=supervisor",
                data=data,
                format='json'
            )

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                self.normal.adjustment_requests.filter(status=FORWARDED).count(),
                0
            )
