from datetime import datetime

from django.test import tag

from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import LeaveEncashmentFactory
from irhrs.leave.constants.model_constants import APPROVED, LEAVE_RENEW, EMPLOYEE_SEPARATION
from irhrs.payroll.tests.test_payroll_calculator_internal_plugins import \
    TestCalculatorInternalPluginsBase

from irhrs.payroll.tests.utils import PackageUtil


class TestLeaveEncashmentFromRenewPlugin(TestCalculatorInternalPluginsBase):
    class package_util_class(PackageUtil):
        RULE_CONFIG = {
            'addition_with_plugin': {
                # __TEST_PLUG_TITLE__ is a plugin
                'rules': ['__EMPLOYEE_LEAVE_ENCASHMENT_FROM_OFF_BOARDING__ * 10'],
                'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
                'duration_unit': 'Monthly', 'taxable': True,
                'absent_days_impact': True
            }
        }

    def data_setup_before_generation(self):
        tzinfo = get_today(with_time=True).tzinfo
        detail = self.employee.detail
        detail.last_working_date = "2017-01-05"
        detail.save()

        self.employee.refresh_from_db()

        self.encashment1 = LeaveEncashmentFactory(
            user=self.employee,
            status=APPROVED,
            approved_on=datetime(2017, 1, 2, 10, 0, tzinfo=tzinfo),
            balance=200,
            source=EMPLOYEE_SEPARATION
        )
        self.encashment2 = LeaveEncashmentFactory(
            user=self.employee,
            status=APPROVED,
            approved_on=datetime(2017, 1, 3, 10, 0, tzinfo=tzinfo),
            balance=150,
            source=EMPLOYEE_SEPARATION
        )
        self.encashment3 = LeaveEncashmentFactory(
            user=self.employee,
            status=APPROVED,
            approved_on=datetime(2016, 12, 3, 10, 0, tzinfo=tzinfo),
            balance=5,
            source=EMPLOYEE_SEPARATION
        )
        self.encashment4 = LeaveEncashmentFactory(
            user=self.employee,
            status=APPROVED,
            approved_on=datetime(2017, 2, 3, 10, 0, tzinfo=tzinfo),
            balance=25,
            source=LEAVE_RENEW
        )
        self.encashment5 = LeaveEncashmentFactory(
            user=self.employee,
            status=APPROVED,
            approved_on=datetime(2017, 1, 3, 10, 0, tzinfo=tzinfo),
            balance=111,
            source=LEAVE_RENEW
        )
        self.expected = (
            self.encashment1.balance + self.encashment2.balance + self.encashment3.balance
        )

    @tag("plugin")
    def test_leave_encashment_from_renew_plugin(self):
        self.assertEquals(
            self.get_heading_value('Addition with plugin')['amount'],
            self.expected * 10  # we have * 10 in rule
        )
