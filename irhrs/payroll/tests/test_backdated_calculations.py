from datetime import date, timedelta
from unittest.mock import patch

from irhrs.common.api.tests.common import BaseTestCase as TestCase


from irhrs.core.utils.common import get_today, DummyObject
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.payroll.models import Payroll, EmployeePayroll, ReportRowRecord, \
    OrganizationPayrollConfig, FY, BackdatedCalculation
from irhrs.payroll.tests.factory import HeadingFactory, PackageFactory, \
    UserExperiencePackageSlotFactory
from irhrs.payroll.utils.backdated_calculations import get_generated_report_rows, generate_payroll, \
    calculate_back_dated_payroll_diff, group_generated_report_rows, \
    get_arguments_for_calculate_back_dated_payroll_diff, update_or_create_backdated_payroll
from irhrs.payroll.utils.calculator import ReportRow
from irhrs.users.api.v1.tests.factory import UserFactory, UserExperienceFactory


class TestCaseGetGeneratedReportRows(TestCase):

    def setUp(self) -> None:
        self.organization = OrganizationFactory()
        self.employee = UserFactory(_organization=self.organization)
        self.heading = HeadingFactory(type='Addition', organization=self.organization)
        self.package = PackageFactory(organization=self.organization)

    def create_row(self, from_date, to_date, amount=10000):
        return self.create_payroll_and_report_row(
            self.employee,
            self.package,
            self.heading,
            self.organization,
            from_date,
            to_date,
            amount
        )

    @staticmethod
    def create_payroll_and_report_row(employee, package, heading, organization,
                                      from_date, to_date, amount):
        payroll = Payroll.objects.create(
            organization=organization,
            from_date=from_date,
            to_date=to_date,
            extra_data={},
        )
        employee_payroll = EmployeePayroll.objects.create(
            employee=employee,
            payroll=payroll,
            package=package
        )
        report_row = ReportRowRecord.objects.create(
            employee_payroll=employee_payroll,
            from_date=from_date,
            to_date=to_date,
            heading=heading,
            amount=amount
        )
        return report_row

    def test_get_generated_report_rows(self):
        this_year = get_today().year
        jan_1 = date(this_year, 1, 1)
        feb_1 = date(this_year, 2, 1)
        mar_1 = date(this_year, 3, 1)
        apr_1 = date(this_year, 4, 1)

        jan_last = feb_1 - timedelta(days=1)
        feb_last = mar_1 - timedelta(days=1)
        mar_last = apr_1 - timedelta(days=1)

        row_1 = self.create_row(jan_1, jan_last)
        row_2 = self.create_row(feb_1, feb_last)
        row_3 = self.create_row(mar_1, mar_last)

        rows = get_generated_report_rows(self.employee, feb_1, feb_last)
        self.assertEqual(rows, [row_2])

        rows = get_generated_report_rows(self.employee, jan_1, feb_last)
        self.assertEqual(rows, [row_1, row_2])

        rows = get_generated_report_rows(self.employee, jan_1, mar_last)
        self.assertEqual(rows, [row_1, row_2, row_3])

        rows = get_generated_report_rows(self.employee, jan_last, feb_last)
        self.assertEqual(rows, [row_1, row_2], "partial intersection")


class TestCaseGeneratePayroll(TestCase):
    def setUp(self) -> None:
        self.organization = OrganizationFactory()
        self.employee = UserFactory(_organization=self.organization)
        self.package = PackageFactory(organization=self.organization)
        self.payroll_config = OrganizationPayrollConfig()

    def test_generate_payroll(self):
        this_year = get_today().year
        from_date = date(year=this_year, month=1, day=1)
        to_date = date(year=this_year, month=1, day=31)
        expected_rows = ['a', 'b', 'c']

        def init_calculator(s, *args, **kwargs):
            s.payroll = DummyObject(rows=expected_rows)

        with patch(
            'irhrs.payroll.utils.backdated_calculations.get_payroll_config',
            return_value=self.payroll_config
        ) as get_payroll_config, patch(
            'irhrs.payroll.utils.helpers.get_appoint_date',
            return_value=from_date
        ) as get_appoint_date, patch(
            'irhrs.payroll.utils.helpers.get_dismiss_date',
            return_value=None
        ) as get_dismiss_date, patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.__init__',
            return_value=None,
            side_effect=init_calculator,
            autospec=True
        ) as calculator_init_fn, patch(
            'irhrs.organization.models.fiscal_year.FY.__eq__',
            lambda s, o: s._organization == o._organization  # patch comparison
        ):
            rows = generate_payroll(self.employee, from_date, to_date, self.package)
            self.assertEqual(rows, expected_rows)

            self.assertEqual(get_payroll_config.call_count, 1)
            self.assertEqual(get_payroll_config.call_args.args, (self.organization,))

            self.assertEqual(get_appoint_date.call_count, 1)
            self.assertEqual(get_appoint_date.call_args.args,
                             (self.employee, self.payroll_config))

            self.assertEqual(get_dismiss_date.call_count, 1)
            self.assertEqual(get_dismiss_date.call_args.args,
                             (self.employee, self.employee.current_experience))

            self.assertEqual(calculator_init_fn.call_count, 1)
            self.assertEqual(
                calculator_init_fn.call_args.args[1:], (
                    self.employee,
                    FY(self.organization),
                    from_date,
                    to_date,
                    self.package,
                    from_date,  # appoint_date
                    None,  # dismiss_date
                    True,  # calculate_tax
                )
            )


class TestCalculateBackdatedPayroll(TestCase):
    def setUp(self) -> None:
        self.organization = OrganizationFactory()
        self.employee = UserFactory(_organization=self.organization)
        self.package = PackageFactory(organization=self.organization)

        self.type1cnst = HeadingFactory(
            name="Type One",
            type="Type1Cnst"
        )
        self.type2cnst = HeadingFactory(
            name="Type Two",
            type="Type2Cnst"
        )

        self.basic_salary = HeadingFactory(
            name="Basic Salary",
            organization=self.organization,
            type="Addition"
        )
        self.developer_allowance = HeadingFactory(
            name="Developer Allowance",
            organization=self.organization,
            type="Addition"
        )
        self.internet_allowance = HeadingFactory(
            name="Internet Allowance",
            organization=self.organization,
            type="Addition"
        )

        this_year = get_today().year
        self.jan_1 = date(this_year, 1, 1)
        self.feb_1 = date(this_year, 2, 1)
        self.mar_1 = date(this_year, 3, 1)
        self.apr_1 = date(this_year, 4, 1)

        self.jan_last = self.feb_1 - timedelta(days=1)
        self.feb_last = self.mar_1 - timedelta(days=1)
        self.mar_last = self.apr_1 - timedelta(days=1)

    def test_group_generated_report_rows(self):
        rows = [
            ReportRow(heading=self.basic_salary, amount=1000),
            ReportRow(heading=self.basic_salary, amount=2000),
            ReportRow(heading=self.internet_allowance, amount=5000)
        ]
        expected_output = {
            self.basic_salary: 3000,
            self.internet_allowance: 5000
        }

        output = group_generated_report_rows(rows)
        self.assertEqual(output, expected_output)

    def test_calculate_backdated_payroll_diff(self):
        this_year = get_today().year
        from_date = date(year=this_year, month=1, day=1)
        to_date = date(year=this_year, month=1, day=31)

        generated_rows = [
            ReportRow(
                heading=self.basic_salary,
                amount=10000
            ),
            ReportRow(
                heading=self.developer_allowance,
                amount=15000
            ),
            # type1 constant should not be in diff
            ReportRow(
                heading=self.type1cnst,
                amount=20000
            )
        ]
        new_rows = [
            ReportRow(
                heading=self.basic_salary,
                amount=20000,
            ),
            ReportRow(
                heading=self.internet_allowance,
                amount=25000
            ),

            # type2 constant should not be in diff
            ReportRow(
                heading=self.type2cnst,
                amount=15000
            )
        ]
        expected_output = [
            {
                "heading": self.basic_salary,
                "previous_amount": 10000,
                "current_amount": 20000
            },
            {
                "heading": self.developer_allowance,
                "previous_amount": 15000,
                "current_amount": None
            },
            {
                "heading": self.internet_allowance,
                "previous_amount": None,
                "current_amount": 25000
            }
        ]

        with patch(
            'irhrs.payroll.utils.backdated_calculations.get_generated_report_rows',
            return_value=generated_rows
        ) as get_generated, patch(
            'irhrs.payroll.utils.backdated_calculations.generate_payroll',
            return_value=new_rows
        ) as get_new_rows:
            output = calculate_back_dated_payroll_diff(self.employee, from_date, to_date,
                                                       self.package)
            output.sort(key=lambda item: item["heading"].order)
            self.assertEqual(output, expected_output)

            self.assertEqual(get_generated.call_count, 1)
            self.assertEqual(get_generated.call_args.args, (self.employee, from_date, to_date))

            self.assertEqual(get_new_rows.call_count, 1)
            self.assertEqual(get_new_rows.call_args.args,
                             (self.employee, from_date, to_date, self.package))

    def set_up_get_arguments(self):
        with patch("irhrs.payroll.signals.async_create_package_rows", return_value=None):
            self.experience = UserExperienceFactory(
                user=self.employee,
                organization=self.organization,
                start_date=self.jan_1,
                end_date=None
            )
            self.package_2 = PackageFactory(organization=self.organization)

            self.package_slot_0 = UserExperiencePackageSlotFactory(
                active_from_date=self.jan_1,
                package=self.package_2,
                user_experience=self.experience
            )

            self.package_slot_1 = UserExperiencePackageSlotFactory(
                active_from_date=self.feb_1,
                package=self.package,
                user_experience=self.experience
            )

            self.row_1 = TestCaseGetGeneratedReportRows.create_payroll_and_report_row(
                self.employee,
                self.package,
                self.basic_salary,
                self.organization,
                self.jan_1,
                self.feb_last,
                10000
            )

            self.package_slot_2 = UserExperiencePackageSlotFactory(
                active_from_date=self.apr_1,
                package=self.package_2,
                user_experience=self.experience,
            )

    def test_get_arguments_for_calculate_back_dated_payroll_diff(self):
        self.set_up_get_arguments()
        slot2 = self.package_slot_2

        with patch(
            'irhrs.payroll.utils.helpers.get_appoint_date',
            return_value=self.jan_1
        ), patch(
            'irhrs.payroll.utils.helpers.get_dismiss_date',
            return_value=None
        ):
            slot2.backdated_calculation_from = self.feb_last
            employee_o, from_date_o, to_date_o, salary_packages_o = \
                get_arguments_for_calculate_back_dated_payroll_diff(slot2)
            job_title = getattr(self.experience.job_title, "title", "")
            employment_status = getattr(self.experience.employment_status, "title", "")

            expected_salary_packages = [
                {
                    "package": self.package_2,
                    "from_date": self.jan_1,
                    "to_date": self.jan_last,
                    "applicable_from": self.jan_1,
                    "job_title": job_title,
                    "current_step": self.experience.current_step,
                    "employment_status": employment_status
                },
                {
                    "package": self.package,
                    "from_date": self.feb_1,
                    "to_date": self.feb_last - timedelta(days=1),
                    "applicable_from": self.feb_1,
                    "job_title": job_title,
                    "current_step": self.experience.current_step,
                    "employment_status": employment_status
                },
                {
                    "package": self.package_2,
                    "from_date": self.feb_last,
                    "to_date": self.mar_last,
                    "applicable_from": self.package_slot_2.active_from_date,
                    "job_title": job_title,
                    "current_step": self.experience.current_step,
                    "employment_status": employment_status
                }
            ]

            self.assertEqual(employee_o, self.employee)
            self.assertEqual(from_date_o, self.jan_1)
            self.assertEqual(to_date_o, self.mar_last)

            self.assertEqual(salary_packages_o, expected_salary_packages)

    def setup_update_or_create_backdated_payroll(self):
        with patch(
            "irhrs.payroll.signals.async_create_package_rows", return_value=None
        ), patch(
            "irhrs.payroll.signals.async_update_or_create_backdated_payroll", return_value=None
        ):
            self.experience = UserExperienceFactory(
                user=self.employee,
                organization=self.organization,
                start_date=self.jan_1,
                end_date=None
            )

            self.package_slot = UserExperiencePackageSlotFactory(
                active_from_date=self.feb_1,
                package=self.package,
                user_experience=self.experience,
                backdated_calculation_from=self.jan_1
            )
            self.old_calculation_ids = [
                BackdatedCalculation.objects.create(
                    heading=self.basic_salary,
                    previous_amount=10000,
                    current_amount=20000,
                    package_slot=self.package_slot
                ).id,
                BackdatedCalculation.objects.create(
                    heading=self.developer_allowance,
                    previous_amount=10000,
                    current_amount=20000,
                    package_slot=self.package_slot
                ).id,
                BackdatedCalculation.objects.create(
                    heading=self.internet_allowance,
                    previous_amount=10000,
                    current_amount=20000,
                    package_slot=self.package_slot
                ).id
            ]

    def test_update_or_create_backdated_payroll(self):
        self.setup_update_or_create_backdated_payroll()
        args = (
            self.employee,
            self.jan_1,
            self.jan_last,
            []
        )
        diffs = [
            {
                "heading": self.basic_salary,
                "previous_amount": 10000,
                "current_amount": 20000
            },
            {
                "heading": self.developer_allowance,
                "previous_amount": 15000,
                "current_amount": None
            },
            {
                "heading": self.internet_allowance,
                "previous_amount": None,
                "current_amount": 25000
            }
        ]
        with patch(
            'irhrs.payroll.utils.backdated_calculations.get_arguments_for_'
            'calculate_back_dated_payroll_diff',
            return_value=args
        ), patch(
            'irhrs.payroll.utils.backdated_calculations.calculate_back_dated_payroll_diff',
            return_value=diffs
        ):
            update_or_create_backdated_payroll(self.package_slot)

        self.assertEqual(
            BackdatedCalculation.objects.filter(id__in=self.old_calculation_ids).count(),
            0
        )
        for diff in diffs:
            self.assertTrue(BackdatedCalculation.objects.filter(package_slot=self.package_slot,
                                                                **diff).exists())
