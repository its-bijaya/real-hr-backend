from django.db import models
from irhrs.common.models import BaseModel
from irhrs.noticeboard.models import Post
from django.contrib.auth import get_user_model

User = get_user_model()


class HRNoticeAcknowledgement(BaseModel):
    post = models.ForeignKey(
        Post, related_name='acknowledgements', on_delete=models.CASCADE)
    acknowledged_by = models.ForeignKey(
        User, related_name='acknowledged_posts', on_delete=models.CASCADE)
    acknowledged = models.BooleanField(default=True)

    def __str__(self):
        acknowledge_action = 'acknowledged' if self.acknowledged else 'unacknowledged'
        return f"{self.acknowledged_by} {acknowledge_action} notice - {self.post}"
