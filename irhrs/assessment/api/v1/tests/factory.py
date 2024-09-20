from datetime import timedelta
import random
import factory
from factory.django import DjangoModelFactory

from irhrs.assessment.models import (
    AssessmentSet,
    AssessmentQuestions,
    AssessmentSection,
    UserAssessment,
)
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.questionnaire.api.v1.tests.factory import QuestionFactory
from irhrs.users.api.v1.tests.factory import UserFactory

class AssessmentQuestionFactory(DjangoModelFactory):
    class Meta:
        model = AssessmentQuestions

    question = factory.SubFactory(QuestionFactory)
    order = factory.Sequence(lambda n: n)
    assessment_section = factory.SubFactory('.AssessmentSectionFactory')


class AssessmentSectionFactory(DjangoModelFactory):
    class Meta:
        model = AssessmentSection

    assessment_set = factory.SubFactory('.AssessmentSetFactory')
    title = factory.Sequence(lambda n: f"Assessment Section-{n}")
    total_weightage = factory.LazyFunction(
        lambda: random.randint(0,20)
    )
    marginal_weightage = factory.LazyFunction(
        lambda: random.randint(0,20)
    )

    @factory.post_generation
    def assessment_questions(self, create, extracted, **kwargs):
        if not create:
            return
        AssessmentQuestionFactory(
            assessment_section=self,
            question__organization = self.assessment_set.organization,
            question__category__organization = self.assessment_set.organization
        )


class AssessmentSetFactory(DjangoModelFactory):
    class Meta:
        model = AssessmentSet

    organization = factory.SubFactory(OrganizationFactory)
    duration = factory.LazyFunction(
        lambda: timedelta(seconds=random.randint(0,100))
    )
    title = factory.Sequence(lambda n: f"Assessment Set-{n}")

    @factory.post_generation
    def sections(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            return

        sections = AssessmentSectionFactory(assessment_set=self)


class UserAssessmentFactory(DjangoModelFactory):
    class Meta:
        model = UserAssessment

    user = factory.SubFactory(UserFactory)
    assessment_set = factory.SubFactory(AssessmentSetFactory)
