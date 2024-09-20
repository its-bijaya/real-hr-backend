import datetime
from irhrs.leave.models.settings import MasterSetting
from unittest.mock import patch

from irhrs.core.utils.common import get_tomorrow, get_yesterday
from django.urls import reverse
from rest_framework import status
from irhrs.users.api.v1.tests.factory import UserFactory

from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.leave.api.v1.tests.factory import (
    MasterSettingFactory, LeaveTypeFactory, 
    LeaveRuleFactory, LeaveAccountFactory
)
from irhrs.common.api.tests.common import BaseTestCase
from irhrs.leave.tasks import expire_master_settings


class TestLeaveAccountVisibility(BaseTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.organization = OrganizationFactory()
        self.user = UserFactory(_organization=self.organization)
        self.client.force_login(self.user)
    
    def test_idle_ms_leave_account_not_visible(self):

        # current master setting
        ms_active = MasterSettingFactory(
            organization=self.organization,
            effective_from=datetime.date(2017, 1, 1),
        )
        lt_active = LeaveTypeFactory(
            master_setting=ms_active
        )
        lr_active = LeaveRuleFactory(
            leave_type=lt_active
        )
        la_active = LeaveAccountFactory(
            rule=lr_active,
            user=self.user
        )

        self.assertEqual(
            self.fetch_user_leave_accounts(),
            [la_active.id]
        )

        ms_active.effective_till = get_yesterday()
        ms_active.save()

        with patch('irhrs.core.utils.common.get_today', return_value=get_tomorrow()):
            expire_master_settings()

        self.assertEqual(
            self.fetch_user_leave_accounts(),
            [],
            "Expired Leave Accounts should not be visible."
        )

        # idle master setting
        ms_idle = MasterSettingFactory(
            organization=self.organization,
            effective_from=get_tomorrow(),
        )
        lt_idle = LeaveTypeFactory(
            master_setting=ms_idle
        )
        lr_idle = LeaveRuleFactory(
            leave_type=lt_idle
        )
        la_idle = LeaveAccountFactory(
            rule=lr_idle,
            user=self.user
        )

        accounts = self.fetch_user_leave_accounts()
        self.assertNotIn(
            la_idle.id,
            accounts,
            "Idle leave accounts should be excluded"
        )
        self.assertNotIn(
            ms_idle,
            MasterSetting.objects.filter().active(),
            "Idle Master Setting should not be included in active list."
        )
        with patch('irhrs.core.utils.common.get_today', return_value=get_tomorrow()):
            accounts = self.fetch_user_leave_accounts()
            self.assertIn(
                la_idle.id,
                accounts,
                "Active leave account must be included."
            )



    def fetch_user_leave_accounts(self):
        """Return response from user available accounts"""

        url = reverse(
            'api_v1:leave:user-balance-detail', 
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': self.user.id
            }
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        return [jsn['id'] for jsn in response.json()['results']]
