from django.conf import settings
from django.db import models

from irhrs.appraisal.constants import APPRAISAL_TYPE, SELF_APPRAISAL, QUESTION_TYPE, KRA
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlot
from irhrs.appraisal.models.question_set import PerformanceAppraisalQuestionSet
from irhrs.common.models import BaseModel
from irhrs.questionnaire.models.helpers import ANSWER_TYPES, LONG


class PerformanceAppraisalFormDesign(BaseModel):
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,
        related_name='form_design',
        on_delete=models.CASCADE
    )
    appraisal_type = models.CharField(max_length=32, choices=APPRAISAL_TYPE,
                                      default=SELF_APPRAISAL, db_index=True)
    instruction_for_evaluator = models.CharField(
        max_length=10000,
        blank=True
    )
    include_kra = models.BooleanField(default=False)
    caption_for_kra = models.CharField(max_length=255, blank=True)
    include_ksa = models.BooleanField(default=False)
    caption_for_ksa = models.CharField(max_length=255, blank=True)
    include_kpi = models.BooleanField(default=False)
    caption_for_kpi = models.CharField(max_length=255, blank=True)
    generic_question_set = models.ForeignKey(
        PerformanceAppraisalQuestionSet,
        on_delete=models.SET_NULL,
        related_name='form_designs',
        null=True,
        blank=True,
    )
    add_feedback = models.BooleanField(default=False)

    class Meta:
        unique_together = ('sub_performance_appraisal_slot', 'appraisal_type')

    def __str__(self):
        return self.appraisal_type


class PerformanceAppraisalAnswerType(BaseModel):
    form_design = models.ForeignKey(
        PerformanceAppraisalFormDesign,
        related_name='answer_types',
        on_delete=models.CASCADE
    )
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPE, default=KRA,
                                     db_index=True)
    answer_type = models.CharField(max_length=22, choices=ANSWER_TYPES, default=LONG,
                                   db_index=True)
    description = models.CharField(
        max_length=settings.TEXT_FIELD_MAX_LENGTH, blank=True)
    is_mandatory = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.form_design}: {self.question_type} : {self.answer_type}"


class ResendPAForm(BaseModel):
    """
    PA forms can be resent multiple times.
    """
    reason = models.CharField(
        max_length=600,
    )

    def __str__(self):
        return f'{self.reason}'


class KAARFormDesign(BaseModel):
    sub_performance_appraisal_slot = models.OneToOneField(
        SubPerformanceAppraisalSlot,
        related_name='kaar_form_design',
        on_delete=models.CASCADE
    )
    instruction_for_evaluator = models.CharField(
        max_length=10000,
        blank=True
    )
    include_kra = models.BooleanField(default=False)
    caption_for_kra = models.CharField(max_length=255, blank=True)
    include_ksa = models.BooleanField(default=False)
    caption_for_ksa = models.CharField(max_length=255, blank=True)
    include_kpi = models.BooleanField(default=False)
    caption_for_kpi = models.CharField(max_length=255, blank=True)
    generic_question_set = models.ForeignKey(
        PerformanceAppraisalQuestionSet,
        on_delete=models.SET_NULL,
        related_name='kaar_form_designs',
        null=True,
        blank=True,
    )
    add_feedback = models.BooleanField(default=False)

    def __str__(self):
        return f" form design of  {self.sub_performance_appraisal_slot.title}."


class KAARAnswerType(BaseModel):
    form_design = models.ForeignKey(
        KAARFormDesign,
        related_name='kaar_answer_types',
        on_delete=models.CASCADE
    )
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPE, default=KRA,
                                     db_index=True)
    answer_type = models.CharField(max_length=22, choices=ANSWER_TYPES, default=LONG,
                                   db_index=True)
    description = models.CharField(
        max_length=settings.TEXT_FIELD_MAX_LENGTH, blank=True)
    is_mandatory = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.form_design}: {self.question_type} : {self.answer_type}"
