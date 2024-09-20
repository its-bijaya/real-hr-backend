from django.core.cache import cache
from django.test import TestCase

from irhrs.core.utils import get_system_admin
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, RenewalRuleFactory, LeaveAccountFactory
from irhrs.leave.constants.model_constants import GENERATED
from irhrs.leave.models.account import LeaveEncashment, LeaveEncashmentHistory
from irhrs.leave.tasks import encash_balance


class EncashLeaveTestCase(TestCase):
    def setUp(self) -> None:
        self.master_setting = MasterSettingFactory(
            encashment=True
        )
        self.leave_type = LeaveTypeFactory(
            master_setting=self.master_setting
        )
        self.leave_rule = LeaveRuleFactory(
            leave_type=self.leave_type
        )

        self.renewal_rule = RenewalRuleFactory(
            rule=self.leave_rule,
            max_balance_encashed=20
        )

        self.leave_account = LeaveAccountFactory(
            rule=self.leave_rule
        )
        cache.delete('SYSTEM_BOT')

    def test_encash_balance(self):
        balance_in_hand, encashed_balance = encash_balance(
            self.leave_account,
            20,  # max balance encashed
            30
        )
        self.assertEqual(balance_in_hand, 10)
        self.assertEqual(encashed_balance, 20)

        encashment_instance = LeaveEncashment.objects.filter(
                user=self.leave_account.user,
                account=self.leave_account,
                status=GENERATED,
                balance=encashed_balance
        ).first()
        self.assertIsNotNone(encashment_instance)
        self.assertTrue(
            LeaveEncashmentHistory.objects.filter(
                encashment=encashment_instance,
                actor=get_system_admin(),
                action=GENERATED,
                previous_balance=None,
                new_balance=encashed_balance,
                remarks="encashment added during renewal"
            ).exists()
        )
