from random import randint

import factory
from factory.django import DjangoModelFactory

from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.kpi import KPI
from irhrs.appraisal.models.performance_appraisal import (PerformanceAppraisalYear,
                                                          SubPerformanceAppraisalSlot,
                                                          SubPerformanceAppraisalSlotMode,
                                                          SubPerformanceAppraisalSlotWeight,
                                                          )
from irhrs.appraisal.models.question_set import (
    PerformanceAppraisalQuestion,
    PerformanceAppraisalQuestionSet,
    PerformanceAppraisalQuestionSection
)
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory, OrganizationFactory
from irhrs.questionnaire.api.v1.tests.factory import QuestionFactory
from irhrs.appraisal.models.performance_appraisal_setting import \
    DeadlineExceedScoreDeductionCondition, AppraisalSetting, ScoreAndScalingSetting, StepUpDownRecommendation


class PerformanceAppraisalYearFactory(DjangoModelFactory):
    class Meta:
        model = PerformanceAppraisalYear

    name = factory.Faker('text', max_nb_chars=100)
    year = factory.SubFactory(FiscalYearFactory)
    organization = factory.SubFactory(OrganizationFactory)


class SubPerformanceAppraisalSlotFactory(DjangoModelFactory):
    class Meta:
        model = SubPerformanceAppraisalSlot

    title = factory.Faker('text', max_nb_chars=100)
    weightage = randint(1, 100)
    from_date = factory.Faker('date')
    to_date = factory.Faker('date')
    performance_appraisal_year = factory.SubFactory(PerformanceAppraisalYearFactory)


class SubPerformanceAppraisalSlotModeFactory(DjangoModelFactory):
    class Meta:
        model = SubPerformanceAppraisalSlotMode


class AppraisalFactory(DjangoModelFactory):
    class Meta:
        model = Appraisal
    sub_performance_appraisal_slot = factory.SubFactory(SubPerformanceAppraisalSlotFactory)


class ScoreAndScalingSetttingFactory(DjangoModelFactory):
    class Meta:
        model = ScoreAndScalingSetting


class DeadlineExceedScoreDeductionConditionFactory(DjangoModelFactory):
    class Meta:
        model = DeadlineExceedScoreDeductionCondition
    sub_performance_appraisal_slot = factory.SubFactory(SubPerformanceAppraisalSlotFactory)


class AppraisalSettingFactory(DjangoModelFactory):
    class Meta:
        model = AppraisalSetting
    sub_performance_appraisal_slot = factory.SubFactory(SubPerformanceAppraisalSlotFactory)


class SubPerformanceAppraisalSlotWeightFactory(DjangoModelFactory):
    class Meta:
        model = SubPerformanceAppraisalSlotWeight
    sub_performance_appraisal_slot = factory.SubFactory(SubPerformanceAppraisalSlotFactory)

class StepUpDownRecommendationFactory(DjangoModelFactory):
    class Meta:
        model = StepUpDownRecommendation


class PerformanceAppraisalQuestionSetFactory(DjangoModelFactory):
    class Meta:
        model = PerformanceAppraisalQuestionSet

    name = factory.Faker('word')
    description = factory.Faker('sentence')
    is_archived = False
    organization = factory.SubFactory(OrganizationFactory)


class PerformanceAppraisalQuestionSectionFactory(DjangoModelFactory):
    class Meta:
        model = PerformanceAppraisalQuestionSection

    title = factory.Faker('word')
    description = factory.Faker('sentence')
    question_set = factory.SubFactory(PerformanceAppraisalQuestionSetFactory)


class PerformanceAppraisalQuestionFactory(DjangoModelFactory):
    class Meta:
        model = PerformanceAppraisalQuestion

    question_section = factory.SubFactory(PerformanceAppraisalQuestionSectionFactory)
    question = factory.SubFactory(QuestionFactory)
    order = factory.Sequence(lambda n: n)


class KPIFactory(DjangoModelFactory):
    class Meta:
        model = KPI

    title = factory.Faker('word')
    success_criteria = factory.Faker('sentence')
    organization = factory.SubFactory(OrganizationFactory)

    @factory.post_generation
    def job_title(self, create, job_list, **kwargs):
        if not (create and job_list):
            return
        self.job_title.set(job_list)

    @factory.post_generation
    def division(self, create, division_list, **kwargs):
        if not (create and division_list):
            return
        self.division.set(division_list)

    @factory.post_generation
    def employment_level(self, create, level_list, *kwargs):
        if not (create and level_list):
            return
        self.employment_level.set(level_list)
