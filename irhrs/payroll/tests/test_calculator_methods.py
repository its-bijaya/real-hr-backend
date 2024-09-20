import random
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.utils import timezone

from irhrs.core.constants.user import CHILDREN
from irhrs.core.utils.common import get_yesterday, get_today, DummyObject
from irhrs.organization.api.v1.tests.factory import OrganizationFactory, FiscalYearFactory
from irhrs.payroll.models import Heading, PackageHeading, BackdatedCalculation
from irhrs.payroll.tests.factory import HeadingFactory, PackageFactory, \
    UserExperiencePackageSlotFactory, OrganizationPayrollConfigFactory
from irhrs.payroll.utils.calculator import EmployeeSalaryCalculator, EmployeePayroll, ReportRow
from irhrs.payroll.utils.helpers import EmployeeAdapterMixin, get_employee_age_variables, \
    get_children_count_for_age_range
from irhrs.users.api.v1.tests.factory import UserFactory, UserExperienceFactory


class TestEmployeeSalaryCalculator(TestCase):
    def test_advance_salary_heading(self):
        organization = OrganizationFactory()
        HeadingFactory(organization=organization, order=20)
        heading = EmployeeSalaryCalculator.get_advance_salary_heading(organization)
        self.assertEqual(
            heading,
            Heading.objects.get(
                organization=organization,
                name='Advance Salary Deduction',
                type="Type2Cnst",
                payroll_setting_type='Penalty/Deduction',
            )
        )
        self.assertEqual(heading.order, 21)

    def test_default_advance_salary_deduction_heading(self):
        organization = OrganizationFactory()
        heading = HeadingFactory(organization=organization)
        package = PackageFactory(organization=organization)
        package_heading = PackageHeading.objects.create(
            heading=heading,
            package=package,
            order=1,
            rules=dict()
        )
        package.package_headings.add(package_heading)
        amount_from_package, repayment_amount = round(random.random() * 100000, 2), round(random.random() * 100000, 2)

        with patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_organization',
            return_value=organization
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_advance_salary_heading_amount',
            return_value=amount_from_package
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.start_calculation',
            return_value=None
        ):
            esc = EmployeeSalaryCalculator(
                employee=UserFactory(),
                datework=None,
                from_date=get_yesterday(),
                to_date=get_today(),
                salary_package=package,
                appoint_date=get_yesterday(),
            )
            esc.salary_package = package
            esc.set_repayment_heading(
                package_heading,
                repayment=DummyObject(amount=repayment_amount)
            )
            self.assertEqual(
                esc.payroll.get_heading_amount(package_heading),
                round((amount_from_package - repayment_amount), 2),
            )
            self.assertEqual(
                esc.payroll.get_heading_amount(esc.default_advance_salary_package_deduction_heading),
                round(repayment_amount, 2),
            )


    def test_adjust_backdated_calculation(self):
        employee = UserFactory()
        organization = OrganizationFactory()
        heading1 = HeadingFactory(organization=organization)
        heading2 = HeadingFactory(organization=organization)
        heading3 = HeadingFactory(organization=organization)
        package = PackageFactory(organization=organization)
        from_date = get_yesterday()
        to_date = get_today()
        user_experience = UserExperienceFactory(user=employee, organization=organization)
        fiscal_year = FiscalYearFactory(organization=organization, applicable_from=from_date)
        OrganizationPayrollConfigFactory(
            organization=organization,
            start_fiscal_year=fiscal_year,
        )
        package_slot = UserExperiencePackageSlotFactory(
            package=package,
            user_experience=user_experience
        )
        payroll = EmployeePayroll(employee=employee, package=package)
        payroll.rows = [
            ReportRow(
                heading=heading1,
                amount=20000,
                to_date=to_date,
                from_date=from_date,
            ),
            ReportRow(
                heading=heading2,
                amount=25000,
                to_date=to_date,
                from_date=from_date,
            ),
            ReportRow(
                heading=heading3,
                amount=30000,
                to_date=to_date,
                from_date=from_date,
            ),
        ]
        backdated_calculations = [
            BackdatedCalculation(
                package_slot=package_slot,
                heading=heading1,
                previous_amount=10000,
                current_amount=25000,
            ),
            BackdatedCalculation(
                package_slot=package_slot,
                heading=heading2,
                previous_amount=15000,
                current_amount=22500,
            ),
            BackdatedCalculation(
                package_slot=package_slot,
                heading=heading3,
                previous_amount=12000,
                current_amount=35000,
            )
        ]

        EmployeeSalaryCalculator.adjust_backdated_calculation(
            backdated_calculations, payroll, from_date, to_date
        )

        output = dict()
        for calculation in backdated_calculations:
            heading_id = calculation.heading.id
            output[heading_id] = payroll.get_heading_amount_from_heading(calculation.heading)

        expected_output = {
            heading1.id: 35000,
            heading2.id: 32500,
            heading3.id: 53000
        }
        self.assertEqual(output, expected_output)


class EmployeeVariableAdapterTest(TestCase):
    def test_get_payroll_increment_multiplier(self):
        input_data = [10, 20, 30, 40, 50]
        expected_output = (1 + 10/100) * (1 + 20/100) * (1 + 30/100) * (1 + 40/100) * (1+50/100)

        with patch(
            'irhrs.payroll.utils.helpers.EmployeeAdapterMixin._get_payroll_increments',
            return_value=input_data
        ):
            output = EmployeeAdapterMixin.get_payroll_increment_multiplier(EmployeeAdapterMixin, {})
            self.assertEqual(output, expected_output)

    def test_get_payroll_increment_multiplier_with_no_increments(self):
        input_value = []
        expected_output = 1
        with patch(
            'irhrs.payroll.utils.helpers.EmployeeAdapterMixin._get_payroll_increments',
            return_value=input_value
        ):
            output = EmployeeAdapterMixin.get_payroll_increment_multiplier(EmployeeAdapterMixin, {})
            self.assertEqual(output, expected_output)

    @override_settings(PAYROLL_CHILDREN_COUNT_VARIABLE_AGE_RANGES=[(0, 20), (20, 40), (40, 100)])
    def test_get_employee_age_variables(self):
        expected_output = [
            ("children_count_aging_from_0_to_20", 0, 20),
            ("children_count_aging_from_20_to_40", 20, 40),
            ("children_count_aging_from_40_to_100", 40, 100)
        ]
        output = get_employee_age_variables()

        self.assertEqual(output, expected_output)

    def test_get_children_for_age_range(self):
        employee = UserFactory()

        # create child aged 10
        employee.contacts.create(
            contact_of=CHILDREN,
            date_of_birth=get_today() - timezone.timedelta(days=365*10),
            number="123456759",
            is_dependent=True
        )

        # create child aged 16
        employee.contacts.create(
            contact_of=CHILDREN,
            date_of_birth=get_today() - timezone.timedelta(days=365 * 16),
            number="123456758",
            is_dependent=True
        )

        # create not dependent child aged 16
        # this should not increase the count as only is_dependent true should be counted
        employee.contacts.create(
            contact_of=CHILDREN,
            date_of_birth=get_today() - timezone.timedelta(days=365 * 16),
            number="123456757",
            is_dependent=False
        )

        obj = employee

        self.assertEqual(get_children_count_for_age_range(obj, 5, 15), 1)
        self.assertEqual(get_children_count_for_age_range(obj, 0, 20), 2)

        # inclusive of lower limit
        self.assertEqual(get_children_count_for_age_range(obj, 10, 15), 1)

        # exclusive of upper limit
        self.assertEqual(get_children_count_for_age_range(obj, 5, 10), 0)

        # sending both to None should send all values
        self.assertEqual(get_children_count_for_age_range(obj, 5, 10), 0)

    @override_settings(PAYROLL_CHILDREN_COUNT_VARIABLE_AGE_RANGES=[(0, 20), (20, 40), (40, 100)])
    def test_age_range_variables(self):
        EmployeeAdapterMixin.set_dynamic_attributes(EmployeeAdapterMixin)

        expected_methods = [
            "get_children_count_aging_from_0_to_20",
            "get_children_count_aging_from_20_to_40",
            "get_children_count_aging_from_40_to_100"
        ]

        for attr in expected_methods:
            self.assertTrue(hasattr(EmployeeAdapterMixin, attr))
