from django.contrib.auth import get_user_model
from django.db import models
from irhrs.common.models import BaseModel
from irhrs.core.constants.organization import EMAIL_TYPE_CHOICES

USER = get_user_model()


class UserEmailUnsubscribe(BaseModel):
    """
    Model to store email types which email has unsubscribed to
    """
    user = models.ForeignKey(USER, on_delete=models.CASCADE, related_name='unsubscribed_emails')
    email_type = models.PositiveIntegerField(choices=EMAIL_TYPE_CHOICES)

    class Meta:
        unique_together = ('user', 'email_type')
