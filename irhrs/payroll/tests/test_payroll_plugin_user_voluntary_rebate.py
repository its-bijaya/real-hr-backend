from irhrs.organization.models import FiscalYear
from irhrs.payroll.constants import LIFE_INSURANCE, YEARLY, HEALTH_INSURANCE
from irhrs.payroll.models import UserVoluntaryRebateAction, CREATED, RebateSetting
from irhrs.payroll.tests.factory import UserVoluntaryRebateFactory, RebateSettingFactory
from irhrs.payroll.tests.utils import PackageUtil
from irhrs.payroll.tests.test_payroll_calculator_internal_plugins import TestCalculatorInternalPluginsBase


class ExamplePluginOnePackageUtil(PackageUtil):
    RULE_CONFIG = {
        'life_insurance':  {
            'rules': ['200'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        },
        'health_insurance':  {
            'rules': ['500'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        },
        'user_voluntary_rebate_function_heading':  {
            'rules': [
                '__USER_VOLUNTARY_REBATE__("Life Insurance") + '
                '__USER_VOLUNTARY_REBATE__("Health Insurance")'
            ],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        }
    }


class TestUserVoluntaryRebateHeading(TestCalculatorInternalPluginsBase):
    package_util_class = ExamplePluginOnePackageUtil

    def data_setup_before_generation(self):
        self.fiscal_year = FiscalYear.objects.first()
        rebate1 = RebateSetting.objects.get(title=LIFE_INSURANCE)
        self.user_voluntary_rebate = UserVoluntaryRebateFactory(
            user=self.employee,
            amount=1000,
            rebate=rebate1,
            fiscal_year=self.fiscal_year,
            duration_unit=YEARLY
        )
        self.rebate_action = UserVoluntaryRebateAction.objects.create(
            user_voluntary_rebate=self.user_voluntary_rebate,
            action=CREATED,
            remarks="Created"
        )
        rebate2 = RebateSetting.objects.get(title=HEALTH_INSURANCE)
        self.user_voluntary_rebate_two = UserVoluntaryRebateFactory(
            user=self.employee,
            amount=500,
            rebate=rebate2,
            fiscal_year=self.fiscal_year,
            duration_unit=YEARLY
        )
        self.rebate_action = UserVoluntaryRebateAction.objects.create(
            user_voluntary_rebate=self.user_voluntary_rebate_two,
            action=CREATED,
            remarks="Delete Request"
        )
        self.expected = 1000 + 500  # 1000 from LIFE_INSURANCE, 500 from HEALTH_INSURANCE

    def test_annual_amount_function_heading_value(self):
        heading_value = self.get_heading_value('User voluntary rebate function heading')
        self.assertEqual(self.expected, heading_value.get('amount'))
