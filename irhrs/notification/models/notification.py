from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields.array import ArrayField
from django.db import models
from django.utils import timezone

from irhrs.common.models import BaseModel
from irhrs.core.constants.common import INFO, INTERACTIVE_NOTIFICATION_CHOICES, NOTIFICATION_LABEL_CHOICES
from irhrs.core.fields import JSONTextField
from irhrs.organization.models import Organization
from irhrs.permission.models import HRSPermission

USER = get_user_model()


class InteractiveNotification(models.Model):
    is_interactive = models.BooleanField(default=False)
    interactive_type = models.CharField(max_length=50, choices=INTERACTIVE_NOTIFICATION_CHOICES,
                                        null=True, db_index=True)
    interactive_data = JSONTextField(null=True)

    class Meta:
        abstract = True


class Notification(InteractiveNotification, BaseModel):
    """
    Notification Model

    actor : one who sends/creates notification
    text : notification text
    action : action object < where notification will redirect >
    recipient : one who receives notification
    notify_on : Time when notification will be sent to the user
    sticky : Pin/Unpin Notification
    can_be_reminded : Notification can be reminded or not
    """
    actor = models.ForeignKey(
        USER, related_name='sent_notifications',
        null=True, on_delete=models.SET_NULL)

    text = models.TextField(blank=True)

    action_content_type = models.ForeignKey(
        ContentType,
        related_name='action_notifications',
        on_delete=models.CASCADE)
    action_object_id = models.PositiveIntegerField()
    action = GenericForeignKey('action_content_type', 'action_object_id')

    recipient = models.ForeignKey(USER,
                                  related_name='my_notifications',
                                  on_delete=models.CASCADE)
    url = models.TextField(null=True, blank=True)

    label = models.CharField(choices=NOTIFICATION_LABEL_CHOICES,
                             max_length=20, default=INFO,
                             db_index=True)
    read = models.BooleanField(default=False)
    notify_on = models.DateTimeField(default=timezone.now)
    sticky = models.BooleanField(default=False)
    can_be_reminded = models.BooleanField(default=False)

    class Meta:
        ordering = ('-notify_on',)

    def __str__(self):
        return self.text


class OrganizationNotification(InteractiveNotification, BaseModel):
    """
    Modification of Notification model.
    * Send the notification to a group, instead of an user.
    * For now, the group HR only gets the notification.
    """
    actor = models.ForeignKey(
        USER, related_name='sent_group_notifications',
        null=True, on_delete=models.SET_NULL
    )

    text = models.TextField(blank=True)
    url = models.TextField(blank=True)

    action_content_type = models.ForeignKey(
        ContentType,
        related_name='action_group_notifications',
        on_delete=models.CASCADE
    )
    action_object_id = models.PositiveIntegerField()
    action = GenericForeignKey(
        'action_content_type', 'action_object_id'
    )

    recipient = models.ForeignKey(
        Organization,
        related_name='notifications',
        on_delete=models.CASCADE
    )

    label = models.CharField(
        choices=NOTIFICATION_LABEL_CHOICES,
        max_length=20, default=INFO,
        db_index=True
    )
    is_resolved = models.BooleanField(default=False)

    notify_on = models.DateTimeField(default=timezone.now)
    associated_permissions = ArrayField(
        base_field=models.FloatField(),
        null=True
    )

    class Meta:
        ordering = ('-notify_on',)

    def __str__(self):
        return self.text
