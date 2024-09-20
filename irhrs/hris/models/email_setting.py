from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import BaseModel

User = get_user_model()


class EmailSetting(BaseModel):
    user = models.ForeignKey(User, related_name='email_setting', on_delete=models.CASCADE)
    leave = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.full_name}'
