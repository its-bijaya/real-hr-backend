from datetime import date
from django.db.models.signals import post_save

from irhrs.payroll.signals import create_update_report_row_user_experience_package, \
    update_package_heading_rows
from irhrs.payroll.tests.utils import PackageUtil
from irhrs.payroll.utils.payroll_behaviour_test_helper import PayrollBehaviourTestBaseClass

from irhrs.payroll.models import (
    Payroll,
    Heading, UserExperiencePackageSlot, PackageHeading
)


class PluginPackageUtil(PackageUtil):
    RULE_CONFIG = {
        'addition_with_plugin':  {
            # __TEST_PLUG_TITLE__ is a plugin
            'rules': ['__TEST_PLUG_TITLE__ * 10'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        }
    }


class TestCalculatorInternalPluginsBase(PayrollBehaviourTestBaseClass):
    package_util_class = PluginPackageUtil

    def create_packages(self):
        package_util = self.package_util_class(
            organization=self.organization
        )
        package = package_util.create_package()
        return package

    def data_setup_before_generation(self):
        pass

    def set_employee_payroll(self):

        payrolls_inputs = [
            (
                date(2017, 1, 1),
                date(2017, 1, 31),
            )
        ]

        self.get_payroll(
            *payrolls_inputs[0],
            self.employee
        )

        payrolls = Payroll.objects.filter(
            organization=self.organization,
            from_date=date(2017, 1, 1),
            to_date=date(2017, 1, 31)
        )

        self.payroll_employee = payrolls[0].employee_payrolls.all()[0]

    def setUp(self):
        # disconnected by runner so needed to connect here
        post_save.disconnect(
            create_update_report_row_user_experience_package, sender=UserExperiencePackageSlot
        )
        post_save.disconnect(update_package_heading_rows, sender=PackageHeading)
        super().setUp()
        self.employee = self.created_users[0]
        self.client.force_login(self.admin)
        self.data_setup_before_generation()
        self.set_employee_payroll()

    def get_heading_value(self, heading_name):
        heading_with_plugin = Heading.objects.get(
            name=heading_name
        )

        heading_with_plugin_report_row_record = self.payroll_employee.report_rows.filter(
            heading=heading_with_plugin
        ).values('amount', 'plugin_sources')[0]

        return heading_with_plugin_report_row_record


class ExamplePluginOnePackageUtil(PackageUtil):
    RULE_CONFIG = {
        'addition_with_plugin':  {
            # __TEST_PLUG_TITLE__ is a plugin
            'rules': ['__EXAMPLE_PLUGIN_ONE__ * 10'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        }
    }

class ExampleFunctionPluginOnePackageUtil(PackageUtil):
    RULE_CONFIG = {
        'addition_with_plugin':  {
            # __TEST_PLUG_TITLE__ is a plugin
            'rules': ['__EXAMPLE_FXN_ONE__("arg_one", 10) * 10 '],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        }
    }

class TestInternalExamplePluginOne(TestCalculatorInternalPluginsBase):
    package_util_class = ExampleFunctionPluginOnePackageUtil

    def test_example_plugin_one_value(self):
        heading_value = self.get_heading_value('Addition with plugin')
        print(heading_value)


class TestFunctionInternalExamplePluginOne(TestCalculatorInternalPluginsBase):
    package_util_class = ExamplePluginOnePackageUtil

    def test_example_plugin_one_value(self):
        heading_value = self.get_heading_value('Addition with plugin')
        print(heading_value)
