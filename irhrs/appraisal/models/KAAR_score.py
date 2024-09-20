from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from rest_framework.exceptions import ValidationError

from irhrs.appraisal.constants import RATING_SCALE, DEFAULT, RANGE, GRADE, KAAR_QUESTION_SET
from irhrs.appraisal.models.KAAR_question import KRAQuestion, KPIQuestion, KSAOQuestion, \
    KAARQuestionSet
from irhrs.appraisal.models.key_achievement_and_rating_pa import KAARAppraiserConfig, \
    KeyAchievementAndRatingAppraisal
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlot
from irhrs.appraisal.models.question_set import PerformanceAppraisalQuestion
from irhrs.common.models import BaseModel


class ScoreAndScalingConfig(BaseModel):
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,
        related_name='score_and_scaling_configs',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=100)
    scale_type = models.CharField(choices=RATING_SCALE, default=DEFAULT, max_length=20)

    def delete(self, using=None, keep_parents=False):
        if any((hasattr(self, 'range_score'), self.grade_and_default_scales.exists())):
            raise ValidationError({'error': "Can't delete assigned score setting."})
        return super().delete(using, keep_parents)


class RangeScore(BaseModel):
    score_config = models.OneToOneField(
        ScoreAndScalingConfig,
        related_name='range_score',
        on_delete=models.CASCADE
    )
    start_range = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    end_range = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])

    def __str__(self):
        return f"Range score wth start range {self.start_range} and end range {self.end_range}."

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.score_config.scale_type != RANGE:
            return ValidationError(f"Only {RANGE} type is acceptable for range model.")
        super().save(force_insert, force_update, using, update_fields)


class GradeAndDefaultScaling(BaseModel):
    score_config = models.ForeignKey(
        ScoreAndScalingConfig,
        related_name='grade_and_default_scales',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    score = models.IntegerField(validators=[MinValueValidator(0)])

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.score_config.scale_type == RANGE:
            return ValidationError(f"{RANGE} type is acceptable user {DEFAULT} or {GRADE} scales.")
        super().save(force_insert, force_update, using, update_fields)


class KAARScaleAndScoreSetting(BaseModel):
    sub_performance_appraisal_slot = models.OneToOneField(
        SubPerformanceAppraisalSlot,
        related_name='kaar_score_setting',
        on_delete=models.CASCADE
    )
    kpi = models.ForeignKey(
        ScoreAndScalingConfig,
        related_name='kpi_score_setting',
        on_delete=models.CASCADE
    )
    ksao = models.ForeignKey(
        ScoreAndScalingConfig,
        related_name='kaso_score_setting',
        on_delete=models.CASCADE
    )
    question_set = models.ForeignKey(
        ScoreAndScalingConfig,
        related_name='question_set_score_setting',
        on_delete=models.CASCADE
    )


class RatingScaleBaseModel(BaseModel):
    score = models.FloatField(null=True, blank=True)
    grade_score = models.CharField(max_length=255, null=True, blank=True)
    remarks = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        scores = (self.score, self.grade_score)
        if not any(scores):
            raise ValidationError({'score': 'score field is mandatory.'})
        if all(scores):
            raise ValidationError({'error': "Can't assign score and grade score."})
        super().save(force_insert, force_update, using, update_fields)


class DefaultScoreSetting(BaseModel):
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,  on_delete=models.CASCADE, related_name='default_scores'
    )
    question_type = models.CharField(choices=KAAR_QUESTION_SET, max_length=20)
    score = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    grade_score = models.CharField(max_length=255, null=True, blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        scores = (self.score, self.grade_score)
        if not any(scores):
            raise ValidationError({'score': 'score field is mandatory.'})
        if all(scores):
            raise ValidationError({'error': "Can't assign score and grade score."})
        super().save(force_insert, force_update, using, update_fields)


class KPIQuestionScore(RatingScaleBaseModel):
    question = models.ForeignKey(
        KPIQuestion, related_name='kpi_scores', on_delete=models.CASCADE
    )
    appraiser = models.ForeignKey(
        KAARAppraiserConfig,
        related_name='kpi_scores',
        on_delete=models.CASCADE
    )
    key_achievements = models.TextField(blank=True, null=True)


class KRAQuestionScore(RatingScaleBaseModel):
    question = models.ForeignKey(
        KRAQuestion, related_name='kra_scores', on_delete=models.CASCADE
    )
    appraiser = models.ForeignKey(
        KAARAppraiserConfig,
        related_name='kra_scores',
        on_delete=models.CASCADE
    )


class KSAOQuestionScore(RatingScaleBaseModel):
    question = models.ForeignKey(
        KSAOQuestion,
        related_name='ksao_scores',
        on_delete=models.CASCADE
    )
    appraiser = models.ForeignKey(
        KAARAppraiserConfig,
        related_name='ksao_scores',
        on_delete=models.CASCADE
    )


class PerformanceAppraisalQuestionScore(BaseModel):
    question = models.ForeignKey(
        PerformanceAppraisalQuestion, related_name='question_scores', on_delete=models.CASCADE
    )
    appraiser = models.ForeignKey(
        KAARAppraiserConfig,
        related_name='pa_question_scores',
        on_delete=models.CASCADE
    )
    data = models.JSONField()


class AnnualRatingOnCompetencies(BaseModel):
    kaar_appraisal = models.ForeignKey(
        KeyAchievementAndRatingAppraisal,
        related_name='annual_rating',
        on_delete=models.CASCADE
    )
    question_set = models.OneToOneField(
        KAARQuestionSet, related_name="annual_rating", on_delete=models.CASCADE
    )
    final_score = models.CharField(max_length=255)
