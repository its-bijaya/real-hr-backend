"""Utils for tests"""
import json
from typing import Union

from django.forms.utils import pretty_name

from irhrs.payroll.api.v1.serializers import HeadingSerializer
from irhrs.payroll.api.v1.serializers.heading import DragHeadingSerializer
from irhrs.payroll.models import Heading, PackageHeading
from irhrs.payroll.tests.factory import PackageFactory


class PackageUtil:
    """
    Utility class to create packages for testing

    default configs are:

        Basic Salary: 10000
        Allowance: 15000
        Total Addition: Basic Salary + Allowance
        PF = 0.10 * Basic Salary
        SSF = 0.08 * Basic Salary
        Total Deduction = PF + SSF
        Total Salary = Total Addition - Total Deduction
        Tax = 0.10 * Annual Gross Salary
        Cash In Hand = Total Salary - Tax
    """

    RULE_CONFIG = {
        'basic_salary': {'rules': ['10000'], 'payroll_setting_type': 'Salary Structure',
                         'type': 'Type1Cnst', 'duration_unit': 'Monthly', 'taxable': None,
                         'absent_days_impact': None},
        'allowance': {'rules': ['15000'], 'payroll_setting_type': 'Salary Structure',
                      'type': 'Type1Cnst', 'duration_unit': 'Monthly', 'taxable': None,
                      'absent_days_impact': None},
        'total_addition': {'rules': ['__BASIC_SALARY__ + __ALLOWANCE__'],
                           'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
                           'duration_unit': 'Monthly', 'taxable': True,
                           'absent_days_impact': True},
        'pf': {'rules': ['0.10 * __BASIC_SALARY__'], 'payroll_setting_type': 'Provident Fund',
               'type': 'Deduction', 'duration_unit': 'Monthly', 'taxable': False,
               'absent_days_impact': False},
        'ssf': {'rules': ['0.10 * __BASIC_SALARY__'],
                'payroll_setting_type': 'Social Security Fund',
                'type': 'Deduction', 'duration_unit': 'Monthly', 'taxable': False,
                'absent_days_impact': False},
        'total_deduction': {'rules': ['__PF__ + __SSF__'],
                            'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
                            'duration_unit': 'Monthly', 'taxable': None,
                            'absent_days_impact': None},
        'total_salary': {'rules': ['__TOTAL_ADDITION__ - __TOTAL_DEDUCTION__'],
                         'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
                         'duration_unit': 'Monthly', 'taxable': None, 'absent_days_impact': None},
        'total_annual_gross_salary': {'rules': ['__ANNUAL_GROSS_SALARY__'],
                         'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
                         'duration_unit': 'Monthly', 'taxable': None, 'absent_days_impact': None},
        'tax': {'rules': ['0.10 * __TOTAL_ANNUAL_GROSS_SALARY__'], 'payroll_setting_type': 'Salary TDS',
                'type': 'Tax Deduction', 'duration_unit': None, 'taxable': None,
                'absent_days_impact': None},
        'cash_in_hand': {'rules': ['__TOTAL_SALARY__ - __TAX__'],
                         'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
                         'duration_unit': 'Monthly', 'taxable': None, 'absent_days_impact': None},
    }

    def __init__(self, organization, **config):
        self.organization = organization

        for heading_name in self.RULE_CONFIG:
            setattr(self, f'{heading_name}_heading', config.get(f'{heading_name}_heading'))
            setattr(self, f'{heading_name}_rule', config.get(
                f'{heading_name}_rule',
                self.RULE_CONFIG[heading_name]['rules']
            ))

    @staticmethod
    def _get_rule_data_for_serializer(rule_data):
        return [
            {"rule": rule, "rule_validator": {"editable": True, "numberOnly": False}}
            for rule in rule_data
        ]

    @staticmethod
    def _get_tds_rule_data_for_serializer(rule_data):
        return [
            {
                "rule": rule,
                "rule_validator": {
                    "editable": True,
                    "numberOnly": False
                },
                "tds_type": str(index)
            }
            for index, rule in enumerate(rule_data)
        ]

    def get_headings(self):
        headings = list()
        for order, heading_name in enumerate(self.RULE_CONFIG.keys()):
            headings.append(self.get_heading(heading_name, order))
        return headings

    def get_heading(self, heading_name, order):
        heading = getattr(self, f"{heading_name}_heading")
        if not heading:
            heading = self.create_heading(heading_name, order)
            setattr(self, f"{heading_name}_heading", heading)
        return heading

    def create_heading(self, heading_name, order):
        heading_obj = Heading.objects.filter(
            name__iexact=pretty_name(heading_name), organization=self.organization
        ).first()

        if heading_obj:
            return heading_obj

        data = dict(self.RULE_CONFIG[heading_name])

        if data['type'] == 'Tax Deduction':
            rule = self._get_tds_rule_data_for_serializer(
                getattr(self, f"{heading_name}_rule"))
        else:
            rule = self._get_rule_data_for_serializer(
                getattr(self, f"{heading_name}_rule"))

        data['rules'] = json.dumps(rule)
        data['order'] = order
        data['organization'] = self.organization.slug
        data['name'] = pretty_name(heading_name)
        data['benefit_type'] = "Monetary Benefit"

        serializer = HeadingSerializer(data=data, context={'organization': self.organization})
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def add_heading_to_package(self, heading, package, order, organization):
        data = {
            "to_obj_order": order,
            "package_id": package.id,
            "heading_id": heading.id
        }
        serializer = DragHeadingSerializer(data=data, context={'organization': organization})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        package_heading = PackageHeading.objects.get(package=package, heading=heading)

        package_heading.rules = json.dumps(self._get_rule_data_for_serializer(
            getattr(
                self,
                f"{package_heading.heading.name.replace(' ', '_').lower()}_rule"
            )
        ))
        is_valid, validator = package_heading.rule_is_valid()

        if is_valid:
            package_heading.save()
        else:
            raise AssertionError(validator.non_field_errors, validator.rules)

    def create_package(self):
        """
        Creates a Package with default structure
        """
        package = PackageFactory(organization=self.organization)
        headings = self.get_headings()
        for order, heading in enumerate(headings, start=1):
            self.add_heading_to_package(heading, package, order, self.organization)

        return package


class SimplePackageUtil(PackageUtil):
    """
    Util for creating simple package with 3 headings addition, deduction and tax

    :arg organization: Organization instance
    :arg addition: Package amount for addition (Defaults to 10000)
    :arg deduction: Package amount for deduction (Defaults to 500)
    """
    RULE_CONFIG = {
        'addition':  {
            'rules': ['10000'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
            'duration_unit': 'Monthly', 'taxable': True,
            'absent_days_impact': True
        },
        'deduction': {
            'rules': ['500'],
            'payroll_setting_type': 'Social Security Fund', 'type': 'Deduction',
            'duration_unit': 'Monthly', 'taxable': False,
            'absent_days_impact': True
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

    def __init__(
        self,
        organization,
        addition: Union[float, int] = None,
        deduction: Union[float, int] = None
    ):
        config = {}
        if addition:
            config['addition_rule'] = [str(addition)]
        if deduction:
            config['deduction_rule'] = [str(deduction)]

        super().__init__(organization, **config)
