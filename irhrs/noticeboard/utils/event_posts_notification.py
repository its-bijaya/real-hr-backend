"""@irhrs_docs"""
from irhrs.noticeboard.models import User
from irhrs.notification.utils import add_notification


def create_event_post_notification(post, user):
    """
    create notification for post generated for interactive events.

    Notification is sent to every members of
    event if post is created by event organizer.

    Else  notification is sent to event organizer
    if post is created my event members.

    :param post: instance of post
    :param user:
    :return:
    """
    event = post.content_object
    url = get_event_frontend_url(event)
    actor = post.created_by
    text = f"{actor.full_name} added a post on the event `{event.title}`."

    if post.content_object.created_by == user:
        recipient = User.objects.filter(eventmembers__event=post.content_object)
        add_notification(text=text, actor=actor, action=post,
                         recipient=recipient, url=url)
    elif post.content_object.event_members.filter(
            user=user).exists():
        recipient = post.content_object.created_by
        add_notification(text=text, actor=actor, action=post,
                         recipient=recipient, url=url)


def get_event_frontend_url(event):
    return f"/user/events/{event.id}"
