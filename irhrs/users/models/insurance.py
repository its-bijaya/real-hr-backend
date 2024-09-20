from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.utils.common import get_upload_path
from irhrs.users.constants import POLICY_TYPE_OPTIONS, HEALTH_INSURANCE
from irhrs.users.models import UserContactDetail

User = get_user_model()


class UserInsurance(BaseModel):
    user = models.ForeignKey(
        User,
        related_name='insurances',
        on_delete=models.CASCADE
    )
    dependent = models.ManyToManyField(
        UserContactDetail,
        related_name='insurances'
    )

    insured_scheme = models.CharField(blank=True, max_length=255)
    insured_amount = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )
    annual_premium = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )

    policy_name = models.CharField(max_length=225)
    policy_provider = models.CharField(max_length=225)
    policy_type = models.CharField(
        max_length=20,
        choices=POLICY_TYPE_OPTIONS,
        default=HEALTH_INSURANCE,
        db_index=True
    )
    start_date = models.DateField()
    end_date = models.DateField()
    attachment = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
        )],
        blank=True, null=True
    )

    def __str__(self):
        return self.policy_name
