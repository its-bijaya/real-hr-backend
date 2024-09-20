from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.leave.api.v1.tests.factory import LeaveAccountFactory, LeaveRuleFactory, \
    LeaveTypeFactory, MasterSettingFactory, LeaveRequestFactory
from irhrs.leave.constants.model_constants import APPROVED, FORWARDED, DENIED, REQUESTED, SUPERVISOR

USER = get_user_model()


class LeaveRequestBulkActionTest(RHRSAPITestCase):
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
        master_settings = MasterSettingFactory(organization=self.organization)
        leave_type = LeaveTypeFactory(master_setting=master_settings)
        rule = LeaveRuleFactory(leave_type=leave_type)
        account = LeaveAccountFactory(user=self.normal, rule=rule)
        for i in range(0, 3):
            LeaveRequestFactory(
                user=self.normal,
                recipient=self.supervisor1,
                leave_rule=rule,
                leave_account=account,
                start=timezone.now() + timezone.timedelta(days=i),
                end=timezone.now() + timezone.timedelta(days=i+1),
                balance=1
            )

        self.bulk_action_url = reverse(
            'api_v1:leave:leave-request-bulk-action',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def get_valid_data(self):
        data = [
            {
                "leave_request": lr.id,
                "action": ["approve", "forward", "deny"][index],
                "remark": ["Approved", "Forwarded", "Denied"][index]
            }
            for index, lr in enumerate(self.normal.leave_requests.all())
        ]
        return data

    def test_valid_data(self):
        with patch(
            'irhrs.core.utils.subordinates.authority_exists', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_request.get_appropriate_recipient',
            return_value=self.supervisor2
        ), patch(
            'irhrs.leave.utils.leave_request.get_leave_request_recipient',
            return_value=(self.supervisor2, SUPERVISOR, APPROVED)
        ), patch(
            'irhrs.leave.utils.leave_request.get_authority',
            return_value=0
        ), patch(
            'irhrs.leave.api.v1.serializers.leave_request.LeaveRequestHelper'
            '.manage_time_sheets_and_overtime',
            return_value=None
        ):

            self.client.force_login(self.supervisor1)
            response = self.client.post(
                path=f"{self.bulk_action_url}?as=supervisor",
                data=self.get_valid_data(),
                format='json'
            )

            self.assertEqual(response.status_code, 200)

            # after actions, approved, forwarded, denied count should be 1
            self.assertEqual(
                self.normal.leave_requests.filter(status=APPROVED).count(),
                1
            )
            self.assertEqual(
                self.normal.leave_requests.filter(status=FORWARDED).count(),
                1
            )
            self.assertEqual(
                self.normal.leave_requests.filter(status=DENIED).count(),
                1
            )
            self.assertEqual(
                self.normal.leave_requests.filter(status=FORWARDED).first().recipient,
                self.supervisor2
            )

    def test_with_action_not_permitted(self):
        with patch(
            'irhrs.core.utils.subordinates.authority_exists', return_value=False
        ), patch(
            'irhrs.leave.utils.leave_request.get_appropriate_recipient',
            return_value=self.supervisor2
        ), patch(
            'irhrs.leave.utils.leave_request.get_leave_request_recipient',
            return_value=self.supervisor2
        ), patch(
            'irhrs.leave.utils.leave_request.get_authority',
            return_value=0
        ), patch(
            'irhrs.leave.api.v1.serializers.leave_request.LeaveRequestHelper'
            '.manage_time_sheets_and_overtime',
            return_value=None
        ):
            self.client.force_login(self.supervisor1)
            response = self.client.post(
                path=f"{self.bulk_action_url}?as=supervisor",
                data=self.get_valid_data(),
                format='json'
            )

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                self.normal.leave_requests.filter(status=REQUESTED).count(),
                3
            )

    def test_forward_with_no_forwarded_to(self):
        with patch(
            'irhrs.core.utils.subordinates.authority_exists', return_value=True
        ), patch(
            'irhrs.leave.utils.leave_request.get_appropriate_recipient',
            return_value=None
        ), patch(
            'irhrs.leave.utils.leave_request.get_leave_request_recipient',
            return_value=None
        ), patch(
            'irhrs.leave.utils.leave_request.get_authority',
            return_value=0
        ), patch(
            'irhrs.leave.api.v1.serializers.leave_request.LeaveRequestHelper'
            '.manage_time_sheets_and_overtime',
            return_value=None
        ):
            data = [{
              'leave_request': self.normal.leave_requests.first().id,
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
                self.normal.leave_requests.filter(status=FORWARDED).count(),
                0
            )
