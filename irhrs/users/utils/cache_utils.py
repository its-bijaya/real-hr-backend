import json

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django_q.tasks import async_task

from irhrs.core.utils.subordinates import set_subordinate_cache, \
    set_immediate_subordinates_and_supervisor_cache, set_subordinate_according_to_organization
from irhrs.users.api.v1.serializers.thin_serializers import AuthUserThinSerializer

USER = get_user_model()


def get_user_autocomplete_cache():
    cached_data = cache.get('user_autocomplete', None)
    if cached_data is None:
        set_user_autocomplete_cache()
        cached_data = cache.get('user_autocomplete', [])
    return cached_data


def set_user_autocomplete_cache():
    """
    Set user autocomplete in cache
    """
    user_filter = {
        'is_blocked': False,
        'is_active': True,
    }
    queryset = USER.objects.filter(detail__isnull=False, **user_filter).select_related(
        'detail', 'detail__organization', 'detail__job_title',
        'detail__division', 'detail__employment_level'
    ).order_by('first_name', 'middle_name', 'last_name')

    cache_data = json.loads(json.dumps(AuthUserThinSerializer(
        queryset,
        many=True
    ).data))

    cache.set('user_autocomplete', cache_data)


def recalibrate_supervisor_subordinate_relation():
    async_task(set_subordinate_cache)
    async_task(set_immediate_subordinates_and_supervisor_cache)
    async_task(set_subordinate_according_to_organization)
