from django.db.models import Prefetch

from irhrs.noticeboard.models import CommentLike, PostLike, PostComment, CommentReply, \
    PostAttachment


def prefetch_queryset_of_post_for_noticeboard(queryset, user=None):

    comment_likes = CommentLike.objects.filter(liked=True).select_related(
        'liked_by', 'liked_by__detail',
        'liked_by__detail__job_title'
    )
    post_likes = PostLike.objects.filter(liked=True).select_related(
        'liked_by', 'liked_by__detail',
        'liked_by__detail__job_title'
    )
    comments = PostComment.objects.select_related(
        'commented_by', 'commented_by__detail',
        'commented_by__detail__job_title'
    ).prefetch_related(
        Prefetch(
            'replies',
            queryset=CommentReply.objects.select_related(
                'reply_by',
                'reply_by__detail',
                'reply_by__detail__job_title'
            )
        )
    )

    prefetches = [
        'organizations',
        'divisions',
        'user_tags',
        'user_tags__detail',
        'user_tags__detail__job_title',
        Prefetch('attachments',
                 queryset=PostAttachment.objects.all().order_by('created_at')),
        Prefetch('comments',
                 queryset=comments),
        Prefetch('likes',
                 queryset=post_likes),
        Prefetch('comments__likes',
                 queryset=comment_likes,
                 to_attr='liked_comments'),

    ]
    if user:
        prefetches.append(Prefetch(
            'comments__likes',
            queryset=comment_likes.filter(
                liked_by=user),
            to_attr='liked_by_user'
        ))

    return queryset.select_related(
        'posted_by', 'posted_by__detail',
        'posted_by__detail__job_title',
        'posted_by__detail__division',
        'posted_by__detail__employment_level',
        'posted_by__detail__organization',
    ).prefetch_related(*prefetches).all()
