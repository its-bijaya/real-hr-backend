from datetime import date

from irhrs.common.api.tests.factory import DutyStationFactory
from irhrs.hris.api.v1.tests.factory import DutyStationAssignmentFactory
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.payroll.tests.test_payroll_calculator_internal_plugins import TestCalculatorInternalPluginsBase
from django.test import tag

from irhrs.payroll.tests.utils import PackageUtil


class TestDutyStationRebatePlugin(TestCalculatorInternalPluginsBase):
    class package_util_class(PackageUtil):
        RULE_CONFIG = {
            'addition_with_plugin': {
                # __TEST_PLUG_TITLE__ is a plugin
                'rules': ['__EMPLOYEE_DUTY_STATION_REBATE__ * 10'],
                'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
                'duration_unit': 'Monthly', 'taxable': True,
                'absent_days_impact': True
            }
        }

    def data_setup_before_generation(self):
        FiscalYearFactory(
            start_at=date(2017, 1, 1),
            end_at=date(2017, 12, 31),
            applicable_from=date(2017, 1, 1),
            applicable_to=date(2017, 12, 31)
        )
        self.duty_station1 = DutyStationFactory(name="A", amount=365)
        self.duty_station2 = DutyStationFactory(name="B", amount=365*2)

        self.assignment0 = DutyStationAssignmentFactory(
            from_date='2016-12-01',
            to_date='2016-12-04',
            organization=self.organization,
            user=self.employee,
            duty_station=self.duty_station1
        )  # amount = 0 (excluded)
        self.assignment1 = DutyStationAssignmentFactory(
            from_date='2016-12-31',
            to_date='2017-01-03',
            organization=self.organization,
            user=self.employee,
            duty_station=self.duty_station1
        )  # amount = 3 (3 days included)
        self.assignment2 = DutyStationAssignmentFactory(
            from_date='2017-01-05',
            to_date='2017-01-06',
            organization=self.organization,
            user=self.employee,
            duty_station=self.duty_station1
        )  # amount = 2 (2 days)
        self.assignment3 = DutyStationAssignmentFactory(
            from_date='2017-01-08',
            to_date='2017-01-09',
            organization=self.organization,
            user=self.employee,
            duty_station=self.duty_station2
        )  # amount = 4 (2 days * 2)
        self.assignment4 = DutyStationAssignmentFactory(
            from_date='2017-01-29',
            to_date='2017-02-05',
            organization=self.organization,
            user=self.employee,
            duty_station=self.duty_station2
        )  # amount = 16 (8 days included * 2)
        self.assignment5 = DutyStationAssignmentFactory(
            from_date='2017-02-12',
            to_date='2017-02-13',
            organization=self.organization,
            user=self.employee,
            duty_station=self.duty_station2
        )  # amount = 4 (2 days included *2)

        self.expected = 3 + 2 + 4 + 16 + 4

    @tag("plugin")
    def test_duty_station_rebate_plugin(self):
        heading_value = self.get_heading_value('Addition with plugin')['amount']
        self.assertEquals(
            heading_value,
            self.expected * 10  # we have * 10 in rule
        )
