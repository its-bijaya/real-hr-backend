import os
from datetime import date
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from irhrs.organization.models import Organization
from irhrs.organization.api.v1.tests.factory import OrganizationFactory

from irhrs.payroll.tests.utils import PackageUtil

from irhrs.payroll.models import (
    PayrollVariablePlugin,
    HH_OVERTIME,
    ReportRowRecord,
    Payroll,
    Heading,
    PackageHeading
)

from irhrs.payroll.admin import PayrollVariablePluginForm

from irhrs.payroll.utils.payroll_behaviour_test_helper import PayrollBehaviourTestBaseClass

from rhrs_calc import build_plugin


class PluginPackageUtil(PackageUtil):
    RULE_CONFIG = {
        'addition':  {
            'rules': ['2000'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        },

        'addition_with_plugin':  {
            # __TEST_PLUG_TITLE__ is a plugin
            'rules': ['__TEST_PLUG_TITLE__ * 10'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        },

        'deduction': {
            'rules': ['1000'],
            'payroll_setting_type': 'Social Security Fund', 'type': 'Deduction',
            'duration_unit': 'Monthly', 'taxable': False,
            'absent_days_impact': True
        },
        'overtime': {
            'rules': ['100'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Hourly', 'taxable': True, 'absent_days_impact': False,
            'hourly_heading_source': f'{HH_OVERTIME}'
        },
        'extra_addition_one': {
            'rules': ['0'],
            'payroll_setting_type': 'Fringe Benefits', 'type': 'Extra Addition',
            'duration_unit': None, 'taxable': True, 'absent_days_impact': None
        },
        'extra_deduction_two': {
            'rules': ['0'],
            'payroll_setting_type': 'Expense Settlement', 'type': 'Extra Deduction',
            'duration_unit': None, 'taxable': False, 'absent_days_impact': None
        },
        'total_annual_gross_salary': {
            'rules': ['__ANNUAL_GROSS_SALARY__'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
            'duration_unit': 'Monthly', 'taxable': None, 'absent_days_impact': None
        },
        'tax': {
            'rules': ['0.10 * __TOTAL_ANNUAL_GROSS_SALARY__'],
            'payroll_setting_type': 'Salary TDS',
            'type': 'Tax Deduction', 'duration_unit': None,
            'taxable': None,
            'absent_days_impact': None
        }
    }


class PayrollVariablePluginInstallTest(PayrollBehaviourTestBaseClass):
    is_superuser = True

    def create_packages(self):

        upload_file = open(self.installable_plugin_path, 'rb')
        post_dict = {
            'name': 'Test Plug Title',
            'organization': self.organization.id
        }

        file_dict = {'module': SimpleUploadedFile(
            'plugin_test.zip', upload_file.read())}
        form = PayrollVariablePluginForm(post_dict, file_dict)

        with self.settings(
            GPG_KEY_SERVER='keyserver.ubuntu.com',
            HRIS_KEY_ID='7CD101550CA35EF150E3AC78E5AEBC25530F34AC'
        ):
            self.assertTrue(form.is_valid())
            form.save()

        package_util = PluginPackageUtil(
            organization=self.organization
        )
        package = package_util.create_package()
        return package

    def setUp(self):
        os.environ['PAYROLL_PLUGIN_PRIVATE_KEY_UNLOCK_PASSPHRASE'] = 'sickmetalhead'
        os.environ['PGP_KEY_SERVER'] = 'keyserver.ubuntu.com'
        os.environ['PGP_KEY_ID'] = '7CD101550CA35EF150E3AC78E5AEBC25530F34AC'

        with self.settings(
            GPG_KEY_SERVER='keyserver.ubuntu.com',
            HRIS_KEY_ID='7CD101550CA35EF150E3AC78E5AEBC25530F34AC'
        ):

            src_root = os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)
                ),
                'test_files',
                'plugin_test_files'
            )
            self.installable_plugin_path = build_plugin(src_root=src_root)

        super().setUp()
        self.client.force_login(self.admin)

    def test_plugin_install(self):

        upload_file = open(self.installable_plugin_path, 'rb')
        post_dict = {
            'name': 'Test Plugin Title',
            'organization': self.organization.id
        }

        file_dict = {'module': SimpleUploadedFile(
            'plugin_test.zip', upload_file.read())}
        form = PayrollVariablePluginForm(post_dict, file_dict)

        with self.settings(
            GPG_KEY_SERVER='keyserver.ubuntu.com',
            HRIS_KEY_ID='7CD101550CA35EF150E3AC78E5AEBC25530F34AC'
        ):
            self.assertTrue(form.is_valid())
            form.save()

    def test_basic_plugin_in_action(self):

        payrolls_inputs = [
            (
                date(2017, 1, 1),
                date(2017, 1, 31),
            )
        ]

        self.get_payroll(
            *payrolls_inputs[0],
            self.created_users[0]
        )

        payrolls = Payroll.objects.filter(
            organization=self.organization,
            from_date=date(2017, 1, 1),
            to_date=date(2017, 1, 31)
        )

        heading_with_plugin = Heading.objects.get(
            name='Addition with plugin'
        )

        payroll_employee = payrolls[0].employee_payrolls.all()[0]

        heading_with_plugin_report_row_record = payroll_employee.report_rows.filter(
            heading=heading_with_plugin
        ).values('amount', 'plugin_sources')[0]

        self.assertEquals(
            1000.0,
            heading_with_plugin_report_row_record.get('amount')
        )

        self.assertEquals(
            [{'value': 100, 'source': [{'url': '', 'model_name': 'XYZ', 'instance_id': 2}], 'used_variable_name': '__TEST_PLUG_TITLE__',
                'registered_plugin_name': 'default plugin name', 'registered_plugin_version': 'default.version'}],
            heading_with_plugin_report_row_record.get('plugin_sources')
        )

    def test_get_heading_variables(self):

        url = reverse(
            'api_v1:payroll:heading-get-variables'
        ) + f'?organization__slug={self.organization.slug}'

        data = dict(
            organization__slug=self.organization.slug,
            current_duration_unit=None,
            current_heading_type='Type2Cnst',
            order=Heading.objects.filter(
                organization=self.organization).order_by('order').last().order
        )

        res = self.client.post(
            url,
            data,
            format='json'
        )

        self.assertEquals(res.status_code, 200)

    def test_get_package_heading_variables(self):
        url = reverse(
            'api_v1:payroll:packageheading-get-variables'
        ) + f'?package__organization__slug={self.organization.slug}'

        package = next(
            iter(
                self.user_packages.values()
            )
        )

        data = dict(
            current_duration_unit=None,
            current_heading_type='Type2Cnst',

            order=PackageHeading.objects.filter(
                package=package
            ).order_by('order').last().order,
            package_id=package.id
        )

        res = self.client.post(
            url,
            data,
            format='json'
        )

        self.assertEquals(res.status_code, 200)
