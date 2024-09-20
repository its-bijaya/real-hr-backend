import os
import shutil
import requests
from datetime import date
from django.conf import settings
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
        'addition_with_plugin':  {
            # __TEST_PLUG_TITLE__ is a plugin
            'rules': ['__TEST_PLUG_TITLE__ * 10'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        }
    }


class PayrollPluginTestBase(PayrollBehaviourTestBaseClass):
    plugin_name = ''
    plugin_version = ''
    plugin_repo_token=''
    build_root = ''

    def get_plugin_source(self):
        url = f'https://api.github.com/repos/aayulogic/{self.plugin_name}/contents/plugin.py?ref={self.plugin_version}'
        

        headers = {
            'Authorization': f'token {self.plugin_repo_token}',
            'Accept': 'application/vnd.github.v3.raw'
        }
        r = requests.get(url, headers=headers)

        file_path = os.path.join(
            self.build_root,
            'plugin.py'
        )

        if not os.path.exists(self.build_root):
            os.mkdir(self.build_root)
            key_src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'test_files',
                               'plugin_test_files')
            private_key_file = os.path.join(key_src, 'private_key.pgp')
            public_key_file = os.path.join(key_src, 'public_key.pgp')
            shutil.copy(private_key_file, self.build_root)
            shutil.copy(public_key_file, self.build_root)
        with open(file_path, 'wb+') as f:
            f.write(r.content)

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
        self.get_plugin_source()
        os.environ['PAYROLL_PLUGIN_PRIVATE_KEY_UNLOCK_PASSPHRASE'] = 'sickmetalhead'
        os.environ['PGP_KEY_SERVER'] = 'keyserver.ubuntu.com'
        os.environ['PGP_KEY_ID'] = '7CD101550CA35EF150E3AC78E5AEBC25530F34AC'

        with self.settings(
            GPG_KEY_SERVER='keyserver.ubuntu.com',
            HRIS_KEY_ID='7CD101550CA35EF150E3AC78E5AEBC25530F34AC'
        ):
            self.installable_plugin_path = build_plugin(src_root=self.build_root)

        super().setUp()
        self.client.force_login(self.admin)

        self.data_setup_before_generation()

        self.result = self.plugin_in_action()

    def data_setup_before_generation(self):
        raise NotImplementedError(
            'Setup some data'
        )

    def plugin_in_action(self):

        payrolls_inputs = [
            (
                date(2017, 1, 1),
                date(2017, 1, 31),
            )
        ]

        self.get_payroll(
            *payrolls_inputs[0]
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

        return heading_with_plugin_report_row_record



class TestSamplePlugin(PayrollPluginTestBase):
    plugin_name = 'payroll_calculator_plugin_template'
    plugin_version = 'master'
    plugin_repo_token=settings.PAYROLL_PLUGIN_REPO_TOKEN
    build_root = '/tmp/payroll_calculator_plugin_template'

    def data_setup_before_generation(self):
        pass

    def test_sample_plugin(self):
        self.assertEquals(
            self.result.get('amount'),
            1000
        )

