import random
import datetime
import factory
from factory.django import DjangoModelFactory

from irhrs.common.api.tests.factory import IdCardSampleFactory, \
    DutyStationFactory
from irhrs.core.utils.common import get_today
from irhrs.core.constants.user import RESIGNED
from irhrs.users.models import UserDetail
from irhrs.hris.models import (
    ChangeType, IdCardTemplate, IdCard, \
    DutyStationAssignment, EmployeeSeparationType, \
    EmployeeSeparation, PreEmployment, EmploymentReview,
    EmployeeChangeTypeDetail,
    ResignationApprovalSetting,
    UserResignation,
    HRApprovalUserResignation,
    UserResignationApproval,
)

from irhrs.organization.api.v1.tests.factory import (
    OrganizationFactory,
    EmploymentLevelFactory,
)
from irhrs.users.api.v1.tests.factory import (
    UserFactory,
    EmploymentJobTitleFactory,
    EmploymentStatusFactory,
    OrganizationDivisionFactory,
)
from irhrs.core.constants.payroll import FIRST


class ChangeTypeFactory(DjangoModelFactory):
    class Meta:
        model = ChangeType

    title = factory.Faker('text', max_nb_chars=150)
    affects_experience = False
    affects_payroll = False
    affects_work_shift = False
    affects_core_tasks = False
    affects_leave_balance = False
    organization = factory.SubFactory(OrganizationFactory)


class IdCardTemplateFactory(DjangoModelFactory):
    class Meta:
        model = IdCardTemplate

    name = factory.Faker('name')
    sample = factory.SubFactory(IdCardSampleFactory)
    organization = factory.SubFactory(OrganizationFactory)
    logo = factory.django.ImageField(color='blue')
    background_image = factory.django.ImageField(color='black')


class IdCardFactory(DjangoModelFactory):
    class Meta:
        model = IdCard

    template = factory.SubFactory(IdCardTemplateFactory)
    user = factory.SubFactory(UserFactory)
    profile_picture = factory.django.ImageField(color='pink')
    issued_on = factory.Faker('date')


class DutyStationAssignmentFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    to_date = factory.LazyAttribute(
        lambda x: datetime.date.today() +
        datetime.timedelta(
            days=random.randint(
                0,
                2)),
    )
    from_date = factory.LazyAttribute(
        lambda x: datetime.date.today() -
        datetime.timedelta(
            days=random.randint(
                0,
                2)),
    )
    organization = factory.SubFactory(OrganizationFactory)
    duty_station = factory.SubFactory(DutyStationFactory)

    class Meta:
        model = DutyStationAssignment


class EmployeeSeparationTypeFactory(DjangoModelFactory):
    title = factory.sequence(lambda n: f"Separation Type {n}")
    category = RESIGNED
    organization = factory.SubFactory(OrganizationFactory)

    class Meta:
        model = EmployeeSeparationType


class EmployeeSeparationFactory(DjangoModelFactory):
    employee = factory.SubFactory(UserFactory)
    separation_type = factory.lazy_attribute(
        lambda s: EmployeeSeparationTypeFactory(organization=s.employee.detail.organization)
    )
    remarks = "Employee Separation Remarks"

    class Meta:
        model = EmployeeSeparation


class PreEmployementFactory(DjangoModelFactory):
    class Meta:
        model = PreEmployment

    organization = factory.SubFactory(OrganizationFactory)
    employment_status = factory.SubFactory(EmploymentStatusFactory)
    employment_level = factory.SubFactory(EmploymentLevelFactory)
    job_title = factory.SubFactory(EmploymentJobTitleFactory)
    division = factory.SubFactory(OrganizationDivisionFactory)
    deadline = get_today(with_time=True) + datetime.timedelta(days=1)
    date_of_join = get_today() + datetime.timedelta(days=5)


class EmploymentReviewFactory(DjangoModelFactory):
    employee = factory.SubFactory(UserFactory)
    change_type = factory.SubFactory(ChangeTypeFactory)

    class Meta:
        model = EmploymentReview

    @factory.lazy_attribute
    def detail(self):
        EmployeeChangeTypeDetailFactory(detail=self)


class EmployeeChangeTypeDetailFactory(DjangoModelFactory):

    class Meta:
        model = EmployeeChangeTypeDetail


class ResignationApprovalSettingFactory(DjangoModelFactory):
    class Meta:
        model = ResignationApprovalSetting

    organization = factory.SubFactory(OrganizationFactory)
    employee = factory.SubFactory(UserFactory)
    supervisor_level = FIRST
    approval_level = 1


class UserResignationFactory(DjangoModelFactory):
    class Meta:
        model = UserResignation

    employee = factory.SubFactory(UserFactory)
    recipient = factory.SubFactory(UserFactory)
    release_date = get_today() + datetime.timedelta(days=1)


class UserResignationApprovalFactory(DjangoModelFactory):
    class Meta:
        model = UserResignationApproval

    resignation = factory.SubFactory(UserResignationFactory)
    user = factory.SubFactory(UserFactory)
