"""
from datetime import time

from irhrs.common.api.tests.common import BaseTestCase as TestCase

from dateutil.relativedelta import relativedelta

from irhrs.core.utils.common import combine_aware
from irhrs.leave.constants.model_constants import DAYS, YEARS, MONTHS
from irhrs.leave.tasks import accrue_balance_to_leave_account, get_next_accrue_date
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from .factory import *


class DoNotTestLeaveAccrualTask(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.master_setting = MasterSettingFactory()
        self.leave_type = LeaveTypeFactory(master_setting=self.master_setting)

    def test_accrual_for_normal_days(self):
        for balance_add, balance_every in [
            (random.randint(1, 10), random.randint(10, 100)) for _ in range(10)
        ]:
            every = random.choice([DAYS, MONTHS, YEARS])
            x_range_ago = lambda x: timezone.now() - {
                DAYS: relativedelta(days=x),
                MONTHS: relativedelta(months=x),
                YEARS: relativedelta(years=x)
            }.get(
                every
            )
            initial_balance = random.randint(1, 10)
            initial_usable = random.randint(1, 10)
            self.leave_rule = LeaveRuleFactory(leave_type=self.leave_type)
            self.accumulation_rule = AccumulationRuleFactory(
                rule=self.leave_rule,
                duration=balance_every,
                duration_type=every,
                balance_added=balance_add,
            )

            leave_account = LeaveAccountFactory(
                balance=initial_balance,
                usable_balance=initial_usable,
                rule=self.leave_rule,
                last_accrued=x_range_ago(balance_every),
                next_accrue=x_range_ago(0)
            )

            # Finally here
            accrue_balance_to_leave_account(leave_account)

            self.assertEqual(
                leave_account.balance, initial_balance + balance_add,
                f"The actual balance should be "
                f"{initial_balance + balance_add}. It is "
                f"{leave_account.balance}"
            )
            self.assertEqual(
                leave_account.usable_balance, initial_usable + balance_add,
                f"The actual balance should be "
                f"{initial_usable + balance_add}. It is "
                f"{leave_account.usable_balance}"
            )

    def test_accural_for_missed_date(self):

        for balance_add, balance_every, every in [
            (10, 20, DAYS),
            (10, 20, MONTHS),
            (10, 20, YEARS),
        ]:
            x_range_ago = lambda x: timezone.now() - {
                DAYS: relativedelta(days=x),
                MONTHS: relativedelta(months=x),
                YEARS: relativedelta(years=x)
            }.get(
                every
            )
            initial_balance = 0
            initial_usable = 0
            self.leave_rule = LeaveRuleFactory(leave_type=self.leave_type)
            self.accumulation_rule = AccumulationRuleFactory(
                rule=self.leave_rule,
                duration=balance_every,
                duration_type=every,
                balance_added=balance_add,
            )
            for x in range(0, 7):
                leave_account = LeaveAccountFactory(
                    user=UserFactory(),
                    balance=initial_balance,
                    usable_balance=initial_usable,
                    rule=self.leave_rule,
                    last_accrued=x_range_ago(balance_every),
                    next_accrue=x_range_ago(x)
                )
                expected_next_accrue = timezone.now().date(
                ) + {
                                           DAYS: relativedelta(days=(balance_every - x)),
                                           MONTHS: relativedelta(months=(balance_every - x)),
                                           YEARS: relativedelta(years=(balance_every - x))
                                       }.get(
                    every
                )
                accrue_balance_to_leave_account(leave_account)

                self.assertEqual(
                    leave_account.balance, initial_balance + balance_add,
                    f"The actual balance should be "
                    f"{initial_balance + balance_add}. It is "
                    f"{leave_account.balance}"
                )
                self.assertEqual(
                    leave_account.usable_balance, initial_usable + balance_add,
                    f"The actual balance should be "
                    f"{initial_usable + balance_add}. It is "
                    f"{leave_account.usable_balance}"
                )
            for x in range(8, 20):
                leave_account = LeaveAccountFactory(
                    balance=initial_balance,
                    usable_balance=initial_usable,
                    rule=self.leave_rule,
                    last_accrued=x_range_ago(x + balance_every),
                    next_accrue=x_range_ago(x)
                )

                _, bias = divmod(x, balance_every)
                x = balance_every - bias
                expected_next_accrue = timezone.now().date(
                ) + {
                                           DAYS: relativedelta(days=x),
                                           MONTHS: relativedelta(months=x),
                                           YEARS: relativedelta(years=x)
                                       }.get(
                    every
                )
                accrue_balance_to_leave_account(leave_account)


class DoNotTestLeaveAccrualTaskFiscalWise(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.master_setting = MasterSettingFactory()
        self.leave_type = LeaveTypeFactory(master_setting=self.master_setting)

    def test_accrual_for_fiscal_setting(self):
        for balance_add in [
            random.randint(1, 10) for _ in range(10)
        ]:
            balance_every = 1
            every = MONTHS
            x_range_ago = lambda x: timezone.now() - {
                DAYS: relativedelta(days=x),
                MONTHS: relativedelta(months=x),
                YEARS: relativedelta(years=x)
            }.get(
                every
            )
            initial_balance = random.randint(1, 10)
            initial_usable = random.randint(1, 10)
            self.leave_rule = LeaveRuleFactory(leave_type=self.leave_type)
            self.accumulation_rule = AccumulationRuleFactory(
                rule=self.leave_rule,
                duration=balance_every,
                duration_type=every,
                balance_added=balance_add,
            )
            leave_account = LeaveAccountFactory(
                balance=initial_balance,
                usable_balance=initial_usable,
                rule=self.leave_rule,
                last_accrued=x_range_ago(balance_every),
                next_accrue=x_range_ago(0)
            )

            fy = FiscalYearFactory(
                organization=leave_account.user.detail.organization,
                start_at=timezone.now().date() - relativedelta(years=2),
                end_at=timezone.now().date() - relativedelta(years=1)
            )
            fiscal_month = fy.fiscal_months.filter(
            ).order_by('?').first()
            last_accrued_date = combine_aware(
                fiscal_month.start_at + relativedelta(days=5),
                time(0, 0)
            )
            leave_account.last_accrued = last_accrued_date
            leave_account.refresh_from_db()
            # Finally here
            accrue_balance_to_leave_account(leave_account)
            try:
                self.assertEqual(
                    leave_account.balance, initial_balance + balance_add,
                    f"The actual balance should be "
                    f"{initial_balance + balance_add}. It is "
                    f"{leave_account.balance}"
                )
                self.assertEqual(
                    leave_account.usable_balance, initial_usable + balance_add,
                    f"The actual balance should be "
                    f"{initial_usable + balance_add}. It is "
                    f"{leave_account.usable_balance}"
                )
            except Exception as e:
                print(str(e))
                print('=-' * 5, 'LOCALS-=')
                print(locals())
                raise e
"""
