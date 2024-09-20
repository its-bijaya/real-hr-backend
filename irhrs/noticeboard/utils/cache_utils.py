import json

from dateutil.parser import parse
from django.core.cache import cache
from django.db.models import Case, When, F
from django.utils import timezone

from irhrs.core.utils.common import DummyObject, get_complete_url
from irhrs.noticeboard.api.v1.serializers.post import PostCacheSerializer
from irhrs.noticeboard.models import Post
from irhrs.noticeboard.utils.queryset_utils import prefetch_queryset_of_post_for_noticeboard


def _filter_visible_until(post):
    visible_until = post.get('visible_until')

    # if visible until is None, always visible
    if visible_until is None:
        return True

    visible_until = parse(visible_until)

    return visible_until >= timezone.now().astimezone()


def get_noticeboard_cache(as_user=None):
    """
    Get cached posts for `as_user`

    Here `as_user` is required to show liked status of user in a post

    :param as_user:
    :type as_user: User
    :return: Noticeboard cache
    """
    cached_data = cache.get('noticeboard_posts', None)
    if cached_data is None:
        set_noticeboard_cache()
        cached_data = cache.get('noticeboard_posts', [])

    visible_posts = list(filter(_filter_visible_until, cached_data))
    if len(visible_posts) < len(cached_data):
        set_noticeboard_cache()
        return get_noticeboard_cache(as_user)

    count = cache.get('posts_count', 0)
    for post_data in visible_posts:

        # liked info by as_user
        likes = post_data.get('likes', {'data': [], 'count': 0, 'me': False})
        if as_user and as_user.id in [like['liked_by']['id'] for like in likes['data']]:
            likes['me'] = True

        # Attach only first four in comment
        likes['data'] = likes['data'][:4]

        # comment like info by as_user
        comments = post_data.get('comments', {'data': [], 'count': True})
        for comment in comments['data']:
            comment_likes = comment.get('likes', {'data': [], 'count': 0})
            if as_user and as_user.id in [
                like['liked_by']['id'] for like in comment_likes['data']
            ]:
                comment['liked_by_user'] = True

    return visible_posts, count


def set_noticeboard_cache():
    """
    Cache recent five posts on cache
    """
    now = timezone.now().astimezone()

    queryset = prefetch_queryset_of_post_for_noticeboard(
        Post.objects.exclude(object_id__isnull=False)
    ).exclude(visible_until__lt=now).annotate(
        posted_on=Case(
            When(
                scheduled_for__isnull=False,
                then=F('scheduled_for')
            ),
            default=F('created_at')
        )
    ).filter(
        posted_on__lte=now
    ).order_by(
        F('pinned').desc(nulls_last=True),
        F('pinned_on').desc(nulls_last=True),
        '-posted_on'
    )

    cache.set("posts_count", queryset.count())
    serializer_context = {
        # Dummy request object as we will not have request but
        # serializer requires it
        'request': DummyObject(
            method='GET',
            user=None,
            is_authenticated=False,
            build_absolute_uri=get_complete_url  # patch get_absolute_uri
        )
    }

    cache_data = json.loads(json.dumps(PostCacheSerializer(
        queryset[:5],
        context=serializer_context,
        many=True
    ).data))
    cache.set('noticeboard_posts', cache_data)

