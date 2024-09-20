import random

import factory
from factory.django import DjangoModelFactory

from irhrs.questionnaire.models.helpers import ANSWER_TYPES, QUESTION_TYPES
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.questionnaire.models.questionnaire import QuestionCategory, Question


class QuestionCategoryFactory(DjangoModelFactory):
    class Meta:
        model = QuestionCategory

    title = factory.Faker('text', max_nb_chars=225)
    organization = factory.SubFactory(OrganizationFactory)
    description = factory.Faker('text', max_nb_chars=225)
    category = random.choice(list(dict(QUESTION_TYPES).keys()))
    organization = factory.SubFactory(OrganizationFactory)


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question

    title = factory.Faker('text', max_nb_chars=225)
    category = factory.SubFactory(QuestionCategoryFactory)
    organization = factory.SubFactory(OrganizationFactory)
    description = factory.Faker('text', max_nb_chars=225)
    answer_choices = random.choice(list(dict(ANSWER_TYPES).keys()))
    question_type = random.choice(list(dict(QUESTION_TYPES).keys()))
    order = factory.Sequence(lambda n: n)
    weightage = factory.Sequence(lambda n: n)
    is_open_ended = True
    difficulty_level = factory.Sequence(lambda n: random.randint(1, 10))
    rating_scale = factory.Sequence(lambda n: random.randint(1, 10))
    category = factory.SubFactory(QuestionCategoryFactory)
    organization = factory.SubFactory(OrganizationFactory)
