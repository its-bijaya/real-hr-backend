"""@irhrs_docs"""
from django.contrib.contenttypes.models import ContentType

from irhrs.core.constants.noticeboard import (HR_NOTICE, NORMAL_POST,
                                              DIVISION_NOTICE, ORGANIZATION_NOTICE)
from irhrs.core.constants.user import MALE, FEMALE
from irhrs.core.utils import get_system_admin
from irhrs.event.models import Event
from irhrs.noticeboard.utils.comment import get_event_post_frontend_url
from irhrs.noticeboard.utils.post_notification import get_post_frontend_url
from irhrs.notification.utils import add_notification, get_notifications


def create_post_like_notification(post_like, user):
    """Create notification for like"""

    # first check notification for the user
    post = post_like.post
    recipient = post.posted_by
    action = post_like
    event = post.content_object

    if recipient == get_system_admin():
        return

    notifications = get_notifications(action=action, actor=user)

    if post_like.liked and not notifications.exists():
        # if user has liked the post ant notification is not generated
        # for that post
        liked_text = "acknowledged" if post.category == HR_NOTICE else "liked"
        post_type = "Post" if post.category == NORMAL_POST else post.category
        text = f"{user.full_name} has {liked_text} your {post_type}" + \
               (f' of the event `{event.title}`.' if event else '.')

        content_type = ContentType.objects.get_for_model(Event)
        if post.content_type == content_type:
            url = get_event_post_frontend_url(post)
        else:
            url = get_post_frontend_url(post)
        add_notification(text=text, actor=user, action=action,
                         recipient=recipient, url=url)

    elif not post_like.liked:
        # delete liked notification if user unlike the post
        notifications.delete()


def create_comment_like_notification(comment_like):
    comment = comment_like.comment
    recipient = comment.commented_by
    actor = comment_like.liked_by
    action = comment_like
    event = comment.post.content_object

    notifications = get_notifications(action=action, actor=actor)

    if comment_like.liked and not notifications.exists():
        # if user has liked the post ant notification is not generated
        # for that post
        posted_by = comment.post.posted_by

        if comment.post.category in [
            HR_NOTICE,
            DIVISION_NOTICE,
            ORGANIZATION_NOTICE,
        ]:
            posted_by_name = f"{comment.post.category}'s"
        elif posted_by == recipient:
            posted_by_name = "your"
        elif posted_by == actor:
            if posted_by.detail.gender == MALE:
                posted_by_name = "his"
            elif posted_by.detail.gender == FEMALE:
                posted_by_name = "her"
            else:
                posted_by_name = "their"
        else:
            posted_by_name = f"{posted_by.full_name}'s"

        # import ipdb; ipdb.set_trace()
        text = f"{actor.full_name} has liked your comment on {posted_by_name} post" + \
               (f' of the event `{event.title}`.' if event else '.')

        post = comment.post
        content_type = ContentType.objects.get_for_model(Event)
        if post.content_type == content_type:
            url = get_event_post_frontend_url(post)
        else:
            url = get_post_frontend_url(post)
        add_notification(text=text, actor=actor, action=action,
                         recipient=recipient, url=url)

    elif not comment_like.liked:
        # delete liked notification if user unlike the post
        notifications.delete()
