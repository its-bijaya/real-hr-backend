import logging
from functools import lru_cache

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.conf import settings
from irhrs.core.constants.noticeboard import HR_NOTICE, AUTO_GENERATED, ORGANIZATION_NOTICE, \
    CONDOLENCE_POST
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import get_patch_attr, get_prefetched_attribute
from irhrs.event.models import Event
from irhrs.notification.utils import notify_organization
from irhrs.noticeboard.constants import PENDING, APPROVED
from irhrs.noticeboard.utils.like_unlike import create_post_like_notification, \
    create_comment_like_notification
from irhrs.permission.constants.permissions import NOTICE_BOARD_PERMISSION
from irhrs.noticeboard.utils.validators import validate_event
from irhrs.users.api.v1.serializers.thin_serializers import UserThumbnailSerializer, \
    AuthUserThinSerializer
from ....models import Post, PostComment, PostLike, PostAttachment, CommentLike, \
    CommentReply, OrganizationDivision, Organization, NoticeBoardSetting, HRNoticeAcknowledgement

logger = logging.getLogger(__name__)


def liked_by(instance, user):
    """
    Cache noticeboard cache
    :param instance:
    :param user:
    :return:
    """
    return instance.likes.filter(
        liked_by=user,
        liked=True).exists()


class CommentReplySerializer(serializers.ModelSerializer):
    reply_by = UserThumbnailSerializer(read_only=True)

    class Meta:
        model = CommentReply
        fields = ('id', 'created_at', 'reply', 'reply_by', 'modified_at')

    def validate(self, attrs):
        try:
            comment = PostComment.objects.get(id=self.context['comment_id'])
        except PostComment.DoesNotExist:
            raise serializers.ValidationError('Invalid comment.')

        post = comment.post
        if post and self.context['request']:
            validate_event(post, self.context['request'])

        attrs.update(
            {'comment': comment, 'reply_by': self.context['request'].user})
        return attrs


class PostCommentSerializer(serializers.ModelSerializer):
    commented_by = UserThumbnailSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    liked_by_user = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ('id', 'created_at', 'content', 'commented_by', 'image',
                  'likes_count', 'liked_by_user', 'replies_count',
                  'modified_at')

    def get_likes_count(self, instance):
        if hasattr(instance, 'liked_comments'):
            return len(instance.liked_comments)
        return instance.likes.filter(liked=True).count()

    def get_liked_by_user(self, instance):
        if hasattr(instance, 'liked_by_user'):
            if len(instance.liked_by_user) > 0:
                return True
        return False

    def get_replies_count(self, instance):
        if isinstance(instance.replies, list):
            return len(instance.replies)
        return instance.replies.all().count()

    def get_fields(self):
        fields = super().get_fields()
        if self.context['request'].method == 'GET':
            fields['image'] = serializers.SerializerMethodField()
        return fields

    def get_image(self, instance):
        if instance.image:
            from irhrs.core.utils.common import get_complete_url
            return get_complete_url(instance.image.url)
        return

    def validate(self, attrs):
        try:
            post = Post.objects.get(
                id=self.context['post_id'])
        except Post.DoesNotExist:
            raise serializers.ValidationError('Invalid post.')

        if post and self.context['request']:
            validate_event(post, self.context['request'])

        # the request needs to have either text, or an image.
        if not (attrs.get('content') or attrs.get('image')):
            raise ValidationError(
                "The comment must have text or an image."
            )
        attrs.update(
            {'post': post, 'commented_by': self.context['request'].user})
        return attrs


class CommentLikeSerializer(serializers.ModelSerializer):
    liked_by = UserThumbnailSerializer(read_only=True)

    class Meta:
        model = CommentLike
        fields = ('liked_by', 'liked',)

    def validate(self, attrs):
        try:
            comment = PostComment.objects.get(id=self.context['comment_id'])

        except PostComment.DoesNotExist:
            raise serializers.ValidationError('Invalid post comment.')

        post = comment.post
        if post and self.context['request']:
            validate_event(post, self.context['request'])

        attrs.update(
            {'comment': comment, 'liked_by': self.context['request'].user})
        return attrs

    def save(self, **kwargs):
        comment_like_data = {
            'comment': self.validated_data['comment'],
            'liked_by': self.context['request'].user
        }
        comment_like, created = CommentLike.objects.get_or_create(
            **comment_like_data)
        comment_like.liked = self.validated_data.get('liked', True)
        comment_like.save()
        create_comment_like_notification(comment_like)
        return comment_like


class PostLikeSerializer(serializers.ModelSerializer):
    liked_by = UserThumbnailSerializer(read_only=True)

    class Meta:
        model = PostLike
        fields = ('liked_by', 'liked',)

    def validate(self, attrs):
        post = self._get_post()
        if post and self.context['request']:
            validate_event(post, self.context['request'])

        attrs.update(
            {'post': post, 'liked_by': self.context['request'].user})
        return attrs

    def validate_liked(self, liked):
        post = self._get_post()
        if not liked and post.category == HR_NOTICE:
            raise ValidationError("Can not un-acknowledge HR Notice.")
        return liked

    def _get_post(self):
        try:
            return Post.objects.get(id=self.context['post_id'])
        except Post.DoesNotExist:
            raise serializers.ValidationError('Invalid post.')

    def save(self, **kwargs):
        post_like_data = {
            'post': self.validated_data['post'],
            'liked_by': self.context['request'].user
        }
        post_like, created = PostLike.objects.get_or_create(**post_like_data)
        if not created:
            post_like.liked = created or self.validated_data.get('liked', True)
            post_like.save()
        if post_like_data.get('post').category != CONDOLENCE_POST:
            create_post_like_notification(post_like, post_like.liked_by)
        return post_like


class PostAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = ('id', 'image', 'caption', 'image_thumb_1', 'image_thumb_2')


class PostSerializer(DynamicFieldsModelSerializer):
    comments = serializers.SerializerMethodField(read_only=True)
    likes = serializers.SerializerMethodField(read_only=True)
    posted_by = AuthUserThinSerializer(read_only=True)
    attachments = PostAttachmentSerializer(many=True, required=False)
    user_tags = UserThumbnailSerializer(many=True, read_only=True)
    divisions = serializers.SlugRelatedField(
        queryset=OrganizationDivision.objects.all(), slug_field='slug',
        many=True,
        required=False, allow_null=True)
    organizations = serializers.SlugRelatedField(
        queryset=Organization.objects.all(), slug_field='slug', many=True,
        required=False, allow_null=True)

    post_type_id = serializers.IntegerField(
        min_value=1,
        required=False,
        write_only=True
    )

    post_type = serializers.CharField(
        max_length=32,
        allow_blank=True,
        required=False,
        write_only=True
    )

    class Meta:
        model = Post
        fields = (
            'id', 'created_at', 'modified_at', 'posted_by', 'post_content',
            'category', 'pinned', 'pinned_on', 'disable_comment',
            'comments', 'likes', 'attachments', 'user_tags', 'organizations',
            'divisions', 'scheduled_for', 'visible_until', 'upload_file',
            'post_type_id', 'post_type', 'status')
        read_only_fields = ['status']

    @staticmethod
    def validate_upload_file(file):
        if file.size > settings.MAX_FILE_SIZE * 1024 * 1024:
            raise serializers.ValidationError({
              "upload_file": f"File size must be less than or equal to {settings.MAX_FILE_SIZE}"
            })
        return file


    def get_attachments(self, post):
        return PostAttachmentSerializer(
            many=True,
            instance=post.attachments.all(),
            context=self.context
        ).data

    def validate_visible_until(self, visible_until):
        if visible_until and visible_until < timezone.now():
            raise serializers.ValidationError("Date should be in future")

    def extract_attachments(self, request_data):
        attachments = []
        data = dict(request_data)
        for key in data.copy():
            if key.startswith('attachment'):
                image = data.pop(key)
                attachments.append({'image': image[0], 'caption': ''})
        return attachments

    def validate_attachments(self, data):
        request_data = dict(self.context['request'].data)
        attachments = self.extract_attachments(request_data)
        serialized_attachments = PostAttachmentSerializer(data=attachments,
                                                          many=True)
        if not serialized_attachments.is_valid():
            raise serializers.ValidationError('Invalid attachments.')
        return attachments

    def validate_category(self, category):
        request = self.context.get("request")
        if category in [ORGANIZATION_NOTICE, HR_NOTICE] and NOTICE_BOARD_PERMISSION.get("code") not \
                in request.user.get_hrs_permissions():
            raise serializers.ValidationError("You do not have enough "
                                              "permission to post an " + category)
        elif category == AUTO_GENERATED:
            raise serializers.ValidationError("Auto Generated type of posts "
                                              "are reserved for system.")
        return category

    def validate_deleted_attachments(self, deleted_str):
        if not self.instance:
            return None

        attachment_pks = set(self.instance.attachments.all().values_list(
            'pk', flat=True))

        if not deleted_str:
            return []

        import re
        pattern = re.compile(r'((\d+,)+\d+)|\d+')

        if not pattern.match(deleted_str):
            raise serializers.ValidationError('Bad pk values')

        pks = set([int(pk) for pk in deleted_str.split(',')])

        if not pks.issubset(attachment_pks):
            raise serializers.ValidationError('Some of the ids does not exist')
        return pks

    def validate(self, attrs):
        attachments = self.validate_attachments(None)
        attrs.update({
            'attachments': attachments
        })
        # the request needs to have either text, or an image.
        post_content = get_patch_attr(
            'post_content',
            attrs,
            self
        )
        attachments = get_patch_attr(
            'attachments',
            attrs,
            self
        )
        if not (post_content or attachments):
            raise ValidationError(
                "The post must have text or images"
            )

        post_type = attrs.get('post_type')
        post_type_id = attrs.get('post_type_id')

        if post_type and post_type_id:
            pt_errors = []
            if post_type.lower() == 'event':
                try:
                    event_obj = Event.objects.get(id=post_type_id)
                except Event.DoesNotExist:
                    raise serializers.ValidationError('Event not found')
                request = self.context.get('request')
                event_members = event_obj.event_members.filter(
                    user=request.user)

                if not event_obj.interactive_event or not event_obj.enabled_event:
                    pt_errors.append('Event must be interactive or enabled'
                                     ' to post any content')

                if not event_members.exists() and request.user != event_obj.created_by:
                    pt_errors.append('You are not the member of this event')

                if len(pt_errors) > 0:
                    raise ValidationError({'post_type': pt_errors})

                attrs['content_object'] = event_obj

            else:
                raise serializers.ValidationError('Irrelevant type')

        return super().validate(attrs)

    def create(self, validated_data):
        attachments = validated_data.pop('attachments', None)
        divisions = validated_data.pop('divisions', None)
        organizations = validated_data.pop('organizations', None)
        validated_data.pop('post_type', None)
        validated_data.pop('post_type_id', None)

        validated_data.update({
            'posted_by': self.context['request'].user
        })

        if not self.context.get('is_hr', False):
            noticeboard = NoticeBoardSetting.objects.first()
            if noticeboard and noticeboard.need_approval:
                validated_data['status'] = PENDING
        else:
            validated_data['status'] = APPROVED

        post = super().create(validated_data)
        if post.status == PENDING:
            organization = post.posted_by.detail.organization
            url=f'/admin/{organization.slug}/hris/noticeboard-approval/request'
            notify_organization(
                text=f'{post.posted_by} has sent a post approval request.',
                action=post,
                actor=post.posted_by,
                organization=organization,
                permissions=[NOTICE_BOARD_PERMISSION],
                url=url
            )

        for attachment in attachments:
            attachment.update({'post': post})
            PostAttachment.objects.create(**attachment)
        if divisions:
            post.divisions.add(*divisions)
        if organizations:
            post.organizations.add(*organizations)
        return post

    def update(self, instance, validated_data):
        attachments = validated_data.pop('attachments', None)
        divisions = validated_data.pop('divisions', None)
        organizations = validated_data.pop('organizations', None)
        deleted_attachments = validated_data.pop('deleted_attachments', [])

        instance = super().update(instance, validated_data)

        if deleted_attachments:
            instance.attachments.filter(id__in=deleted_attachments).delete()

        for attachment in attachments:
            attachment.update({'post': instance})
            PostAttachment.objects.create(**attachment)

        if divisions:
            instance.divisions.add(*divisions)
        else:
            instance.divisions.clear()
        if organizations:
            instance.organizations.add(*organizations)
        else:
            instance.organizations.clear()

        instance.refresh_from_db()
        return instance

    def get_comments(self, instance):
        # attach first two comments in posts
        ctx = {'request': self.context['request']}
        comments = PostCommentSerializer(
            instance.comments.all()[:3], context=ctx, many=True)
        return {
            'data': comments.data,
            'count': instance.comments.all().count()
        }

    def get_likes(self, instance):
        logged_in_user = self.context['request'].user
        likes_qs = get_prefetched_attribute(instance, 'likes', instance.likes.filter(liked=True))
        # attach first four likes in posts
        likes = PostLikeSerializer(likes_qs[:4],
                                   many=True)
        return {
            'data': likes.data,
            'count': likes_qs.count(),
            'me': liked_by(instance, logged_in_user)
        }

    def get_fields(self):
        request = self.context.get('request')
        fields = super().get_fields()
        # add field deleted_attachments on put
        if request and self.instance and (
            request.method.upper() in ['PUT', 'PATCH']
        ):
            fields["deleted_attachments"] = serializers.CharField(
                required=False)
        if request and request.method == 'GET':
            fields['attachments'] = serializers.SerializerMethodField()
        return fields


class PostCommentCacheSerializer(PostCommentSerializer):
    """Serializer For Caching Post comment"""
    likes = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ('id', 'created_at', 'content', 'commented_by', 'image',
                  'likes_count', 'liked_by_user', 'replies_count',
                  'modified_at', 'likes')

    @staticmethod
    def get_likes(instance):
        likes_qs = get_prefetched_attribute(instance, 'likes', instance.likes.filter(liked=True))
        likes = CommentLikeSerializer(likes_qs, many=True)
        count = likes_qs.count()
        return {
            'data': likes.data,
            'count': count
        }


class PostCacheSerializer(PostSerializer):
    """Serializer For Caching Post"""
    def get_likes(self, instance):
        likes = get_prefetched_attribute(instance, 'likes', instance.likes.filter(liked=True))
        likes_data = PostLikeSerializer(likes, many=True).data

        count = likes.count()

        return {
            'data': likes_data,
            'count': count,
            'me': False
        }

    def get_comments(self, instance):
        # attach first two comments in posts
        ctx = {'request': self.context['request']}

        comments = PostCommentCacheSerializer(
            instance.comments.all()[:3], context=ctx, many=True)
        count = instance.comments.count()
        return {
            'data': comments.data,
            'count': count
        }
