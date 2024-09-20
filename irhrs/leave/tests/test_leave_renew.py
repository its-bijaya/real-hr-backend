from datetime import date, datetime
from unittest.mock import patch
from django.utils import timezone

from irhrs.common.api.tests.common import BaseTestCase
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, RenewalRuleFactory, LeaveAccountFactory
from irhrs.leave.tasks import renew_leave_balance
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory, OrganizationFactory
from irhrs.users.api.v1.tests.factory import UserFactory


class TestLeaveRenewTask(BaseTestCase):
    def test_leave_renew_at_fiscal_end(self):
        end_at = date(2017, 12, 31)
        organization = OrganizationFactory()
        user = UserFactory(_organization=organization)
        fiscal_year = FiscalYearFactory(
            organization=organization,
            start_at=date(2017, 1, 1),
            end_at=end_at,
            applicable_from=date(2017, 1, 1),
            applicable_to=end_at
        )
        master_setting = MasterSettingFactory(
            renewal=True,
            organization=organization,
            effective_from=fiscal_year.start_at
        )
        leave_type = LeaveTypeFactory(master_setting=master_setting)
        leave_rule = LeaveRuleFactory(leave_type=leave_type)
        RenewalRuleFactory(
            duration=1,  # 1 year
            rule=leave_rule,
            initial_balance=(fiscal_year.end_at-fiscal_year.start_at).days
        )
        account = LeaveAccountFactory(rule=leave_rule, user=user, usable_balance=0, balance=0)
        account.last_renewed = timezone.make_aware(datetime(2017, 12, 30, 12, 12))
        account.save()
        with patch(
            'irhrs.leave.tasks.get_next_renew_date', return_value=end_at
        ):
            renew_leave_balance()
        self.assertEqual(
            user.leave_accounts.get().usable_balance,
            account.rule.renewal_rule.initial_balance
        )
        end_at = date(2018, 12, 31)
        start_at=date(2018, 1, 1)
        FiscalYearFactory(
            organization=organization,
            start_at=start_at,
            end_at=end_at,
            applicable_from=start_at,
            applicable_to=end_at
        )
        with patch(
            'irhrs.leave.tasks.get_next_renew_date', return_value=end_at
        ), patch(
            'django.utils.timezone.now', return_value=timezone.make_aware(datetime(2018, 12, 31, 23, 59))
        ):
            renew_leave_balance()
        self.assertEqual(
            user.leave_accounts.get().usable_balance,
            account.rule.renewal_rule.initial_balance, 
            "Balance should not be added in second renewal."
        )
