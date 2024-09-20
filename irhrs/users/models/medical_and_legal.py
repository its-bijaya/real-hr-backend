from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import BaseModel, SlugModel, Disability
from irhrs.core.constants.user import (
    BLOOD_GROUP_CHOICES, WEIGHT_UNIT_CHOICES,
    HEIGHT_UNIT_CHOICES)
from irhrs.core.validators import validate_has_digit, validate_invalid_chars, \
    validate_title, validate_past_date_or_today

USER = get_user_model()


class ChronicDisease(BaseModel, SlugModel):
    user = models.ForeignKey(to=USER,
                             on_delete=models.CASCADE, editable=False)
    title = models.CharField(max_length=150,
                             validators=[validate_title])
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Chronic Disease {self.title} of {self.user}"


class RestrictedMedicine(BaseModel, SlugModel):
    user = models.ForeignKey(
        USER,
        on_delete=models.CASCADE,
        editable=False
    )
    title = models.CharField(max_length=225)
    description = models.TextField(blank=True, max_length=settings.TEXT_FIELD_MAX_LENGTH)

    def __str__(self):
        return self.title


class AllergicHistory(BaseModel, SlugModel):
    user = models.ForeignKey(
        USER,
        on_delete=models.CASCADE,
        editable=False
    )
    title = models.CharField(max_length=225)
    description = models.TextField(blank=True, max_length=settings.TEXT_FIELD_MAX_LENGTH)

    def __str__(self):
        return self.title


class UserMedicalInfo(BaseModel):
    user = models.OneToOneField(to=USER,
                                on_delete=models.CASCADE,
                                related_name='medical_info',
                                editable=False)
    blood_group = models.CharField(max_length=10,
                                   choices=BLOOD_GROUP_CHOICES)
    height = models.CharField(max_length=10)
    weight = models.FloatField()
    height_unit = models.CharField(max_length=10, choices=HEIGHT_UNIT_CHOICES)
    weight_unit = models.CharField(max_length=10, choices=WEIGHT_UNIT_CHOICES)
    smoker = models.BooleanField(default=False)
    drinker = models.BooleanField(default=False)
    on_medication = models.BooleanField(default=False)
    disabilities = models.ManyToManyField(to=Disability, blank=True)

    def __str__(self):
        return f"Medical Info - {self.user}"

    @property
    def get_height(self):
        return f"{self.height} {self.height_unit}"

    @property
    def get_weight(self):
        return f"{self.weight} {self.weight_unit}"


class UserLegalInfo(BaseModel):
    user = models.OneToOneField(to=USER,
                                on_delete=models.CASCADE,
                                related_name='legal_info',
                                editable=False)
    pan_number = models.CharField(max_length=50,
                                  validators=[validate_invalid_chars,
                                              validate_has_digit])
    cit_number = models.CharField(max_length=50, blank=True,
                                  validators=[validate_invalid_chars,
                                              validate_has_digit])
    pf_number = models.CharField(max_length=50, blank=True,
                                 validators=[validate_invalid_chars,
                                             validate_has_digit])
    citizenship_number = models.CharField(max_length=50,
                                          validators=[validate_invalid_chars,
                                                      validate_has_digit])
    citizenship_issue_place = models.CharField(
        max_length=255,
        blank=True
    )
    citizenship_issue_date = models.DateField(
        validators=[validate_past_date_or_today],
        null=True,
        blank=True
    )
    ssfid = models.CharField(
        max_length=50,
        validators=[validate_invalid_chars,
                    validate_has_digit],
        help_text="Social Security Fund ID",
        blank=True
    )
    passport_number = models.CharField(
        max_length=50, blank=True,
        validators=[validate_invalid_chars, validate_has_digit])

    passport_issue_place = models.CharField(
        max_length=255,
        blank=True
    )
    passport_issue_date = models.DateField(
        validators=[validate_past_date_or_today],
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('user', 'citizenship_number',)

    def __str__(self):
        return f"Legal Info of {self.user}"
