from rest_framework.routers import DefaultRouter

from irhrs.noticeboard.api.v1.views.noticeboard_setting import NoticeBoardSettingViewSet
from .views.post import PostViewSet, PostLikeViewSet, PostCommentViewSet,\
    CommentLikeViewSet, CommentReplyViewSet

app_name = "noticeboard"

router = DefaultRouter()
router.register('posts', PostViewSet, basename='post')
router.register('post/like/(?P<post_id>\d+)', PostLikeViewSet,
                basename='post-like')
router.register('post/comment/(?P<post_id>\d+)', PostCommentViewSet,
                basename='post-comment')
router.register('post/comment/like/(?P<comment_id>\d+)', CommentLikeViewSet,
                basename='comment-like')
router.register('post/comment/reply/(?P<comment_id>\d+)', CommentReplyViewSet,
                basename='comment-reply')

router.register(r'noticeboard-setting',
                NoticeBoardSettingViewSet,
                basename='noticeboard-setting')

# router.register(r'posts/(?P<post_id>\d+)/comments',
#                 CommentViewSet, basename='comment')
# router.register('report', NoticeBoardReportViewSet, basename='report')
# router.register('postImage', PostAttachmentViewSet, basename='post-attachment')
urlpatterns = router.urls
