from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from irhrs.core.constants.payroll import APPROVAL_STATUS_CHOICES, APPROVED_BY

USER = get_user_model()


class AbstractApprovals(models.Model):
    status = models.CharField(max_length=25, choices=APPROVAL_STATUS_CHOICES, db_index=True)
    role = models.CharField(max_length=25, choices=APPROVED_BY, db_index=True)
    level = models.IntegerField(
        validators=[MinValueValidator(limit_value=1)]
    )

    remarks = models.TextField(max_length=settings.TEXT_FIELD_MAX_LENGTH)

    class Meta:
        abstract = True


class AbstractHistory(models.Model):
    actor = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20)
    target = models.CharField(max_length=255, blank=True)  # extra description
    remarks = models.TextField(max_length=settings.TEXT_FIELD_MAX_LENGTH, blank=True)

    class Meta:
        abstract = True
