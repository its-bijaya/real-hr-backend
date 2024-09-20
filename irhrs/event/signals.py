from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from irhrs.core.constants.organization import EVENT_CANCELED_DELETED_EMAIL
from irhrs.core.utils import email
from irhrs.event.models import Event
from irhrs.noticeboard.models import Post
from irhrs.notification.models import Notification


@receiver(pre_delete, sender=Event)
def send_event_cancellation_email(sender, instance, **kwargs):
    recipients = []
    for member in instance.event_members.all():
        if email.can_send_email(member.user, EVENT_CANCELED_DELETED_EMAIL):
            recipients.append(member.user.email)

    if recipients:
        subject = f"Event Cancellation"
        message = f"Event {instance.title} has been cancelled."
        email.send_notification_email(
            recipients=recipients,
            subject=subject,
            notification_text=message
        )


@receiver(post_delete, sender=Event)
def delete_event_notifications(sender, instance, **kwargs):
    # for deleting notifications associated with event
    ctype = ContentType.objects.get_for_model(Post)
    object_id = list(instance.event_posts.all().values_list('id', flat=True))
    Notification.objects.filter(action_content_type=ctype,
                                action_object_id__in=object_id).delete()

    # for deleting post associated with event
    ctype = ContentType.objects.get_for_model(sender)
    object_id = instance.id
    Post.objects.filter(content_type=ctype,
                        object_id=object_id).delete()

    # for deleting meeting room related to event
    if instance.room:
        instance.room.delete()
