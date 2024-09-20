from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.validators import validate_title


class IdCardSample(BaseModel):
    """
    Id Card Sample
    ==============
    """
    name = models.CharField(max_length=150, unique=True, validators=[validate_title])
    content = models.TextField(max_length=1000000)

    def __str__(self):
        return self.name
