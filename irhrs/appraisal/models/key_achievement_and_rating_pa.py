from rest_framework.exceptions import ValidationError

from irhrs.appraisal.constants import SELF_APPRAISAL, APPRAISAL_TYPE, KAAR_QUESTION_STATUS, \
    NOT_GENERATED, REVIEWER_EVALUATION, KAAR_APPRAISAL_STATUS, IDLE, SUPERVISOR_APPRAISAL, \
    KAAR_QUESTION_SET
from irhrs.common.models import BaseModel
from django.contrib.auth import get_user_model
from django.db import models
from irhrs.core.validators import MinMaxValueValidator
from irhrs.appraisal.models.form_design import ResendPAForm
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlot

User = get_user_model()


class KeyAchievementAndRatingAppraisal(BaseModel):
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,
        related_name='kaar_appraisals',
        on_delete=models.CASCADE,
    )
    appraisee = models.ForeignKey(
        User,
        related_name='as_kaar_appraisees',
        on_delete=models.CASCADE,
        help_text='Person for whom performance appraisal is being conducted'
    )

    resend = models.ForeignKey(ResendPAForm,
                               on_delete=models.CASCADE,
                               related_name='kaar_appraisals',
                               null=True,
                               blank=True)

    total_score = models.JSONField(null=True)
    overall_rating = models.JSONField(null=True)
    status = models.CharField(
        max_length=20, choices=KAAR_APPRAISAL_STATUS, default=IDLE
    )
    display_to_appraisee = models.BooleanField(default=False)
    is_appraisee_satisfied = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return f"appraisal of {self.appraisee}"


class KAARAppraiserConfig(BaseModel):
    kaar_appraisal = models.ForeignKey(
        KeyAchievementAndRatingAppraisal,
        related_name='appraiser_configs',
        on_delete=models.CASCADE
    )
    appraiser = models.ForeignKey(
        User,
        related_name='appraiser_configs',
        on_delete=models.CASCADE,
        help_text='Person who gives review for appraisee'
    )
    appraiser_type = models.CharField(max_length=32, choices=APPRAISAL_TYPE,
                                      default=SELF_APPRAISAL, db_index=True)
    question_status = models.CharField(
        max_length=15, choices=KAAR_QUESTION_STATUS, default=NOT_GENERATED
    )
    total_score = models.JSONField(null=True)
    start_date = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"appraise {self.kaar_appraisal.appraisee} and appraiser {self.appraiser}"


class BaseEvaluationModel(BaseModel):
    comment = models.TextField(blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        abstract = True


class ReviewerEvaluation(BaseEvaluationModel):
    appraiser = models.OneToOneField(
        KAARAppraiserConfig, related_name="reviewer_evaluation", on_delete=models.CASCADE
    )
    agree_with_appraiser = models.BooleanField(default=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.appraiser.appraiser_type != REVIEWER_EVALUATION:
            raise ValidationError(f"Appraiser type should be {REVIEWER_EVALUATION}")
        super().save(force_insert, force_update, using, update_fields)


class SupervisorEvaluation(BaseEvaluationModel):
    appraiser = models.OneToOneField(
        KAARAppraiserConfig, related_name="supervisor_evaluation", on_delete=models.CASCADE
    )
    set_default_rating = models.BooleanField(default=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.appraiser.appraiser_type != SUPERVISOR_APPRAISAL:
            raise ValidationError(f"Appraiser type should be {SUPERVISOR_APPRAISAL}")
        super().save(force_insert, force_update, using, update_fields)


