from django.db import models

from irhrs.common.models import SlugModel, BaseModel
from irhrs.core.validators import MinMaxValueValidator
from irhrs.core.validators import validate_invalid_chars, validate_title, \
    MinMaxValueValidator

class DutyStation(BaseModel, SlugModel):
    name = models.CharField(
        max_length=255,
        validators=[
            validate_title,
            validate_invalid_chars
        ],
        unique=True
    )
    description = models.TextField(blank=True, max_length=600)
    amount = models.FloatField()
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name