from django.core.cache import cache
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenBackendError

USER = get_user_model()


def jwt_decode(token):
    obj = TokenBackend(api_settings.ALGORITHM, api_settings.SIGNING_KEY, api_settings.VERIFYING_KEY)
    return obj.decode(token)


@database_sync_to_async
def get_user_or_none(token):
    """
    Tries to fetch a room for the user, checking permissions along the way.
    """
    # Check if the user is logged in
    try:
        payload = jwt_decode(token)
        user_id = str(payload.get('user_id'))
        user_group = cache.get(
            f'group_for_user_id_{user_id}'
        )
        if not user_group:
            user = USER.objects.get(
                id=user_id
            )
            cache.set(
                f'group_for_user_id_{user_id}',
                list(user.groups.values_list('id', flat=True))
            )
        return str(user_id)
    except (TokenBackendError, USER.DoesNotExist):
        return None


@database_sync_to_async
def update_user(user_id, data):
    _ = USER.objects.filter(id=user_id).update(**data)
