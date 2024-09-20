from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models

from irhrs.appraisal.constants import (
    MONTHS, DURATION_OF_INVOLVEMENT_TYPE, DEDUCTION_TYPE,
    PERCENTAGE, APPRAISAL_TYPE, SELF_APPRAISAL
)
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlot
from irhrs.common.models import BaseModel
from irhrs.organization.models import (
    OrganizationBranch, OrganizationDivision, EmploymentStatus,
    EmploymentLevel, get_user_model
)

User = get_user_model()


class AppraisalSetting(BaseModel):
    sub_performance_appraisal_slot = models.OneToOneField(
        SubPerformanceAppraisalSlot,
        related_name='appraisal_setting',
        on_delete=models.CASCADE
    )
    duration_of_involvement = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    duration_of_involvement_type = models.CharField(
        max_length=6,
        choices=DURATION_OF_INVOLVEMENT_TYPE,
        default=MONTHS,
        db_index=True
    )
    branches = models.ManyToManyField(
        OrganizationBranch,
        related_name='branch_appraisal_settings',
    )
    divisions = models.ManyToManyField(
        OrganizationDivision,
        related_name='division_appraisal_settings',
    )
    employment_types = models.ManyToManyField(
        EmploymentStatus,
        related_name='employment_types_appraisal_settings',
    )
    employment_levels = models.ManyToManyField(
        EmploymentLevel,
        related_name='employment_levels_appraisal_settings',
    )

    def __str__(self):
        return f'{self.duration_of_involvement} {self.duration_of_involvement_type}'


class ExceptionalAppraiseeFilterSetting(BaseModel):
    """
    1. Input: user list, action_type and appraisal_type
    2. Edit
    """
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,
        related_name='exceptional_appraisee_filter_seetings',
        on_delete=models.CASCADE
    )
    appraisal_type = models.CharField(max_length=24, choices=APPRAISAL_TYPE,
                                      default=SELF_APPRAISAL,
                                      db_index=True)

    # include_user and exclude_user must be disjoint set
    include_users = models.ManyToManyField(User, related_name='+')
    exclude_users = models.ManyToManyField(User, related_name='+')

    class Meta:
        unique_together = ('sub_performance_appraisal_slot', 'appraisal_type')


class ScoreAndScalingSetting(BaseModel):
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,
        related_name='score_and_scaling_setting',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=125)

    # TODO @wrufesh scale field might not be required

    scale = models.IntegerField(validators=[MinValueValidator(1)])
    score = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f'{self.name} with score {self.score}'

    class Meta:
        ordering = 'score',


class DeadlineExtendCondition(BaseModel):
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,
        related_name='deadline_extend_condition',
        on_delete=models.CASCADE
    )
    total_appraise_count_ranges_from = models.IntegerField(validators=[MinValueValidator(0)])
    total_appraise_count_ranges_to = models.IntegerField(validators=[MinValueValidator(0)])
    extended_days = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f'For {self.total_appraise_count_ranges_from} - ' \
               f'{self.total_appraise_count_ranges_to} extended deadline by ' \
               f'{self.extended_days} days.'

    class Meta:
        ordering = 'total_appraise_count_ranges_from',


class DeadlineExceedScoreDeductionCondition(BaseModel):
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,
        related_name='deduction_condition',
        on_delete=models.CASCADE
    )
    deduction_type = models.CharField(max_length=10, choices=DEDUCTION_TYPE, default=PERCENTAGE,
                                      db_index=True)
    total_exceed_days_from = models.IntegerField(validators=[MinValueValidator(0)])
    total_exceed_days_to = models.IntegerField(validators=[MinValueValidator(0)])
    deduct_value = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f'{self.deduction_type}'

    class Meta:
        ordering = 'total_exceed_days_from',


class StepUpDownRecommendation(BaseModel):
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,
        related_name='step_up_down_recommendation',
        on_delete=models.CASCADE
    )
    score_acquired_from = models.IntegerField(validators=[MinValueValidator(0)])
    score_acquired_to = models.IntegerField(validators=[MinValueValidator(0)])
    change_step_by = models.IntegerField()

    class Meta:
        ordering = 'score_acquired_from',


class FormReviewSetting(BaseModel):
    sub_performance_appraisal_slot = models.OneToOneField(
        SubPerformanceAppraisalSlot,
        related_name='form_review_setting',
        on_delete=models.CASCADE
    )

    viewable_appraisal_submitted_form_type = ArrayField(
        models.CharField(
            max_length=25,
            choices=APPRAISAL_TYPE,
            default=SELF_APPRAISAL,
            db_index=True
        ),
        size=4
    )
    can_hr_download_form = models.BooleanField(default=False)
