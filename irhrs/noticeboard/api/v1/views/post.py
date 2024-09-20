from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Prefetch, Count, Q, Subquery, F, Case, When
from django.utils import timezone
from rest_framework import filters, serializers
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework.fields import ReadOnlyField
from rest_framework.generics import get_object_or_404 as drf_get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.constants.noticeboard import NORMAL_POST, HR_NOTICE
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import GetStatisticsMixin
from irhrs.core.mixins.viewset_mixins import ListCreateViewSetMixin, \
    ListCreateUpdateDestroyViewSetMixin
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.event.models import Event
from irhrs.noticeboard.api.v1.permissions import PostPermission, \
    CommentPermission, CommentReplyPermission, LikePermission, \
    CommentLikePermission
from irhrs.noticeboard.constants import APPROVED, DENIED
from irhrs.noticeboard.utils.queryset_utils import prefetch_queryset_of_post_for_noticeboard
from irhrs.notification.utils import add_notification
from irhrs.permission.constants.permissions import NOTICE_BOARD_PERMISSION
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from ..serializers.post import PostSerializer, \
    PostLikeSerializer, PostCommentSerializer, CommentLikeSerializer, \
    CommentReplySerializer
from ....models import Post, PostLike, PostComment, CommentLike, CommentReply, NoticeBoardSetting, \
    HRNoticeAcknowledgement

USER = get_user_model()


class CustomNoticeboardPagination(LimitOffsetPagination):
    default_limit = 5


class PostViewSet(GetStatisticsMixin, ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    parser_classes = (MultiPartParser, FormParser,)
    pagination_class = CustomNoticeboardPagination
    permission_classes = [PostPermission]
    statistics_field = "status"
    filter_backends = [FilterMapBackend, filters.SearchFilter]
    filter_map = {'status': 'status'}
    search_fields = ['posted_by__first_name', 'posted_by__middle_name', 'posted_by__last_name']
    trending_post_serializer_class = type(
        "TrendingPostSerializer",
        (PostSerializer,),
        {
            "Meta": type("Meta", (object,), {
                "model": Post,
                "fields": (
                    "id", "created_at", "posted_by", "post_content",
                    "attachments", "likes_count", "comments_count",
                    "category"
                )
            }),
            "likes_count": ReadOnlyField(),
            "comments_count": ReadOnlyField()
        }
    )

    def filter_queryset(self, queryset):
        scheduled_post = self.request.query_params.get('scheduled')
        mode = self.request.query_params.get('as')

        normal_filter = Q()
        if mode == 'user':
            normal_filter = Q(scheduled_for__isnull=True) | Q(
                scheduled_for__lte=timezone.now())
        scheduled_filter = Q(scheduled_for__isnull=False) & Q(
            scheduled_for__gte=timezone.now())
        qs = super().filter_queryset(queryset).filter(
            scheduled_filter if scheduled_post else normal_filter
        )
        return qs.exclude(
            visible_until__lt=timezone.now()
        ).annotate(
            posted_on=Case(
                When(
                    scheduled_for__isnull=False,
                    then=F('scheduled_for')
                ),
                default=F('created_at')
            )
        ).order_by(
            F('pinned').desc(nulls_last=True),
            F('pinned_on').desc(nulls_last=True),
            '-created_at' if scheduled_post else '-posted_on'
        )

    def get_queryset(self):

        actions = ['my', 'retrieve', 'update', 'partial_update', 'destroy', 'status_change']
        if self.action in actions:
            if self.is_hr:
                queryset = Post.objects.all()
            else:
                queryset = Post.objects.filter(
                    Q(posted_by=self.request.user, category=NORMAL_POST) | Q(status=APPROVED))
        else:
            queryset = Post.objects.exclude(object_id__isnull=False)

        return prefetch_queryset_of_post_for_noticeboard(queryset, self.request.user)

    def get_serializer_class(self):
        if self.action == 'trending':
            return self.trending_post_serializer_class
        return super().get_serializer_class()

    def get_serializer(self, *args, **kwargs):
        is_hr = NOTICE_BOARD_PERMISSION.get(
            "code") in self.request.user.get_hrs_permissions()

        if self.request.method.upper() in ('PATCH', 'PUT'):
            post = self.get_post()
            ct_event = ContentType.objects.get_for_model(Event)

            if post and post.content_type == ct_event:
                event = post.content_object
                if not event.created_by == self.request.user:
                    kwargs.update({'exclude_fields': ['pinned']})
            else:
                if post and post.posted_by != self.request.user:
                    kwargs.update({'fields': ['pinned']})

                elif not is_hr:
                    kwargs.update({'exclude_fields': ['pinned']})

        elif self.request.method.upper() == 'POST':
            if not is_hr:
                kwargs.update({'exclude_fields': ['pinned']})

        return super().get_serializer(*args, **kwargs)

    def has_user_permission(self):
        post = self.get_post()
        ct_event = ContentType.objects.get_for_model(Event)
        if self.request.method.upper() in ('PATCH', 'PUT'):
            if post and post.content_type == ct_event:
                return True

            return getattr(post, 'posted_by',
                           None) == self.request.user or NOTICE_BOARD_PERMISSION.get(
                "code") in self.request.user.get_hrs_permissions()
        elif self.request.method.upper() == 'GET':

            scheduled_post = self.request.query_params.get('scheduled')
            if scheduled_post and NOTICE_BOARD_PERMISSION.get(
                "code") not in self.request.user.get_hrs_permissions():
                return False
            return post.has_get_permission(
                request=self.request) if post else True
        elif self.request.method.upper() == 'DELETE':
            if post and post.content_type == ct_event:
                event_created_by = post.content_object.created_by
                if event_created_by == self.request.user or getattr(post,
                                                                    'posted_by',
                                                                    None) == self.request.user:
                    return True
                return False

            return getattr(post, 'posted_by',
                           None) == self.request.user or NOTICE_BOARD_PERMISSION.get(
                "code") in self.request.user.get_hrs_permissions() if post else True
        elif self.request.method.upper() == 'POST':
            if self.request.query_params.get('as') == 'hr' and \
                NOTICE_BOARD_PERMISSION.get('code') in self.request.user.get_hrs_permissions():
                return True

            noticeboard = NoticeBoardSetting.objects.first()
            return noticeboard.allow_to_post if noticeboard else True

    def get_post(self):
        if not self.detail:
            return None
        try:
            return Post.objects.filter(
                id=self.kwargs.get('pk')).first()
        except (ValueError, TypeError, ValidationError):
            return None

    @action(methods=['GET'], detail=False)
    def trending(self, request):
        return Response(
            self.get_serializer(
                Post.objects.annotate(
                    likes_count=Count('likes', filter=Q(likes__liked=True),
                                      distinct=True),
                    comments_count=Count('comments', distinct=True)
                ).distinct().select_related(
                    'posted_by',
                    'posted_by__detail',
                    'posted_by__detail__organization',
                    'posted_by__detail__division'
                ).prefetch_related('attachments').order_by(
                    '-likes_count', '-comments_count')[:10],
                many=True
            ).data)

    @action(methods=['GET'], detail=False)
    def my(self, request):
        user = request.user
        queryset = self.get_queryset().filter(
            posted_by=user
        ).order_by(
            F('scheduled_for').desc(nulls_last=True),
            F('pinned').desc(nulls_last=True),
            '-created_at'
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        stats = self.statistics
        # TODO: @shital noticeboard cache has been disabled as it was not used, uncomment set_noticeboard_cahce
        # call from signals after doing TO-DO below.
        # TODO @shital this code has been commented to make filter & search workable
        #  if {'limit', 'offset', 'scheduled'}.isdisjoint(self.request.query_params):
        #      posts, count = get_noticeboard_cache(self.request.user)
        #
        #      # to get next and previous
        #      if count > 5:
        #          url = self.request.build_absolute_uri()
        #          url = replace_query_param(url, "limit", 0)
        #          url = replace_query_param(url, "offset", 5)
        #      else:
        #          url = None
        #
        #      return Response({
        #          "count": count,
        #          "next": url,
        #          "previous": None,
        #          "results": posts,
        #          'stats':stats
        #      })

        response = super().list(request, *args, **kwargs)
        response.data.update({'stats': stats})
        return response

    @property
    def is_hr(self):
        return self.request.query_params.get('as') == 'hr' and \
               NOTICE_BOARD_PERMISSION.get('code') in self.request.user.get_hrs_permissions()

    @action(
        methods=['POST'],
        detail=True,
        url_path='(?P<type>(approve|deny))',
        url_name='status-change',
        serializer_class=DummySerializer
    )
    def status_change(self, request, *args, **kwargs):
        if not self.is_hr:
            return Response({"detail": "Not Found."}, status=status.HTTP_404_NOT_FOUND)
        post = self.get_object()
        if post.status == APPROVED:
            return Response({"detail": "This post has already been approved."},
                            status=status.HTTP_400_BAD_REQUEST)
        status_map = {'approve': APPROVED, 'deny': DENIED}
        post.status = status_map.get(self.kwargs.get('type'))
        post.save()

        url = f'/user/noticeboard'
        actor = self.request.user
        add_notification(
            actor=actor,
            text=f'Your post has been {post.status} by {actor.full_name}.',
            recipient=post.posted_by,
            action=post,
            url=url
        )

        serializer = PostSerializer(post, context=self.get_serializer_context())
        return Response(serializer.data)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['is_hr'] = self.is_hr
        return ctx

    @action(
        detail=True,
        methods=['POST']
    )
    def acknowledge(self, request, *args, **kwargs):
        post = self.get_object()
        if post.category != HR_NOTICE:
            raise RestValidationError({'detail': 'HR Notice can only be acknowledged.'})
        acknowledge = HRNoticeAcknowledgement.objects.get_or_create()
        pass


class PostLikeCommentMixin:
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update(self.kwargs)
        return ctx

    def _get_instance(self):
        instance_for = 'post' if 'post_id' in self.kwargs else 'comment'
        database = {
            'post': Post,
            'comment': PostComment
        }
        return database.get(instance_for).objects.filter(
            id=self.kwargs.get(f'{instance_for}_id')
        ).first()


class DisablePostLikeCommentMixin(PostLikeCommentMixin):
    def initial(self, request, *args, **kwargs):
        super(PostLikeCommentMixin, self).initial(request, *args, *kwargs)
        instance = self._get_instance()
        if instance and not isinstance(instance, Post):
            instance = instance.post
        if not instance:
            raise serializers.ValidationError()
        if instance.disable_comment and \
            request.method.lower() in ['post', 'put', 'patch', 'delete']:
            raise serializers.ValidationError({'detail': 'You can\'t comment on this post'})


class PostLikeViewSet(PostLikeCommentMixin,
                      ListCreateViewSetMixin):
    queryset = PostLike.objects.all()
    serializer_class = PostLikeSerializer
    permission_classes = [LikePermission]

    def get_queryset(self):
        return super().get_queryset().filter(post_id=self.kwargs['post_id'])

    def list(self, request, *args, **kwargs):
        queryset = USER.objects.filter(
            id__in=Subquery(self.filter_queryset(
                self.get_queryset()
            ).filter(
                liked=True
            ).order_by(
                '-created_at'
            ).values(
                'liked_by',
            ))
        ).select_related(
            'detail',
            'detail__organization',
            'detail__division',
            'detail__employment_level',
            'detail__job_title',
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserThinSerializer(
                page,
                many=True
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserThinSerializer(queryset, many=True)
        return Response(serializer.data)

    def has_user_permission(self):
        if self.request.method.upper() == 'GET':
            post = self.get_post()
            return post.has_get_permission(
                request=self.request) if post else True
        return True

    def get_post(self):
        return Post.objects.filter(
            id=self.kwargs.get('post_id')).first()


class PostCommentViewSet(DisablePostLikeCommentMixin,
                         ListCreateUpdateDestroyViewSetMixin):
    queryset = PostComment.objects.all()
    serializer_class = PostCommentSerializer
    permission_classes = [CommentPermission]

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        comment_likes = CommentLike.objects.filter(
            liked=True).select_related(
            'liked_by', 'liked_by__detail',
            'liked_by__detail__organization',
            'liked_by__detail__division'
        )

        return super().get_queryset().filter(post_id=post_id).prefetch_related(
            Prefetch('likes',
                     queryset=comment_likes.filter(
                         liked_by=self.request.user),
                     to_attr='liked_by_user')
        ).all()

    def get_post(self):
        return Post.objects.filter(
            id=self.kwargs.get('post_id')).first()

    def has_user_permission(self):
        if self.request.method.upper() == 'DELETE':

            comment = self._get_comment()
            if comment and comment.commented_by_id == self.request.user.id:
                return True

            post = self.get_post()
            if post and post.posted_by_id == self.request.user.id:
                return True

            return False

        if self.request.method.upper() == 'GET':
            post = self.get_post()
            return post.has_get_permission(
                request=self.request) if post else True

        return True

    def _get_comment(self):
        # just return comment instance without raising 404
        # used in permission as get_object calls has_object_permission and
        # there will be a loop
        comment_id = self.kwargs.get('pk')
        try:
            return self.get_queryset().get(id=comment_id)
        except (
            PostComment.DoesNotExist, TypeError, ValueError,
            ValidationError):
            return None


class CommentLikeViewSet(DisablePostLikeCommentMixin,
                         ListCreateViewSetMixin):
    queryset = CommentLike.objects.all()
    serializer_class = CommentLikeSerializer

    permission_classes = [CommentLikePermission]

    def get_queryset(self):
        qs = super().get_queryset().filter(
            comment_id=drf_get_object_or_404(
                PostComment,
                pk=self.kwargs.get('comment_id')
            )
        )
        if self.action.lower() == 'list':
            qs = qs.filter(liked=True)
        return qs

    def has_user_permission(self):
        if self.request.method.upper() == 'GET':
            comment = self.get_comment()
            post = comment.post if comment else None
            return post.has_get_permission(
                request=self.request) if post else True

        return True

    def get_comment(self):
        return PostComment.objects.filter(
            id=self.kwargs.get('comment_id')).first()


class CommentReplyViewSet(DisablePostLikeCommentMixin,
                          ModelViewSet):
    queryset = CommentReply.objects.all()
    serializer_class = CommentReplySerializer
    permission_classes = [CommentReplyPermission]

    def get_queryset(self):
        return super().get_queryset().filter(
            comment_id=self.kwargs['comment_id'])

    def has_user_permission(self):
        comment = self.get_comment()
        if self.request.method.upper() == 'DELETE':
            if comment:
                return comment.commented_by_id == self.request.user.id or \
                       comment.post.posted_by_id == self.request.user.id

        if self.request.method.upper() == 'GET':
            post = comment.post if comment else None
            return post.has_get_permission(
                request=self.request) if post else True

        return True

    def get_comment(self):
        return PostComment.objects.filter(
            id=self.kwargs.get('comment_id')).first()

    def get_reply(self):
        return CommentReply.objects.first(id=self.kwargs.get('id')).first()
