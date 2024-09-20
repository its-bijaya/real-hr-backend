import factory
from factory.django import DjangoModelFactory

from irhrs.forms.models import (
    Form,
    UserForm,
    UserFormAnswerSheet,
    AnonymousFormAnswerSheet,
    FormQuestionSection,
    FormQuestionSet,
    FormApprovalSettingLevel,
    FormAnswerSheetApproval,
    UserFormIndividualQuestionAnswer,
    AnonymousFormIndividualQuestionAnswer,
    FormQuestion
)
from irhrs.core.constants.payroll import (
    EMPLOYEE,
    ALL
)
from irhrs.forms.constants import APPROVED, DENIED, PENDING
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.questionnaire.api.v1.tests.factory import QuestionFactory


class FormQuestionSetFactory(DjangoModelFactory):
    class Meta:
        model = FormQuestionSet

    name = factory.Faker('word')
    description = factory.Faker('sentence')
    is_archived = False
    organization = factory.SubFactory(OrganizationFactory)


class FormFactory(DjangoModelFactory):
    class Meta:
        model = Form

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Faker('word')
    description = factory.Faker('sentence')
    question_set = factory.SubFactory(FormQuestionSetFactory)


class FormQuestionSectionFactory(DjangoModelFactory):
    class Meta:
        model = FormQuestionSection

    title = factory.Faker('word')
    description = factory.Faker('sentence')
    question_set = factory.SubFactory(FormQuestionSetFactory)


class UserFormFactory(DjangoModelFactory):
    class Meta:
        model = UserForm

    user = factory.SubFactory(UserFactory)
    form = factory.SubFactory(FormFactory)


class FormQuestionFactory(DjangoModelFactory):
    class Meta:
        model = FormQuestion

    question_section = factory.SubFactory(FormQuestionSectionFactory)
    question = factory.SubFactory(QuestionFactory)
    order = factory.Sequence(lambda n: n)


class AnonymousFormAnswerSheetFactory(DjangoModelFactory):
    class Meta:
        model = AnonymousFormAnswerSheet

    form = factory.SubFactory(FormFactory)

class UserFormAnswerSheetFactory(DjangoModelFactory):
    class Meta:
        model = UserFormAnswerSheet

    user = factory.SubFactory(UserFactory)
    form = factory.SubFactory(FormFactory)

class UserFormIndividualQuestionAnswerFactory(DjangoModelFactory):
    class Meta:
        model = UserFormIndividualQuestionAnswer

    answer_sheet = factory.SubFactory(UserFormAnswerSheetFactory)

class AnonymousFormIndividualQuestionAnswerFactory(DjangoModelFactory):
    class Meta:
        model = AnonymousFormIndividualQuestionAnswer

class FormApprovalSettingLevelFactory(DjangoModelFactory):
    class Meta:
        model = FormApprovalSettingLevel

class FormAnswerSheetApprovalFactory(DjangoModelFactory):
    class Meta:
        model = FormAnswerSheetApproval
