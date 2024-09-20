from datetime import date

from irhrs.payroll.constants import LIFE_INSURANCE, HEALTH_INSURANCE
from irhrs.payroll.tests.factory import RebateSettingFactory

from unittest.mock import patch

from django.contrib.auth.models import Group

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.organization.models import (
    FiscalYear,
    FiscalYearMonth
)
from irhrs.organization.models import (
    UserOrganization, EmploymentJobTitle
)
from irhrs.payroll.models import (
    HH_OVERTIME,
    Payroll,
    CONFIRMED,
    UserExperiencePackageSlot,
    OrganizationPayrollConfig
)
from irhrs.payroll.tests.utils import PackageUtil
from irhrs.payroll.utils.calculator import (
    EmployeeSalaryCalculator
)
from irhrs.payroll.utils.datework.date_helpers import DateWork
from irhrs.permission.constants.groups import ADMIN
from irhrs.users.models import User, UserDetail
from irhrs.users.models.experience import UserExperience
from irhrs.users.utils import get_default_date_of_birth


class ExtraEarningTaxAdjustmentPackageUtil(PackageUtil):
    RULE_CONFIG = {
        'addition':  {
            'rules': ['2000'],
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


class RHRSTestCaseWithUserExperience(RHRSTestCaseWithExperience):

    def __init__(self, *args, **kwargs):
        assert self.user_experience_start_date is not None
        assert self.user_experience_package_slot_start_date is not None
        super().__init__(*args, **kwargs)

    def create_users(self, after_create=list()):
        """
        Create users and call after create functions with
        params (userdetail, parsed_data)

        parsed_data is the return data of method get_parsed_data

        :param after_create: functions to call after create
        :type after_create: list
        """
        i = 0
        for user_dict in self.users:
            user = User.objects.create_user(
                email=user_dict.get('email'),
                first_name=user_dict.get('email').split('@')[0],
                last_name=user_dict.get('email').split('@')[1],
                password=user_dict.get('password'),
                username=user_dict.get('email'),

                is_active=True
            )

            self.created_users.append(user)
            UserOrganization.objects.create(
                user=user,
                organization=self.organization
            )

            code = "{}{}".format(self.organization.abbreviation, i)
            i += 1

            userdetail = UserDetail.objects.create(
                user=user,
                code=code,
                gender=user_dict.get('detail').get(
                    'gender', 'Male') if user_dict.get('detail') else 'Male',
                date_of_birth=get_default_date_of_birth(),
                organization=self.organization,
                joined_date=user_dict.get('detail').get(
                    'joined_date', get_today()) if user_dict.get('detail') else get_today(),
            )

            if not self.admin:
                self.admin = user
                Group.objects.get(name=ADMIN).user_set.add(user)

            for func in after_create:
                func(userdetail, user_dict)

    def create_experience(self, userdetail, parsed_data):
        job_title = parsed_data.get('job_title', 'Job Title')
        job_title, _ = EmploymentJobTitle.objects.get_or_create(
            organization=self.organization,
            title=job_title
        )

        # set user division head if not set
        if not self.division.head:
            self.division.head = userdetail.user
            self.division.save()

        data = {
            "organization": self.organization,
            "user": userdetail.user,
            "job_title": job_title,
            "division": self.division,
            "start_date": self.user_experience_start_date,
            "is_current": True,
            "current_step": 1
        }

        # One user one user exeoerience
        UserExperience.objects.create(**data)


    def create_packages(self):
        package_util = PackageUtil(organization=self.organization)
        package = package_util.create_package()
        return package


class PayrollBehaviourTestBaseClass(
    RHRSTestCaseWithUserExperience
):

    organization_name = 'Test'

    user_experience_package_slot_start_date = date(2017, 1, 1)
    user_experience_start_date = date(2017, 1, 1)

    users = [
        dict(
            email='employee@example.com',
            password='password',
            user_experience_start_date=date(2017, 1, 1),
            detail=dict(
                gender='Male',
                joined_date=get_today()
            )
        )
    ]

    payroll_mocked_settings = dict()

    def setUp(self):
        super().setUp()


        # START: Setup fiscal year
        fiscal_year = FiscalYear.objects.create(
            organization=self.organization,
            name="Test Fiscal Year",
            start_at=date(2017, 1, 1),
            end_at=date(2017, 12, 31),
            applicable_from=date(2017, 1, 1),
            applicable_to=date(2017, 12, 31)
        )

        fiscal_year_month_slots = [
            dict(
                start=date(2017, 1, 1),
                end=date(2017, 1, 31)
            ),
            dict(
                start=date(2017, 2, 1),
                end=date(2017, 2, 28)
            ),
            dict(
                start=date(2017, 3, 1),
                end=date(2017, 3, 31)
            ),
            dict(
                start=date(2017, 4, 1),
                end=date(2017, 4, 30)
            ),
            dict(
                start=date(2017, 5, 1),
                end=date(2017, 5, 31)
            ),
            dict(
                start=date(2017, 6, 1),
                end=date(2017, 6, 30)
            ),
            dict(
                start=date(2017, 7, 1),
                end=date(2017, 7, 31)
            ),
            dict(
                start=date(2017, 8, 1),
                end=date(2017, 8, 31)
            ),
            dict(
                start=date(2017, 9, 1),
                end=date(2017, 9, 30)
            ),
            dict(
                start=date(2017, 10, 1),
                end=date(2017, 10, 31)
            ),
            dict(
                start=date(2017, 11, 1),
                end=date(2017, 11, 30)
            ),
            dict(
                start=date(2017, 12, 1),
                end=date(2017, 12, 31)
            )
        ]

        fy_months_args = [
            FiscalYearMonth(
                fiscal_year=fiscal_year,
                month_index=i + 1,
                display_name=f"Month-{i + 1}",
                start_at=fiscal_year_month_slots[i].get('start'),
                end_at=fiscal_year_month_slots[i].get('end')
            ) for i in range(12)
        ]

        FiscalYearMonth.objects.bulk_create(fy_months_args)
        # END: Setup fiscal year

        OrganizationPayrollConfig.objects.create(
            organization=self.organization,
            start_fiscal_year=fiscal_year,
        )

        RebateSettingFactory(title=LIFE_INSURANCE, organization=self.organization)
        RebateSettingFactory(title=HEALTH_INSURANCE, organization=self.organization)

        self.create_user_experience_packge_slots()


    def create_user_experience_packge_slots(self):

        package = self.create_packages()

        self.user_packages = dict()

        for user in self.created_users:

            self.user_packages[user.id] = package

            UserExperiencePackageSlot.objects.create(
                user_experience=UserExperience.objects.get(
                    user=user,
                    organization=self.organization
                ),
                active_from_date=self.user_experience_package_slot_start_date,
                package=package
            )

    def create_packages(self):
        package_util = ExtraEarningTaxAdjustmentPackageUtil(
            organization=self.organization
        )
        package = package_util.create_package()
        return package

    @property
    def datework(self):
        return DateWork(
            # set start of fiscal year to jan 1
            fiscal_year_start_month_date=(1, 1)
        )

    def get_payroll(self, from_date, to_date, employee):

        rebate_amount = 0

        working_days = (30, 30)
        worked_days = (30, 30)

        with patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_organization',
            return_value=self.organization
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_hours_of_work',
            return_value=0
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_working_days',
            return_value=working_days
        ), patch(
            'irhrs.payroll.utils.calculator.EmployeeSalaryCalculator.get_worked_days',
            return_value=worked_days
        ):
            with self.settings(
                **self.payroll_mocked_settings
            ):
                calculator = EmployeeSalaryCalculator(
                    employee=employee,
                    datework=self.datework,
                    from_date=from_date,
                    to_date=to_date,
                    salary_package=self.user_packages[employee.id],
                    appoint_date=date(2017, 1, 1),
                    simulated_from=None,
                    extra_headings=dict()
                )

            payroll = self.create_payroll(from_date, to_date)

            calculator.payroll.record_to_model(payroll)

            return payroll, calculator

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
