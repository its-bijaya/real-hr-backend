from django.contrib.auth import get_user_model
from django.db.models import JSONField
from django.db import models

from irhrs.appraisal.constants import APPRAISAL_TYPE, SELF_APPRAISAL
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlot
from irhrs.appraisal.models.form_design import ResendPAForm
from irhrs.common.models import BaseModel
from irhrs.core.validators import MinMaxValueValidator

User = get_user_model()


class Appraisal(BaseModel):
    """Validate data according to type of appraisal

    unique_together (appraisee, appraiser, appraisal_type)

    'answer_committed' field can only be set true when all required questions
    has been answered
    """
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,
        related_name='appraisals',
        on_delete=models.CASCADE,
    )
    appraisee = models.ForeignKey(
        User,
        related_name='as_appraisees',
        on_delete=models.CASCADE,
        help_text='Person for whom performance appraisal is being conducted'
    )

    appraiser = models.ForeignKey(
        User,
        related_name='as_appraisers',
        on_delete=models.CASCADE,
        help_text='Person who gives review for appraisee'
    )

    appraisal_type = models.CharField(
        max_length=25,
        choices=APPRAISAL_TYPE,
        default=SELF_APPRAISAL,
        db_index=True
    )
    question_set = JSONField(null=True)
    # answer = JSONField(null=True)
    remarks = models.CharField(
        max_length=225,
        blank=True,
        null=True
    )

    resend = models.ForeignKey(ResendPAForm,
                               on_delete=models.CASCADE,
                               related_name='resend',
                               null=True,
                               blank=True)

    final_score = models.FloatField(
        default=0,
        validators=[MinMaxValueValidator(0, 100)])
    total_score = models.PositiveIntegerField(
        default=0,
        validators=[MinMaxValueValidator(0, 100)]
    )
    score_deduction_factor = models.FloatField(
        default=0,
        validators=[MinMaxValueValidator(0, 100)]
    )

    answer_committed = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    committed_at = models.DateTimeField(null=True)

    start_date = models.DateTimeField(null=True)
    deadline = models.DateTimeField(null=True)

    approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True)

    def __str__(self):
        return " : ".join(
            map(
                lambda attr: str(getattr(self, attr)),
                ['appraisal_type', 'appraisee', 'appraiser']
            )
        )
