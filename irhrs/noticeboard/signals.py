from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django_q.models import Schedule

from irhrs.core.constants.common import NOTICEBOARD
from irhrs.core.constants.noticeboard import HR_NOTICE, DIVISION_NOTICE, \
    ORGANIZATION_NOTICE
from irhrs.core.utils.user_activity import create_user_activity
from irhrs.event.models import Event
from irhrs.noticeboard.models import (
    Post, PostComment, PostLike, CommentReply, CommentLike,
    PostAttachment)
from irhrs.noticeboard.utils.cache_utils import set_noticeboard_cache
from irhrs.noticeboard.utils.comment import create_post_comment_notification, \
    create_comment_reply_notification
from irhrs.noticeboard.utils.event_posts_notification import \
    create_event_post_notification
from irhrs.notification.models import Notification


def find_posted_by(instance):
    post = instance.post
    if post.category in [
        HR_NOTICE,
        DIVISION_NOTICE,
        ORGANIZATION_NOTICE,
    ]:
        return post.get_category_display()
    return post.posted_by


@receiver(post_save, sender=Post)
@receiver(post_save, sender=PostComment)
@receiver(post_save, sender=PostLike)
@receiver(post_save, sender=CommentReply)
@receiver(post_save, sender=CommentLike)
def create_activity_on_noticeboard(sender, instance, created, **kwargs):
    activity = {}
    if sender == Post:
        activity = {
            'actor': instance.posted_by,
            'message_string': f'{"created" if created else "updated"} a post.'
        }
    elif sender == PostComment:
        activity = {
            'actor': instance.commented_by,
            'message_string': f'commented on '
            f'{find_posted_by(instance)}\'s post.'
        }
    elif sender == PostLike:
        message_by = find_posted_by(instance)
        activity = {
            'actor': instance.liked_by,
            'message_string': f"{'liked' if instance.liked else 'unliked'} "
            f'{message_by}\'s post.'
        }
    elif sender == CommentReply:
        activity = {
            'actor': instance.reply_by,
            'message_string': f'replied on '
            f'{instance.comment.commented_by}\'s comment on '
            f'{find_posted_by(instance.comment)}\'s post.'
        }
    elif sender == CommentLike:
        activity = {
            'actor': instance.liked_by,
            'message_string': f"{'liked' if instance.liked else 'unliked'} "
            f"{instance.comment.commented_by} comment on "
            f'{find_posted_by(instance.comment)}\'s post.'
        }
    create_user_activity(
        category=NOTICEBOARD,
        **activity
    )
    # set_noticeboard_cache()


@receiver(post_save, sender=Post)
def schedule_noticeboard_cache_update(sender, instance, created, **kwargs):
    if instance.scheduled_for:
        Schedule.objects.create(
            func='irhrs.noticeboard.utils.cache_utils.set_noticeboard_cache',
            next_run=instance.scheduled_for,
            name="Schedule Post update cache"
        )


@receiver(pre_delete, sender=Post)
@receiver(pre_delete, sender=PostComment)
@receiver(pre_delete, sender=CommentReply)
def delete_notifications(sender, instance, **kwargs):
    ctype = ContentType.objects.get_for_model(sender)
    object_id = instance.id
    Notification.objects.filter(action_content_type=ctype,
                                action_object_id=object_id).delete()


@receiver(post_save, sender=PostAttachment)
@receiver(post_delete, sender=PostAttachment)
@receiver(post_delete, sender=Post)
@receiver(post_delete, sender=PostComment)
@receiver(post_delete, sender=CommentReply)
def set_post_cache(sender, instance, **kwargs):
    # set_noticeboard_cache()
    pass

@receiver(post_save, sender=PostComment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        create_post_comment_notification(instance)


@receiver(post_save, sender=CommentReply)
def create_comment_reply_notification_(sender, instance, created, **kwargs):
    if created:
        create_comment_reply_notification(instance)


@receiver(post_save, sender=Post)
def event_post_notification(sender, instance, created, **kwargs):
    if created and instance.content_type == ContentType.objects.get_for_model(Event):
        create_event_post_notification(instance, instance.created_by)
