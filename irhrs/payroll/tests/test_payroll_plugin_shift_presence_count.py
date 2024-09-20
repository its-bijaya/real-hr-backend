from irhrs.attendance.api.v1.tests.factory import WorkShiftFactory
from irhrs.attendance.api.v1.tests.factory import TimeSheetFactory
from irhrs.payroll.tests.utils import PackageUtil
from irhrs.payroll.tests.test_payroll_calculator_internal_plugins import TestCalculatorInternalPluginsBase


class ShiftPresenceCountPackageUtil(PackageUtil):
    RULE_CONFIG = {
        'shift_presence_count_heading': {
            'rules': [
                '__SHIFT_PRESENCE_COUNT__("Morning")'
            ],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        }
    }


class TestWorkShiftPresenceCount(TestCalculatorInternalPluginsBase):
    package_util_class = ShiftPresenceCountPackageUtil

    def create_packages(self):
        WorkShiftFactory(organization=self.organization, name="Morning")
        package_util = self.package_util_class(
            organization=self.organization
        )
        package = package_util.create_package()
        return package

    def data_setup_before_generation(self):
        TimeSheetFactory(
            timesheet_user=self.employee,
            timesheet_for="2017-01-02",
            work_shift__name="Morning",
            is_present=True,
        )
        TimeSheetFactory(
            timesheet_user=self.employee,
            timesheet_for="2017-01-04",
            work_shift__name="Morning",
            is_present=True,
        )
        self.expected = 2

    def test_shift_presence_count_heading_value(self):
        heading_value = self.get_heading_value('Shift presence count heading')
        self.assertEqual(self.expected, heading_value.get('amount'))
