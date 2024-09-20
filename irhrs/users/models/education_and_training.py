from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import SlugModel, BaseModel

from irhrs.core.validators import (validate_past_date, validate_title)
from irhrs.core.constants.user import EDUCATION_DEGREE_CHOICES, MARKS_TYPE

USER = get_user_model()


class UserEducation(BaseModel):
    user = models.ForeignKey(USER,
                             related_name='user_education',
                             on_delete=models.CASCADE,
                             editable=False)
    degree = models.CharField(max_length=20, choices=EDUCATION_DEGREE_CHOICES)
    field = models.CharField(max_length=150, validators=[validate_title])
    institution = models.CharField(max_length=150, validators=[validate_title])
    university = models.CharField(max_length=150, validators=[validate_title])
    marks_type = models.CharField(max_length=10, choices=MARKS_TYPE, blank=True)
    marks = models.FloatField(null=True)
    from_year = models.DateField(validators=[validate_past_date])
    to_year = models.DateField(null=True, validators=[validate_past_date])
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.degree} Record of {self.user}'

    @property
    def total_years_spent(self):
        if not self.is_current and self.to_year:
            return self.to_year - self.from_year
        return None


class UserTraining(BaseModel, SlugModel):
    user = models.ForeignKey(USER,
                                   related_name='trainings',
                                   on_delete=models.CASCADE,
                                   editable=False)
    name = models.CharField(max_length=100, validators=[validate_title])
    institution = models.CharField(max_length=100, validators=[validate_title])
    is_current = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField(null=True)

    def __str__(self):
        return "Training - {}".format(self.name)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'user')
