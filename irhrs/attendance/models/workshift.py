from django.db import models
from django.utils.functional import cached_property

from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.utils.common import get_today
from ..managers.workshift import WorkDayManager
from ..constants import WEEK_DAYS_CHOICES
from ...core.validators import validate_title, validate_is_hex_color


class WorkShift(BaseModel, SlugModel):
    organization = models.ForeignKey(to='organization.Organization',
                                     null=True, on_delete=models.CASCADE,
                                     related_name='work_shifts')
    name = models.CharField(max_length=150)
    start_time_grace = models.DurationField()
    end_time_grace = models.DurationField()
    is_default = models.BooleanField(
        default=False, help_text='Defines a Default shift for an organization'
    )
    description = models.TextField(blank=True, max_length=600)

    class Meta:
        unique_together = (
            'organization', 'name'
        )

    def __str__(self):
        return f"{self.name}"

    @property
    def half_day(self):
        return ''

    @cached_property
    def days(self):
        return self.work_days.all()


class WorkDay(BaseModel):
    shift = models.ForeignKey(WorkShift, on_delete=models.CASCADE,
                              related_name='work_days')
    day = models.PositiveSmallIntegerField(choices=WEEK_DAYS_CHOICES)

    applicable_from = models.DateField(default=get_today)
    applicable_to = models.DateField(null=True, blank=True)

    objects = WorkDayManager()

    def __str__(self):
        return f"{self.shift}-day-{self.day}"

    @cached_property
    def work_times(self):
        return self.timings.all()


class WorkTiming(BaseModel):
    work_day = models.ForeignKey(
        to=WorkDay,
        on_delete=models.CASCADE,
        related_name='timings'
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    extends = models.BooleanField(default=False)

    working_minutes = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('work_day', 'start_time', 'end_time')
        ordering = ('created_at',)

    def __str__(self):
        return f"{self.work_day} {self.start_time} - {self.end_time}"

    @property
    def display(self):
        return "%s - %s" % (self.start_time, self.end_time)


class WorkShiftLegend(BaseModel):
    shift = models.OneToOneField(WorkShift, on_delete=models.CASCADE,
                                 related_name='work_shift_legend')
    legend_text = models.CharField(max_length=3, validators=[validate_title])
    legend_color = models.CharField(max_length=9, validators=[validate_is_hex_color])

    def __str__(self):
        return f"{self.shift}-legend-{self.legend_text}"
