from irhrs.payroll.tests.utils import PackageUtil
from irhrs.payroll.tests.test_payroll_calculator_internal_plugins import TestCalculatorInternalPluginsBase

class ExamplePluginOnePackageUtil(PackageUtil):
    RULE_CONFIG = {
        'addition_heading_one':  {
            'rules': ['200'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        },
        'addition_heading_two':  {
            'rules': ['500'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        },
        'annual_amount_function_heading':  {
            'rules': ['__ANNUAL_AMOUNT__("ADDITION HEADING ONE") +  __ANNUAL_AMOUNT__("Addition heading two")'],
            # 'rules': ['__ANNUAL_AMOUNT__("ADDITION HEADING ONE")'],
            # 'rules': ['__ANNUAL_AMOUNT__("Addition heading two")'],
            # 'rules': ['__ANNUAL_AMOUNT__'],
            # 'rules': ['__ANNUAL_AMOUNT__("ADDITION HEADING ONE", "Addition heading two")'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        }
    }

class TestAnnualAmountFunctionHeading(TestCalculatorInternalPluginsBase):
    package_util_class = ExamplePluginOnePackageUtil

    def test_annual_amount_function_heading_value(self):
        heading_value = self.get_heading_value('Annual amount function heading')

        self.assertEqual(8400, heading_value.get('amount'))
