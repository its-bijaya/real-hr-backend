import json

from django.core.files.temp import NamedTemporaryFile

from irhrs.common.api.tests.common import BaseTestCase
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.payroll.models import HeadingDependency
from irhrs.payroll.tests.factory import HeadingFactory
from irhrs.payroll.views import HeadingExportView, HeadingImportView


class PayrollHeadingImportExportTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.source_organization = OrganizationFactory()
        self.target_organization = OrganizationFactory()
        HeadingFactory(
            name='Basic Salary',
            organization=self.source_organization,
            rules=json.dumps(
                [{"rule": "1000", "rule_validator": {"editable": True, "numberOnly": False}}],
            ),
            type="Type1Cnst",
            order=1,
        )
        HeadingFactory(
            name='Dearness Allowance',
            organization=self.source_organization,
            rules=json.dumps(
                [{"rule": "2000", "rule_validator": {"editable": True, "numberOnly": False}}],
            ),
            type="Type1Cnst",
            order=2
        )

        HeadingFactory(
            name='Addition',
            organization=self.source_organization,
            rules=json.dumps(
                [{"rule": "__BASIC_SALARY__ + __DEARNESS_ALLOWANCE__",
                    "rule_validator": {"editable": True, "numberOnly": False}}],
            ),
            type="Addition",
            order=3
        )

        HeadingFactory(
            name='Taxable',
            organization=self.source_organization,
            rules=json.dumps(
                [{"rule": "__ADDITION__",
                    "rule_validator": {"editable": True, "numberOnly": False}}],
            ),
            type="Type2Cnst",
            order=4
        )

    def test_export_import(self):
        dump_data = HeadingExportView.dump_payroll_data(self.source_organization)

        # to test export store it in file
        with NamedTemporaryFile(suffix='.pikle') as fp:
            fp.write(dump_data)
            fp.seek(0)

            HeadingImportView.load_heading(
                fp,
                self.target_organization
            )

        basic_salary = self.target_organization.headings.filter(
            name="Basic Salary",
            rules=json.dumps(
                [{"rule": "1000", "rule_validator": {"editable": True, "numberOnly": False}}],
            ),
            type="Type1Cnst",
            order=1,
        ).first()
        self.assertIsNotNone(basic_salary)

        dearness = self.target_organization.headings.filter(
            name='Dearness Allowance',
            rules=json.dumps(
                [{"rule": "2000", "rule_validator": {"editable": True, "numberOnly": False}}],
            ),
            type="Type1Cnst",
            order=2
        ).first()
        self.assertIsNotNone(dearness)

        addition = self.target_organization.headings.filter(
            name='Addition',
            rules=json.dumps(
                [{"rule": "__BASIC_SALARY__ + __DEARNESS_ALLOWANCE__",
                  "rule_validator": {"editable": True, "numberOnly": False}}],
            ),
            type="Addition",
            order=3
        ).first()
        self.assertIsNotNone(addition)
        self.assertTrue(
            HeadingDependency.objects.filter(
                source=addition,
                target=basic_salary
            ).exists()
        )
        self.assertTrue(
            HeadingDependency.objects.filter(
                source=addition,
                target=dearness
            ).exists()
        )

        taxable = self.target_organization.headings.filter(
            name='Taxable',
            rules=json.dumps(
                [{"rule": "__ADDITION__",
                  "rule_validator": {"editable": True, "numberOnly": False}}],
            ),
            type="Type2Cnst",
            order=4
        ).first()
        self.assertIsNotNone(taxable)
        self.assertTrue(
            HeadingDependency.objects.filter(
                source=taxable,
                target=addition
            ).exists()
        )
