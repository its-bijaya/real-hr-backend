from datetime import datetime, timedelta, date

from django.test import tag

from irhrs.attendance.tests.factory import TimeSheetPenaltyToPayrollFactory, \
    TimeSheetUserPenaltyFactory
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.payroll.tests.test_payroll_calculator_internal_plugins import \
    TestCalculatorInternalPluginsBase

from irhrs.payroll.tests.utils import PackageUtil


class TestTimeSheetPenaltyReductionPlugin(TestCalculatorInternalPluginsBase):
    class package_util_class(PackageUtil):
        RULE_CONFIG = {
            'deduction_with_plugin': {
                'rules': ['__DAYS_DEDUCTION_FROM_PENALTY__ * 10'],
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

        fiscal_year = FiscalYearFactory(
            start_at=date(2017, 1, 1),
            applicable_from=date(2017, 1, 1),
            end_at=date(2017, 12, 31),
            applicable_to=date(2017, 12, 31),
        )
        fiscal_month = fiscal_year.fiscal_months.order_by(
            'month_index').first()
        user_penalty = TimeSheetUserPenaltyFactory(
            fiscal_month=fiscal_month,
            user=self.employee
        )
        to_payroll_1 = TimeSheetPenaltyToPayrollFactory(
            confirmed_on=deviate_by(-20),
            days=2,
            user_penalty=user_penalty
        )
        to_payroll_2 = TimeSheetPenaltyToPayrollFactory(
            confirmed_on=deviate_by(0),
            days=5,
            user_penalty=user_penalty
        )
        to_payroll_3 = TimeSheetPenaltyToPayrollFactory(
            confirmed_on=deviate_by(3),
            days=12,
            user_penalty=user_penalty
        )
        to_payroll_4 = TimeSheetPenaltyToPayrollFactory(
            confirmed_on=deviate_by(10),
            days=0.5,
            user_penalty=user_penalty
        )
        to_payroll_5 = TimeSheetPenaltyToPayrollFactory(
            confirmed_on=deviate_by(50),
            days=19,
            user_penalty=user_penalty
        )

        self.expected = (
            to_payroll_2.days + to_payroll_3.days + to_payroll_4.days
        )

    @tag("plugin")
    def test_timesheet_penalty_days_from_plugin(self):
        self.assertEquals(
            self.get_heading_value('Deduction with plugin')['amount'],
            self.expected * 10  # we have * 10 in rule
        )
