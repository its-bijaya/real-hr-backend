from django.db import models
from irhrs.common.models import SlugModel, BaseModel
from irhrs.core.validators import validate_title


class Skill(BaseModel, SlugModel):
    name = models.CharField(max_length=150, unique=True,
                            validators=[validate_title])
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return f"Skill -  {self.name}"
