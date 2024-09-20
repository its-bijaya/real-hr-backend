"""@irhrs_docs"""
from django.contrib.contenttypes.models import ContentType

from irhrs.core.constants.noticeboard import (HR_NOTICE, DIVISION_NOTICE,
                                              ORGANIZATION_NOTICE, NORMAL_POST)
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import get_possessive_determiner
from irhrs.event.models import Event
from irhrs.noticeboard.utils.post_notification import get_post_frontend_url
from irhrs.notification.utils import add_notification


def create_post_comment_notification(comment):
    post = comment.post
    recipient = post.posted_by
    actor = comment.commented_by
    content_type = ContentType.objects.get_for_model(Event)
    event = None
    if post.content_type == content_type:
        event = post.content_object
        url = get_event_post_frontend_url(post)
    else:
        url = get_post_frontend_url(post)

    if not recipient == get_system_admin():

        if post.category == NORMAL_POST:
            post_type = 'post'
        else:
            post_type = post.category
        text = f"{actor.full_name} commented on your {post_type}" + \
               (f' of the event `{event.title}`.' if event else '.')

        add_notification(text=text, actor=actor, action=comment,
                         recipient=recipient, url=url)

    # handle user tags, if post has tags send notifications to
    # tagged users also
    text = f"{actor.full_name} commented on a post you are tagged in."
    u = post.user_tags.all()
    add_notification(
        text=text,
        actor=actor,
        action=comment,
        recipient=u,
        url=url
    )


def create_comment_reply_notification(comment_reply):
    comment = comment_reply.comment
    post = comment.post
    event = None
    content_type = ContentType.objects.get_for_model(Event)
    if post.content_type == content_type:
        url = get_event_post_frontend_url(post)
        event = post.content_object
    else:
        url = get_post_frontend_url(post)
    actor = comment_reply.reply_by

    recipients = {post.posted_by, comment.commented_by} - {actor}

    def get_notification_text(recipient):
        if post.category in [
            HR_NOTICE,
            DIVISION_NOTICE,
            ORGANIZATION_NOTICE
        ]:
            posted_by_name = f"{post.get_category_display()}'s"
        elif post.posted_by in {actor, recipient}:
            posted_by_name = get_possessive_determiner(recipient,
                                                       post.posted_by)
        else:
            posted_by_name = f"{post.posted_by.full_name}'s"

        if comment.commented_by in {actor, recipient}:
            commented_by_name = get_possessive_determiner(recipient,
                                                          comment.commented_by)
        else:
            commented_by_name = f"{comment.commented_by.full_name}'s"
        return f"{actor.full_name} replied to {commented_by_name} comment on " \
               f"{posted_by_name} post" + (f' of the event `{event.title}`.' if event else '.')

    notifications = [(get_notification_text(recipient), recipient) for recipient in recipients]

    for text, recipient in notifications:
        add_notification(text=text, actor=actor, action=comment_reply,
                         recipient=recipient, url=url)


def get_event_post_frontend_url(post):
    return f"/user/events/{post.object_id}/posts/{post.id}"
