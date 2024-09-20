"""@irhrs_docs"""
from django.contrib.auth import get_user_model

from irhrs.common.models.user_activity import UserActivity
from irhrs.core.constants.common import USER_ACTIVITY_CATEGORIES_CHOICES

USER = get_user_model()


def create_user_activity(actor, message_string, category):
    assert isinstance(actor, USER),\
        "`actor` must be of `User` instance."
    assert len(message_string) <= 255, "`message_string` can be at most `255`" \
                                       " characters long."
    assert (category, category) in USER_ACTIVITY_CATEGORIES_CHOICES,\
        f"{category} is not a valid activity category."

    return UserActivity.objects.create(actor=actor,
                                       message=message_string,
                                       category=category)
