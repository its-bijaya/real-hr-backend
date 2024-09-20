from datetime import datetime

from irhrs.core.constants.payroll import APPROVED
from irhrs.core.utils.common import get_today
from django.test import tag

from irhrs.payroll.tests.test_payroll_calculator_internal_plugins import \
    TestCalculatorInternalPluginsBase
from irhrs.payroll.tests.utils import PackageUtil
from irhrs.reimbursement.api.v1.tests.factory import ExpenseSettlementFactory
from irhrs.reimbursement.models import SettlementHistory


class TestExpenseSettlementPlugin(TestCalculatorInternalPluginsBase):
    class package_util_class(PackageUtil):
        RULE_CONFIG = {
            'addition_with_plugin': {
                # __TEST_PLUG_TITLE__ is a plugin
                'rules': ['__EMPLOYEE_TAXABLE_EXPENSE__ * 10'],
                'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
                'duration_unit': 'Monthly', 'taxable': True,
                'absent_days_impact': True
            }
        }

    def data_setup_before_generation(self):
        tzinfo = get_today(with_time=True).tzinfo
        employee = self.employee

        # included settlements
        self.settlement1 = ExpenseSettlementFactory(
            employee=employee,
            reason="Need Money",
            total_amount=1000,
            status=APPROVED,
            detail={},
            is_taxable=True,
        )
        his = SettlementHistory.objects.create(
            request=self.settlement1,
            action=APPROVED,
        )
        his.created_at = datetime(2017, 1, 1, 10, 0, tzinfo=tzinfo)
        his.save()

        self.settlement2 = ExpenseSettlementFactory(
            employee=employee,
            reason="Need More Money",
            total_amount=500,
            status=APPROVED,
            detail={},
            is_taxable=True,
        )
        his = SettlementHistory.objects.create(
            request=self.settlement2,
            action=APPROVED,
        )
        his.created_at = datetime(2017, 1, 2, 10, 0, tzinfo=tzinfo)
        his.save()
        # end included

        # Excluded ones
        self.settlement3 = ExpenseSettlementFactory(
            employee=employee,
            reason="Need Money Past",
            total_amount=5,
            status=APPROVED,
            detail={},
            is_taxable=True,
        )
        his = SettlementHistory.objects.create(
            request=self.settlement3,
            action=APPROVED,
        )
        his.created_at = datetime(2016, 12, 1, 10, 0, tzinfo=tzinfo)
        his.save()

        self.settlement4 = ExpenseSettlementFactory(
            employee=employee,
            reason="Need Money Future",
            total_amount=10,
            status=APPROVED,
            detail={},
            is_taxable=True,
        )
        his = SettlementHistory.objects.create(
            request=self.settlement4,
            action=APPROVED,
        )
        his.created_at = datetime(2017, 2, 1, 10, 0, tzinfo=tzinfo)
        his.save()
        # End excluded

    @tag("plugin")
    def test_expense_settlement_plugin(self):
        expected = self.settlement1.total_amount + self.settlement2.total_amount
        self.assertEquals(
            self.get_heading_value('Addition with plugin')['amount'],
            expected * 10  # we have * 10 in rule
        )
