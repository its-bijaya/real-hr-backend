from django.db import models

from irhrs.appraisal.constants import KAAR_QUESTION_SET
from irhrs.appraisal.models.key_achievement_and_rating_pa import KeyAchievementAndRatingAppraisal
from irhrs.appraisal.models.kpi import ExtendedIndividualKPI
from irhrs.appraisal.models.question_set import PerformanceAppraisalQuestion
from irhrs.common.models import BaseModel
from irhrs.task.models import UserResultArea
from irhrs.users.models import UserKSAO


class QuestionBaseModel(BaseModel):
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=False)
    remarks_required = models.BooleanField(default=False)

    class Meta:
        abstract = True


class KAARQuestionSet(BaseModel):
    kaar_appraisal = models.ForeignKey(
        KeyAchievementAndRatingAppraisal, related_name="question_set", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, blank=True)
    is_archived = models.BooleanField(default=False)
    question_type = models.CharField(choices=KAAR_QUESTION_SET, max_length=15)


class KPIQuestion(QuestionBaseModel):
    question_set = models.ForeignKey(
        KAARQuestionSet, related_name='kpi_questions', on_delete=models.CASCADE
    )
    extended_individual_kpi = models.ForeignKey(
        ExtendedIndividualKPI, related_name='kpi_questions', on_delete=models.CASCADE
    )


class KRAQuestion(QuestionBaseModel):
    question_set = models.ForeignKey(
        KAARQuestionSet, related_name='kra_questions', on_delete=models.CASCADE
    )
    kra = models.ForeignKey(
        UserResultArea, related_name='kra_questions', on_delete=models.CASCADE
    )


class KSAOQuestion(QuestionBaseModel):
    question_set = models.ForeignKey(
        KAARQuestionSet, related_name='ksao_questions', on_delete=models.CASCADE
    )
    ksao = models.ForeignKey(
        UserKSAO, related_name='ksao_questions', on_delete=models.CASCADE
    )


class GenericQuestionSet(BaseModel):
    question_set = models.ForeignKey(
        KAARQuestionSet, related_name='generic_questions', on_delete=models.CASCADE
    )
    generic_question = models.ForeignKey(
        PerformanceAppraisalQuestion, related_name='generic_questions', on_delete=models.CASCADE
    )




