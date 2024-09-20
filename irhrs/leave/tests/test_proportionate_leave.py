from datetime import datetime, date
from unittest.mock import patch

from django.utils import timezone

from irhrs.common.api.tests.common import BaseTestCase
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, RenewalRuleFactory, LeaveAccountFactory
from irhrs.leave.tasks import add_pro_rata_leave_balance, renew_balance_to_leave_account, \
    get_proportionate_leave_balance
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory


class ProportionateLeaveBalanceTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.master_setting = MasterSettingFactory(
            proportionate_leave=True
        )
        self.organization = self.master_setting.organization
        self.leave_type = LeaveTypeFactory(
            master_setting=self.master_setting
        )
        self.leave_rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            proportionate_on_joined_date=True,
            proportionate_on_contract_end_date=True
        )

        self.renewal_rule = RenewalRuleFactory(
            rule=self.leave_rule,
            initial_balance=365
        )

        self.leave_account = LeaveAccountFactory(
            rule=self.leave_rule,
            balance=0,
            usable_balance=0
        )
        self.user = self.leave_account.user

        FiscalYearFactory(
            organization=self.organization,
            start_at=date(2017, 1, 1),
            end_at=date(2017, 12, 31),
            applicable_from=date(2017, 1, 1),
            applicable_to=date(2017, 12, 31)
        )

    def test_add_pro_rata_leave_balance(self):

        detail = self.user.detail
        detail.joined_date = date(2017, 2, 1)
        detail.save()

        current_experience = self.user.current_experience

        current_experience.start_date = detail.joined_date
        current_experience.end_date = date(2017, 11, 30)
        current_experience.save()

        # (365 - jan_days - dec_days)
        expected_balance = 365 - 31 - 31

        now_time = datetime(2017, 12, 31, 0, 0, tzinfo=timezone.now().tzinfo)
        with patch('django.utils.timezone.now', return_value=now_time):
            add_pro_rata_leave_balance(self.leave_account)
            self.leave_account.refresh_from_db()
            self.assertEqual(self.leave_account.balance, expected_balance)
            self.assertEqual(self.leave_account.usable_balance, expected_balance)

    def test_add_pro_rata_leave_balance_with_join_date_proportionate_disabled(self):
        self.leave_rule.proportionate_on_joined_date = False
        self.leave_rule.save()

        detail = self.user.detail
        detail.joined_date = date(2017, 2, 1)
        detail.save()

        current_experience = self.user.current_experience

        current_experience.start_date = detail.joined_date
        current_experience.end_date = date(2017, 11, 30)
        current_experience.save()

        # (365 - dec_days)
        expected_balance = 365 - 31

        now_time = datetime(2017, 12, 31, 0, 0, tzinfo=timezone.now().tzinfo)
        with patch('django.utils.timezone.now', return_value=now_time):
            add_pro_rata_leave_balance(self.leave_account)
            self.leave_account.refresh_from_db()
            self.assertEqual(self.leave_account.balance, expected_balance)
            self.assertEqual(self.leave_account.usable_balance, expected_balance)

    def test_renew_balance_to_leave_account(self):
        detail = self.user.detail
        detail.joined_date = date(2016, 2, 1)
        detail.organization = self.organization
        detail.save()

        current_experience = self.user.current_experience

        current_experience.start_date = detail.joined_date
        current_experience.end_date = date(2017, 11, 30)
        current_experience.save()

        expected_balance = 365 - 31 + 10  # carry 10

        now_time = datetime(2017, 12, 31, 0, 0, tzinfo=timezone.now().tzinfo)
        with patch('django.utils.timezone.now', return_value=now_time):
            renew_balance_to_leave_account(
                self.leave_account,
                balance_in_hand=0,
                carry_forward=10
            )
            self.leave_account.refresh_from_db()
            self.assertEqual(self.leave_account.balance, expected_balance)
            self.assertEqual(self.leave_account.usable_balance, expected_balance)

    def test_get_proportionate_leave_balance_util(self):
        rule = self.leave_rule
        cases = [
            (
                True,
                True,
                date(2017, 2, 1),
                date(2017, 11, 30),
                365 - 31 - 31
            ),
            (
                True,
                False,
                date(2017, 2, 1),
                date(2017, 11, 30),
                365 - 31
            ),
            (
                False,
                False,
                date(2017, 2, 1),
                date(2017, 11, 30),
                365
            ),
            (
                False,
                True,
                date(2017, 2, 1),
                date(2017, 11, 30),
                365 - 31
            ),
        ]
        for case in cases:
            (proportionate_on_joined_date, proportionate_on_contract_end_date,
             start, end, expected) = case
            rule.proportionate_on_joined_date = proportionate_on_joined_date
            rule.proportionate_on_contract_end_date = proportionate_on_contract_end_date
            rule.save()
            with patch(
                'irhrs.core.utils.common.get_today',
                return_value=start
            ):
                result = get_proportionate_leave_balance(
                    self.leave_account,
                    start,
                    end
                )
                self.assertEqual(expected, result)
