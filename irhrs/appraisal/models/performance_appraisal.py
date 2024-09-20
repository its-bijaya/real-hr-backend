from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from irhrs.appraisal.constants import APPRAISAL_TYPE, SELF_APPRAISAL, \
    QUESTION_SET_STATUS, NOT_GENERATED, SUB_PERFORMANCE_APPRAISAL_TYPE, \
    THREE_SIXTY_PERFORMANCE_APPRAISAL, RATING_SCALE, DEFAULT
from irhrs.appraisal.constants import IDLE, COMPLETED, ACTIVE
from irhrs.common.models import BaseModel, SlugModel
from irhrs.organization.models import FiscalYear, Organization
from irhrs.core.utils.common import get_today

User = get_user_model()


class PerformanceAppraisalYear(BaseModel, SlugModel):
    name = models.CharField(max_length=125)
    year = models.ForeignKey(
        FiscalYear, null=True,
        on_delete=models.SET_NULL,
        related_name='performance_appraisal_years',
    )
    organization = models.ForeignKey(
        Organization,
        related_name='performance_appraisal_years',
        on_delete=models.CASCADE,
        null=True
    )
    performance_appraisal_type = models.CharField(
        max_length=40,
        choices=SUB_PERFORMANCE_APPRAISAL_TYPE,
        default=THREE_SIXTY_PERFORMANCE_APPRAISAL
    )

    class Meta:
        unique_together = (('name', 'organization'), ('year', 'organization'))

    def __str__(self):
        return self.name


class SubPerformanceAppraisalSlot(BaseModel):
    title = models.CharField(max_length=125)
    weightage = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    from_date = models.DateField()
    to_date = models.DateField()
    performance_appraisal_year = models.ForeignKey(
        PerformanceAppraisalYear,
        related_name='slots',
        on_delete=models.CASCADE
    )
    question_set_status = models.CharField(
        max_length=14,
        choices=QUESTION_SET_STATUS,
        default=NOT_GENERATED,
        db_index=True
    )

    def __str__(self):
        return f'{self.title} for {self.performance_appraisal_year.name}'

    class Meta:
        ordering = 'from_date',

    @property
    def status(self):
        today = get_today()
        if self.from_date <= today <= self.to_date:
            return ACTIVE
        if self.to_date < today:
            return COMPLETED
        return IDLE


class SubPerformanceAppraisalSlotMode(BaseModel):
    """
    Defining appraisal_types(modes) used by particular appraisal
    session.

    Note: combination of weightage supported by particular appraisal
    session should be equal to 100.
    """
    appraisal_type = models.CharField(
        max_length=125,
        choices=APPRAISAL_TYPE,
        default=SELF_APPRAISAL,
        db_index=True
    )
    weightage = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,
        related_name='modes',
        on_delete=models.CASCADE
    )
    start_date = models.DateTimeField(null=True)
    deadline = models.DateTimeField(null=True)

    class Meta:
        unique_together = ('sub_performance_appraisal_slot', 'appraisal_type')
        ordering = 'created_at',

    def __str__(self):
        return f'{self.appraisal_type} with weightage {self.weightage} ' \
               f'for {self.sub_performance_appraisal_slot.title}'


class SubPerformanceAppraisalSlotWeight(BaseModel):
    appraiser = models.ForeignKey(
        User,
        related_name='sub_performance_appraisal_slot_weights',
        on_delete=models.CASCADE
    )
    sub_performance_appraisal_slot = models.ForeignKey(
        SubPerformanceAppraisalSlot,
        related_name='weight',
        on_delete=models.CASCADE
    )
    percentage = models.FloatField(validators=[MinValueValidator(0)], default=0)

    class Meta:
        unique_together = ('appraiser', 'sub_performance_appraisal_slot')

    def __str__(self):
        return f"{self.appraiser} -> {self.sub_performance_appraisal_slot} -> ({self.percentage}%)"


class SubPerformanceAppraisalYearWeight(BaseModel):
    appraiser = models.ForeignKey(
        User,
        related_name='sub_performance_appraisal_year_weights',
        on_delete=models.CASCADE
    )
    performance_appraisal_year = models.ForeignKey(
        PerformanceAppraisalYear,
        related_name='sub_performance_appraisal_year_weights',
        on_delete=models.CASCADE
    )
    percentage = models.FloatField(validators=[MinValueValidator(0)], default=0)

    class Meta:
        unique_together = ('appraiser', 'performance_appraisal_year')

    def __str__(self):
        return f"{self.appraiser} -> {self.performance_appraisal_year} -> ({self.percentage}%)"

