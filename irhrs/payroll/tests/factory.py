import random

import factory
from factory.django import DjangoModelFactory

from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.payroll.models import (
    Heading,
    HEADING_TYPES,
    PAYROLL_SETTING_TYPES,
    AdvanceSalarySetting,
    AmountSetting,
    ApprovalSetting,
    Package,
    Operation,
    OperationCode,
    OperationRate,
    Payroll,
    EmployeePayroll,
    ReportRowRecord,
    CONFIRMED,
    PENDING,
    UserExperiencePackageSlot,
    OverviewConfig,
    UserVoluntaryRebate
)

from irhrs.payroll.models.payroll import BackdatedCalculation, OrganizationPayrollConfig, \
    RebateSetting
from irhrs.users.api.v1.tests.factory import UserFactory, UserExperienceFactory

class HeadingFactory(DjangoModelFactory):
    class Meta:
        model = Heading

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Faker('text', max_nb_chars=150)
    type = random.choice(list(dict(HEADING_TYPES).keys()))
    payroll_setting_type = random.choice(list(dict(PAYROLL_SETTING_TYPES).keys()))
    order = factory.Sequence(lambda n: n)
    rules = {}


class PackageFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Package-{n}")

    class Meta:
        model = Package


# --- Advance Salary Factory

class AmountSettingFactory(DjangoModelFactory):
    multiple = 1

    class Meta:
        model = AmountSetting


class ApprovalSettingFactory(DjangoModelFactory):
    class Meta:
        model = ApprovalSetting


class AdvanceSalarySettingsFactory(DjangoModelFactory):
    class Meta:
        model = AdvanceSalarySetting


class OperationFactory(DjangoModelFactory):
    title = factory.sequence(lambda n: f'Title {n}')
    description = factory.Faker('text', max_nb_chars=600)
    organization = factory.SubFactory(OrganizationFactory)

    class Meta:
        model = Operation


class OperationCodeFactory(DjangoModelFactory):
    title = factory.sequence(lambda n: f'Title {n}')
    description = factory.Faker('text', max_nb_chars=600)
    organization = factory.SubFactory(OrganizationFactory)

    class Meta:
        model = OperationCode


class OperationRateFactory(DjangoModelFactory):
    operation = factory.SubFactory(OperationFactory)
    operation_code = factory.SubFactory(OperationCodeFactory)
    rate = 20

    class Meta:
        model = OperationRate

# Backdated calculation factory
class UserExperiencePackageSlotFactory(DjangoModelFactory):
    active_from_date = factory.Faker('date')

    class Meta:
        model = UserExperiencePackageSlot


class BackdatedCalculationFactory(DjangoModelFactory):
    heading = factory.SubFactory(HeadingFactory)
    previous_amount = factory.Faker('random_number', digits=5)
    current_amount = factory.Faker('random_number', digits=5)

    class Meta:
        model = BackdatedCalculation


class OrganizationPayrollConfigFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationPayrollConfig


class OverviewConfigFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)

    class Meta:
        model = OverviewConfig

class ReportRowRecordFactory(DjangoModelFactory):
    amount = 100
    projected_amount = 1000
    class Meta:
        model=ReportRowRecord

class PayrollFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    from_date = factory.Faker('date')
    to_date = factory.Faker('date')
    status = PENDING
    extra_data = {}
    class Meta:
        model = Payroll

class EmployeePayrollFactory(DjangoModelFactory):
    employee = factory.SubFactory(UserFactory)
    package = factory.SubFactory(PackageFactory)
    payroll = factory.SubFactory(PayrollFactory)

    class Meta:
        model = EmployeePayroll

class ConfirmedEmployeePayrollFactory(DjangoModelFactory):
    employee = factory.SubFactory(UserFactory)
    package = factory.SubFactory(PackageFactory)

    class Meta:
        model = EmployeePayroll

    @factory.post_generation
    def report_rows(self, *args, **kwargs):
        headings = kwargs.get('headings')
        from_date = kwargs.get('from_date')
        to_date = kwargs.get('to_date')
        for heading in headings:
            ReportRowRecordFactory(
                employee_payroll=self,
                heading=heading,
                from_date=from_date,
                to_date=to_date
            )


class ConfirmedPayrollFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    status = CONFIRMED
    extra_data = {}
    class Meta:
        model = Payroll

    @factory.post_generation
    def employee_payrolls(self, *args, **kwargs):
        ConfirmedEmployeePayrollFactory(
            employee=kwargs.get('employee'),
            payroll=self,
            package=kwargs.get('package'),
            report_rows__headings=kwargs.get('report_rows_headings'),
            report_rows__from_date=kwargs.get('report_rows_from_date'),
            report_rows__to_date=kwargs.get('report_rows_to_date')
        )


class RebateSettingFactory(DjangoModelFactory):
    title = factory.Faker('name')
    amount = 20000
    duration_type = "Yearly"
    is_archived = False
    organization = factory.SubFactory(OrganizationFactory)

    class Meta:
        model = RebateSetting


class UserVoluntaryRebateFactory(DjangoModelFactory):
    amount = factory.LazyAttribute(lambda x: random.randint(0, 100000))
    rebate = factory.SubFactory(RebateSettingFactory)
    description = factory.Faker('text', max_nb_chars=120)

    class Meta:
        model = UserVoluntaryRebate
