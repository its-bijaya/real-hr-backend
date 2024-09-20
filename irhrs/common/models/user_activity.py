from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.constants.common import USER_ACTIVITY_CATEGORIES_CHOICES

USER = get_user_model()


class UserActivity(BaseModel):
    actor = models.ForeignKey(USER, on_delete=models.CASCADE,
                              related_name='activities')
    category = models.CharField(max_length=25,
                                choices=USER_ACTIVITY_CATEGORIES_CHOICES,
                                db_index=True)
    message = models.CharField(max_length=255)

    def __str__(self):
        return self.message
