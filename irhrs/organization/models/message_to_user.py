from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import SlugModel, BaseModel
from irhrs.core.validators import validate_title

USER = get_user_model()


class MessageToUser(BaseModel, SlugModel):
    """
    Model to hold the information on the organizational messages for the users.

    Message could be anything by any user from motivational text to organization
    message and so on.

    # Field Definitions:
    created_by -> Logged In User
    title  -> Title of the message.
    message -> Message Text
    message_from -> The message of HR/HOD/CEO/ChairPerson/...
    published -> visible to users
    archived -> is message active
    """
    title = models.CharField(
        max_length=255,
        validators=[validate_title]
    )
    message = models.TextField(
        help_text="Message to display for the users."
    )
    message_from = models.ForeignKey(
        to=USER,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    published = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return f"{self.title}"
