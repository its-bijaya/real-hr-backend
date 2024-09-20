from django.db import models

from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.constants.common import NOTIFICATION_TYPE_CHOICES
from irhrs.core.validators import validate_title


class NotificationTemplate(BaseModel, SlugModel):
    name = models.CharField(max_length=150, validators=[validate_title], unique=True)
    type = models.CharField(
        max_length=40,
        choices=NOTIFICATION_TYPE_CHOICES,
        db_index=True
    )
    description = models.TextField(blank=True, max_length=600)

    def __str__(self):
        return f"Notification Template for {self.name} ({self.type})"


class NotificationTemplateContent(BaseModel):
    template = models.ForeignKey(NotificationTemplate, related_name='contents',
                                 on_delete=models.CASCADE)
    content = models.TextField(max_length=10000)
    # it is set to open char field because it may have random status
    status = models.CharField(max_length=32, default="Default",
                              db_index=True)

    def __str__(self):
        return f"{self.template} with status {self.status}"
