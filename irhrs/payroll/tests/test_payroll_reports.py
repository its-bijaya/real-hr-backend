from django.contrib.auth import get_user_model

from unittest.mock import patch
from datetime import date

from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today, DummyObject
from irhrs.core.tests.utils import FakeManager, FakeModel
from irhrs.payroll.models import Payroll, CONFIRMED, SSFReportSetting, Heading, \
    DisbursementReportSetting, TaxReportSetting
from irhrs.payroll.tests.utils import PackageUtil
from irhrs.payroll.utils.calculator import EmployeeSalaryCalculator, EmployeePayroll
from irhrs.payroll.utils.datework.date_helpers import DateWork
from irhrs.users.models import User

from irhrs.users.api.v1.tests.factory import UserExperienceFactory
from irhrs.payroll.tests.factory import BackdatedCalculationFactory,\
    PackageFactory, UserExperiencePackageSlotFactory


User = get_user_model()


class FakeHeading(DummyObject):
    pass


class FakePackageHeading(FakeModel):
    def __init__(self, **kwargs):
        self.heading = FakeHeading()
        super().__init__(**kwargs)


class FakeSalaryPackage(DummyObject):

    @property
    def package_headings(self):
        return FakeManager(faked_class=FakePackageHeading)


class FakeUserExperience(FakeModel):
    pass


class FakeUserContact(FakeModel):
    pass


class FakeEmployee(FakeModel):

    def first_date_range_user_experiences(self, start_date, end_date):
        return FakeUserExperience(current_step=1)

    @property
    def detail(self):
        return FakeEmployeeDetail(
            user=self,
            gender=getattr(self, 'd_gender', 'Male'),
            joined_date=getattr(self, 'd_joined_date', get_today()),
            organization=getattr(self, 'd_organization', None),
            nationality=getattr(self, 'd_nationality', None)
        )

    @property
    def payroll_increments(self):
        return FakeManager(faked_class=FakePayrollIncrements, return_count=0)

    @property
    def contacts(self):
        return FakeManager(FakeUserContact)


class FakePayrollIncrements(FakeModel):
    pass


class FakeEmployeeDetail(FakeModel):
    pass


class FakeOrganizationPayrollConfig(FakeModel):
    pass


class PayrollReportMixin:

    @property
    def datework(self):
        return DateWork(
            fiscal_year_start_month_date=(1, 1)  # set start of fiscal year to jan 1
        )

    def get_payroll_config(self, **kwargs):
        return FakeOrganizationPayrollConfig(**kwargs)

    def create_employee_payroll(self):

        payroll = self.get_payroll()
        rows = payroll.rows
        user = self.admin
        from_date, to_date = self.get_dates()
        employee_payroll = self.get_employee_payroll(user, self.package)
        create_payroll = self.create_payroll(from_date, to_date)

        set_rows = list(map(employee_payroll.add_or_update_row, rows))
        created_employee_payroll = employee_payroll.record_to_model(create_payroll)
        return created_employee_payroll


    @staticmethod
    def get_employee_payroll(employee, package):
        with patch(
            'irhrs.payroll.utils.calculator.EmployeePayroll.get_heading_amount',
            return_value=0
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeePayroll.get_heading_amount_from_heading',
            return_value=0
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeePayroll.get_heading_amount_from_variable',
            return_value=0
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeePayroll.get_package_heading_amount',
            return_value=0
        ):
            employee_payroll = EmployeePayroll(
                employee=employee,
                package=package
            )
            return employee_payroll

    @staticmethod
    def get_dates():
        year = get_today().year
        from_date = date(year, 1, 1)
        to_date = date(year, 1, 31)
        return from_date, to_date


    def get_payroll(self):
        payroll_config = self.get_payroll_config()
        employee = FakeEmployee(
            marital_status="Single",
            d_organization=self.organization,
            d_nationality="Nepalese"
        )
        from_date, to_date = self.get_dates()
        appoint_date = from_date

        previous_taxable_amount = 0
        paid_tax = 0

        working_days = (30, 30)
        worked_days = (30, 30)

        with patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_organization',
            return_value=self.organization
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.previous_payroll',
            return_value=None
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.payroll_config',
            return_value=payroll_config
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_working_days',
            return_value=working_days
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_worked_days',
            return_value=worked_days
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_taxable_amount_from_entry',
            return_value=previous_taxable_amount
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_paid_tax',
            return_value=paid_tax
        ):

            calculator = EmployeeSalaryCalculator(
                employee=employee,
                datework=self.datework,
                from_date=from_date,
                to_date=to_date,
                salary_package=self.package,
                appoint_date=appoint_date,
                simulated_from=None
            )

            return calculator.payroll

    def create_packages(self):
        package_util = PackageUtil(organization=self.organization)
        package = package_util.create_package()
        return package

    def create_payroll(self, from_date, to_date):
        create_payroll = Payroll.objects.create(
            organization=self.organization,
            from_date=from_date,
            to_date=to_date,
            extra_data={}
        )
        create_payroll.status = CONFIRMED
        create_payroll.save()
        return create_payroll


class TestSSFReport(PayrollReportMixin, RHRSAPITestCase):

    organization_name = 'Test'
    users = [('admin@example.com', 'password', 'Male')]

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )
        self.package = self.create_packages()

    def ssf_setting_url(self):
        return reverse(
            'api_v1:payroll:ssfreportsetting-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def ssf_report_url(self, instance):
        return reverse(
            'api_v1:payroll:employeepayroll-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'payroll_id': instance.id
            }
        )

    def test_ssf_report_setting(self):
        url = self.ssf_setting_url() + f'?organization__slug={self.organization.slug}'
        ssf_report_model = self.create_ssf_report_model()
        headings_id = SSFReportSetting.objects.first().headings.values_list('id', flat=True)
        data = {
            "headings": list(headings_id)
        }

        patch_response = self.client.post(
            url,
            data=data,
            format='json'
        )
        self.assertEqual(
            patch_response.json(),
            data
        )
        get_response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            get_response.json(),
            data
        )

    def test_ssf_report(self):
        employee_payroll = self.create_employee_payroll()
        payroll = employee_payroll.payroll
        ssf_report = self.create_ssf_report_model()
        basic_salary = 10000
        ssf = round((0.10 * basic_salary), 2)
        url = self.ssf_report_url(payroll)
        response = self.client.get(
            url,
            format='json'
        )
        heading_amounts = response.json().get('results')[0].get('heading_amounts')
        ssf_report_heading_id = ssf_report.headings.get(name='Ssf').id
        value = heading_amounts.get(str(ssf_report_heading_id))
        self.assertEqual(
            value,
            ssf
        )

    def create_ssf_report_model(self):
        employee_payroll = self.create_employee_payroll()
        ssf_heading = Heading.objects.filter(name='Ssf').first()
        ssf = SSFReportSetting.objects.create(
            organization=self.organization
        )
        ssf.headings.add(ssf_heading)
        return ssf


class TestTaxReport(PayrollReportMixin, RHRSAPITestCase):

    organization_name = 'Test'
    users = [('admin@example.com', 'password', 'Male')]

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )
        self.package = self.create_packages()

    def tax_setting_url(self):
        return reverse(
            'api_v1:payroll:taxreportsetting-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def tax_report_url(self, instance):
        return reverse(
            'api_v1:payroll:tax-report-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'payroll_id': instance.id
            }
        )

    def test_tax_report_setting(self):
        url = self.tax_setting_url() + f'?organization__slug={self.organization.slug}'
        tax_report_model = self.create_tax_report_model()
        headings_id = TaxReportSetting.objects.first().headings.values_list('id', flat=True)
        data = {
            "headings": list(headings_id)
        }

        patch_response = self.client.post(
            url,
            data=data,
            format='json'
        )
        self.assertEqual(
            patch_response.json(),
            data
        )
        get_response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            get_response.json(),
            data
        )

    def test_tax_report(self):
        employee_payroll = self.create_employee_payroll()
        payroll = employee_payroll.payroll
        tax_report = self.create_tax_report_model()
        total_annual_gross_salary = 23000
        tax = round((0.10 * total_annual_gross_salary), 2)
        url = self.tax_report_url(payroll)
        response = self.client.get(
            url,
            format='json'
        )
        heading_amounts = response.json().get('results')[0].get('heading_amounts')
        tax_report_heading_id = tax_report.headings.get(name='Tax').id
        value = heading_amounts.get(str(tax_report_heading_id))
        self.assertEqual(
            value,
            tax
        )

    def create_tax_report_model(self):
        employee_payroll = self.create_employee_payroll()
        tax_heading = Heading.objects.filter(name='Tax').first()
        tax = TaxReportSetting.objects.create(
            organization=self.organization
        )
        tax.headings.add(tax_heading)
        return tax


class TestDisbursementReport(PayrollReportMixin, RHRSAPITestCase):
    organization_name = 'Test'
    users = [('admin@example.com', 'password', 'Male')]

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )
        self.package = self.create_packages()

    def disbursement_setting_url(self):
        return reverse(
            'api_v1:payroll:disbursement-report-setting-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def disbursement_report_url(self, instance):
        return reverse(
            'api_v1:payroll:disbursement-report-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'payroll_id': instance.id
            }
        )

    def test_disbursement_report_setting(self):
        url = self.disbursement_setting_url()
        disbursement_report_model = self.create_disbursement_report_model()
        headings_id = DisbursementReportSetting.objects.first()\
            .headings.values_list('id', flat=True)
        data = {
            "headings": list(headings_id)
        }

        post_response = self.client.post(
            url,
            data=data,
            format='json'
        )
        self.assertEqual(
            post_response.json(),
            data
        )
        get_response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            get_response.json(),
            data
        )

    def test_disbursement_report(self):
        employee_payroll = self.create_employee_payroll()
        payroll = employee_payroll.payroll
        disbursement_report = self.create_disbursement_report_model()

        basic_salary = 10000
        allowance = 15000
        total_addition = basic_salary + allowance
        pf = 0.10 * basic_salary
        ssf = 0.10 * basic_salary
        total_deduction = pf + ssf
        total_salary = total_addition - total_deduction
        total_tax = 0.10 * total_salary

        url = self.disbursement_report_url(payroll)
        response = self.client.get(
            url,
            format='json'
        )
        heading_amounts = response.json().get('results')[0].get('heading_amounts')
        tax_heading_id = disbursement_report.headings.get(name='Tax').id
        total_salary_heading_id = disbursement_report.headings.get(name='Total salary').id
        total_salary_amount = heading_amounts.get(str(total_salary_heading_id))
        total_tax_amount = heading_amounts.get(str(tax_heading_id))

        self.assertEqual(
            total_salary,
            total_salary_amount
        )
        self.assertEqual(
            total_tax,
            total_tax_amount
        )


    def create_disbursement_report_model(self):
        employee_payroll = self.create_employee_payroll()
        disbursement_headings = Heading.objects.all()
        headings_list = list(disbursement_headings)
        disbursement = DisbursementReportSetting.objects.create(
            organization=self.organization
        )
        for heading in headings_list:
            disbursement.headings.add(heading)
        return disbursement


class BackdatedCalculationReportTest(RHRSAPITestCase):
    users = [
        ('admin@gmail.com', 'password', 'Male'),
        ('normalone@gmail.com', 'password', 'Male',),
    ]
    organization_name = "Organization"

    def setUp(self):
        super().setUp()
        self.ux = UserExperienceFactory(user=self.admin,
                              organization=self.organization)
        self.package = PackageFactory(organization=self.organization)
        self.package_slot = UserExperiencePackageSlotFactory(
            package=self.package,
            user_experience=self.ux
        )
        self.backdated = BackdatedCalculationFactory(
            package_slot = self.package_slot
        )
        self.client.force_login(self.created_users[0])

    def test_backdated_report_list(self):
        backdated_report_url = self.url()
        response = self.client.get(backdated_report_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)

    def url(self):
        return reverse(
            'api_v1:payroll:backdated-calculations-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'package_slot_id': self.package_slot.id
            }
        )
