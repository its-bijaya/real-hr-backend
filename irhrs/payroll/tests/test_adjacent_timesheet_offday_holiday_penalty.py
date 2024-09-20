from datetime import datetime, timedelta

from django.test import tag

from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import AdjacentTimeSheetOffdayHolidayPenaltyFactory, \
    LeaveAccountFactory
from irhrs.payroll.tests.test_payroll_calculator_internal_plugins import \
    TestCalculatorInternalPluginsBase

from irhrs.payroll.tests.utils import PackageUtil


class TestTimeSheetPenaltyReductionPlugin(TestCalculatorInternalPluginsBase):
    class package_util_class(PackageUtil):
        RULE_CONFIG = {
            'deduction_with_plugin': {
                'rules': ['__ADJACENT_OFFDAY_PENALTY_DAYS__ * 10'],
                'payroll_setting_type': 'Social Security Fund',
                'type': 'Deduction',
                'duration_unit': 'Monthly',
                'taxable': True,
                'absent_days_impact': True
            }
        }

    def data_setup_before_generation(self):
        tzinfo = get_today(with_time=True).tzinfo
        # detail = self.employee.detail
        # detail.last_working_date = "2017-01-05"
        # detail.save()

        # self.employee.refresh_from_db()
        # 2017-1-1 --> 2017-1-31
        def deviate_by(delta):
            return datetime(2017, 1, 1, 19, 0, tzinfo=tzinfo) + timedelta(days=delta)

        leave_account = LeaveAccountFactory(user=self.employee)
        leave_account2 = LeaveAccountFactory(user=self.employee)
        AdjacentTimeSheetOffdayHolidayPenaltyFactory(
            penalty_for=deviate_by(-50),
            leave_account=leave_account
        )
        AdjacentTimeSheetOffdayHolidayPenaltyFactory(
            penalty_for=deviate_by(5),
            leave_account=leave_account
        )
        AdjacentTimeSheetOffdayHolidayPenaltyFactory(
            penalty_for=deviate_by(10),
            leave_account=leave_account
        )
        AdjacentTimeSheetOffdayHolidayPenaltyFactory(
            penalty_for=deviate_by(-2),
            leave_account=leave_account
        )
        AdjacentTimeSheetOffdayHolidayPenaltyFactory(
            penalty_for=deviate_by(15),
            leave_account=leave_account2
        )

        self.expected = 3

    @tag("plugin")
    def test_timesheet_penalty_days_from_plugin(self):
        self.assertEquals(
            self.get_heading_value('Deduction with plugin')['amount'],
            self.expected * 10  # we have * 10 in rule
        )
