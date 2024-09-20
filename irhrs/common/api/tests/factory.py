from irhrs.recruitment.models.common import JobBenefit, Salary
import random

import factory
from factory.django import DjangoModelFactory
from irhrs.recruitment.constants import APPROVED, VERIFICATION_STATUS_CHOICES

from irhrs.common.models import DocumentCategory, Bank, Skill, IdCardSample
from irhrs.common.models.commons import EquipmentCategory, Industry
from irhrs.common.models import DutyStation
from irhrs.core.constants.common import FIXED


class DocumentCategoryFactory(DjangoModelFactory):
    class Meta:
        model = DocumentCategory

    name = factory.Faker('word')
    associated_with = random.choice(["Employee", "Organization", "Both"])


class BankFactory(DjangoModelFactory):
    class Meta:
        model = Bank

    name = factory.Faker('name')
    acronym = factory.Faker('bank_country')


class SkillFactory(DjangoModelFactory):
    class Meta:
        model = Skill

    name = factory.Faker('name')
    description = factory.Faker('text', max_nb_chars=150)


class EquipmentCategoryFactory(DjangoModelFactory):
    class Meta:
        model = EquipmentCategory

    name = factory.Faker('name')
    type = FIXED


class IdCardSampleFactory(DjangoModelFactory):
    class Meta:
        model = IdCardSample

    name = factory.Faker('name')
    content = factory.Faker('text')


class DutyStationFactory(DjangoModelFactory):
    amount = factory.LazyAttribute(lambda x: random.randint(0, 100000))
    name = factory.Faker('name')

    class Meta:
        model = DutyStation

class IndustryFactory(DjangoModelFactory):
    class Meta:
        model = Industry

    name = factory.Faker('name')

class SalaryFactory(DjangoModelFactory):
    class Meta:
        model = Salary
    
    currency = factory.Faker('word')
    operator = factory.Faker('word')
    minimum = factory.Faker('random_number', digits=3)
    maximum = factory.Faker('random_number', digits=3)
    unit = factory.Faker('word')

class JobBenefitFactory(DjangoModelFactory):
    class Meta:
        model = JobBenefit

    name = factory.Faker('word')
    status = APPROVED
