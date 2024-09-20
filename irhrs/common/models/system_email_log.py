from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.constants.common import NOTIFICATION_STATUS_CHOICES

USER = get_user_model()


class SystemEmailLog(BaseModel):
    user = models.ForeignKey(
        to=USER, on_delete=models.CASCADE,
        related_name='notification_logs'
    )
    subject = models.CharField(max_length=150)
    status = models.CharField(
        max_length=20,
        choices=NOTIFICATION_STATUS_CHOICES,
        db_index=True
    )
    sent_address = models.EmailField(max_length=150)
    text_message = models.TextField()
    html_message = models.TextField()

    def __str__(self):
        return f"{self.created_at} -> {self.subject}"
