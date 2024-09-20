"""@irhrs_docs"""
from django.contrib.contenttypes.models import ContentType

from irhrs.core.constants.noticeboard import HR_NOTICE, DIVISION_NOTICE
from irhrs.event.models import Event
from irhrs.notification.utils import add_notification
from irhrs.organization.models import Organization
from irhrs.users.models import UserDetail


def create_post_notification(post, user):
    """
    create notification for hr and division notice
    """
    # TODO: @Shital remove this or use this.
    if post.category == HR_NOTICE:
        text = f"An HR notice has been published by {user.full_name}"
        organizations = Organization.objects.filter(
            users__user__detail=user)
        recipients = UserDetail.objects.filter(
            user__organization__organization__in=organizations
        ).exclude(id=user.id)
        add_notification(text=text, actor=user, recipient=recipients,
                         sticky=True, action=post)
    elif post.category == DIVISION_NOTICE:
        text = "A division notice has been published by" \
            f" {user.full_name}"
        division = user.division
        if not division:
            return

        recipients = UserDetail.objects.filter(
            user_experiences__is_current=True,
            user_experiences__division=division).exclude(id=user.id)
        add_notification(text=text, actor=user, recipient=recipients,
                         action=post)


def get_post_frontend_url(post):
    return f"/user/posts/{post.id}/"
