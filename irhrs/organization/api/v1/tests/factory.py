from irhrs.core.constants.common import SKILL
import json
from datetime import timedelta
import factory
from factory.django import DjangoModelFactory
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from irhrs.common.api.tests.factory import DocumentCategoryFactory, EquipmentCategoryFactory
from irhrs.core.constants.organization import PRIVATE, USER
from irhrs.core.utils.common import get_today
from irhrs.organization.models import (
    Organization, Holiday, HolidayRule, EquipmentAssignedTo,
    MeetingRoom, MeetingRoomStatus, OrganizationBranch, OrganizationDivision,
    EmploymentLevel, EmploymentStatus,
    EmploymentJobTitle, OrganizationDocument, OrganizationVision,
    OrganizationMission, OrganizationEthics, OrganizationEquipment,
    FiscalYear, FiscalYearMonth, ContractSettings
)
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.organization.models.settings import EmailNotificationSetting


class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.sequence(lambda n: f"name {n}")
    abbreviation = factory.LazyAttribute(lambda o: o.name[:5])
    ownership = PRIVATE
    size = '1 - 10 employees'
    contacts = {}
    # branch = factory.RelatedFactory(OrganizationBranchFactory, 'organization')
    # division = factory.RelatedFactory(
    #     'irhrs.organization.api.v1.tests.factory.OrganizationDivisionFactory',
    #     'organization')


class OrganizationBranchFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationBranch

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Faker('text', max_nb_chars=16)
    description = factory.Faker('text', max_nb_chars=512)
    contacts = json.dumps(
        {
            'Mobile': '9874563210'
        }
    )
    email = factory.Faker('email')


class OrganizationDivisionFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationDivision

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Faker('text', max_nb_chars=16)
    description = factory.Faker('text', max_nb_chars=512)
    email = factory.Faker('email')


class EmploymentLevelFactory(DjangoModelFactory):
    class Meta:
        model = EmploymentLevel

    title = factory.Faker('text', max_nb_chars=150)
    description = factory.Faker('text', max_nb_chars=500)
    organization = factory.SubFactory(OrganizationFactory)
    order_field = 1
    scale_max = 20


class EmploymentStatusFactory(DjangoModelFactory):
    class Meta:
        model = EmploymentStatus

    title = factory.Faker('text', max_nb_chars=150)
    organization = factory.SubFactory(OrganizationFactory)
    description = factory.Faker('text', max_nb_chars=500)
    is_contract = True


class EmploymentJobTitleFactory(DjangoModelFactory):
    class Meta:
        model = EmploymentJobTitle

    title = factory.Faker('text', max_nb_chars=150)
    organization = factory.SubFactory(OrganizationFactory)


class HolidayRuleFactory(DjangoModelFactory):
    class Meta:
        model = HolidayRule

    gender = 'All'


class HolidayFactory(DjangoModelFactory):
    class Meta:
        model = Holiday

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Faker('name')
    description = factory.Faker('text')
    date = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def rule(self, create, extracted, **kwargs):
        if not create:
            return
        if not extracted:
            HolidayRuleFactory(holiday=self)


class MeetingRoomFactory(DjangoModelFactory):
    class Meta:
        model = MeetingRoom

    organization = factory.SubFactory(OrganizationFactory)
    branch = factory.SubFactory(OrganizationBranchFactory)
    name = factory.Faker('text', max_nb_chars=32)
    description = factory.Faker('sentence', nb_words=10)
    location = factory.Faker('address')
    floor = '1st'
    area = '120 sq ft'
    capacity = 100


class MeetingRoomStatusFactory(DjangoModelFactory):
    class Meta:
        model = MeetingRoomStatus

    meeting_room = factory.SubFactory(MeetingRoomFactory)
    # booked for tomorrow from 12PM - 6PM
    booked_from = get_today(with_time=True, reset_hours=True) + timedelta(days=1, hours=12)
    booked_to = get_today(with_time=True, reset_hours=True) + timedelta(days=1, hours=18)


class OrganizationDocumentFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationDocument

    organization = factory.SubFactory(OrganizationFactory)
    category = factory.SubFactory(DocumentCategoryFactory)
    title = factory.sequence(lambda n: f"name {n}")
    description = factory.Faker('sentence')


class OrganizationVisionFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationVision

    title = factory.Faker('text', max_nb_chars=512)
    organization = factory.SubFactory(OrganizationFactory)


class OrganizationMissionFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationMission

    organization = factory.SubFactory(OrganizationFactory)
    title = factory.Faker('text', max_nb_chars=255)
    description = factory.Faker('text', max_nb_chars=500)
    order_field = factory.Sequence(lambda n: n)


class OrganizationEthicsFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationEthics

    organization = factory.SubFactory(OrganizationFactory)
    title = factory.Faker('text', max_nb_chars=255)
    description = factory.Faker('text', max_nb_chars=610)


class EquipmentFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationEquipment

    name = factory.Faker('name')
    code = factory.Sequence(lambda n: '123A555%04d' % n)
    assigned_to = USER
    category = factory.SubFactory(EquipmentCategoryFactory)
    organization = factory.SubFactory(OrganizationFactory)


class EquipmentAssignedToFactory(DjangoModelFactory):
    class Meta:
        model = EquipmentAssignedTo

    equipment = factory.SubFactory(EquipmentFactory)


class FiscalYearMonthFactory(DjangoModelFactory):
    display_name = factory.Faker('text', max_nb_chars=20)

    class Meta:
        model = FiscalYearMonth


class FiscalYearFactory(DjangoModelFactory):
    class Meta:
        model = FiscalYear

    name = factory.Faker('text', max_nb_chars=100)
    description = factory.Faker('text', max_nb_chars=610)
    start_at = timezone.now().date() - relativedelta(days=30)
    end_at = timezone.now().date() + relativedelta(days=30)
    applicable_from = timezone.now().date() - relativedelta(days=30)
    applicable_to = timezone.now().date() + relativedelta(days=30)
    organization = factory.SubFactory(OrganizationFactory)

    @factory.post_generation
    def fiscal_months(self, create, extracted, **kwargs):

        def generate_fiscal_months(end_date_):
            a_year_ago = end_date_ - relativedelta(years=1) + timedelta(days=1)
            for ind in range(12):
                FiscalYearMonthFactory(
                    fiscal_year=self,
                    month_index=ind + 1,
                    start_at=(a_year_ago + relativedelta(months=ind)),
                    end_at=(a_year_ago + relativedelta(months=ind + 1) -
                            relativedelta(days=1)),
                )

        if not create:
            return
        if extracted:
            return
        generate_fiscal_months(self.end_at)
        self.save()


class KSAFactory(DjangoModelFactory):
    class Meta:
        model = KnowledgeSkillAbility

    name = factory.sequence(lambda n: f'name {n}')
    description = factory.Faker('text')


class ContractSettingsFactory(DjangoModelFactory):
    class Meta:
        model = ContractSettings

    organization = factory.SubFactory(OrganizationFactory)


class KnowledgeSkillAbilityFactory(DjangoModelFactory):
    class Meta:
        model = KnowledgeSkillAbility
    
    name = factory.Faker('name')
    description = factory.Faker('text')
    ksa_type = SKILL


class EmailNotificationSettingFactory(DjangoModelFactory):
    class Meta:
        model = EmailNotificationSetting
