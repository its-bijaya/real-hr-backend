from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import cached_property
from django.conf import settings

from sorl import thumbnail

from irhrs.common.models import BaseModel
from irhrs.core.utils.common import get_complete_url, get_upload_path
from irhrs.core.validators import validate_future_datetime, validate_image_file_extension
from irhrs.event.constants import PRIVATE
from irhrs.noticeboard.managers.post import PostManager
from irhrs.noticeboard.constants import POST_STATUS_CHOICES, APPROVED

from irhrs.organization.models import Organization, OrganizationDivision
from irhrs.core.constants.noticeboard import POST_CATEGORY_CHOICES, NORMAL_POST
from irhrs.permission.constants.permissions import NOTICE_BOARD_PERMISSION
from ..utils.file_path import get_post_attachment_path
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator


User = get_user_model()


# TODO: @Shital: Maintain Unique Together for PostLike(Post+Liked_by) and same for CommentLike.

class Post(BaseModel):
    posted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='posts')
    post_content = models.TextField(blank=True, max_length=10000)
    category = models.CharField(
        choices=POST_CATEGORY_CHOICES, default=NORMAL_POST, max_length=50, db_index=True)

    disable_comment = models.BooleanField(default=False)
    # users tagged in the post [optional]
    user_tags = models.ManyToManyField(
        User, related_name='tagged_posts', blank=True)

    # Post Pin
    pinned = models.BooleanField(default=False)
    pinned_on = models.DateTimeField(null=True)

    # HR Notice
    visible_until = models.DateTimeField(null=True)

    # Post Visibility Scope with Organization and Divisions [optional]
    organizations = models.ManyToManyField(
        Organization, related_name='organization_posts', blank=True)
    divisions = models.ManyToManyField(
        OrganizationDivision, related_name='division_posts', blank=True)

    scheduled_for = models.DateTimeField(null=True,
                                         validators=[validate_future_datetime])

    content_type = models.ForeignKey(ContentType, blank=True, null=True,
                                     on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey()
    status = models.CharField(
        choices=POST_STATUS_CHOICES, default=APPROVED, max_length=50,
        db_index=True)

    upload_file = models.FileField(
        null=True,
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
        )]
    )

    objects = PostManager()

    def __str__(self):
        return f"{self.post_content}"

    def has_get_permission(self, request):
        event = self.content_object
        if event and event.event_type == PRIVATE and (
            not event.created_by == request.user and
            NOTICE_BOARD_PERMISSION.get(
                "code") not in request.user.get_hrs_permissions()
            and not event.event_members.filter(user=request.user)):
            return False
        return True


class PostLike(BaseModel):
    post = models.ForeignKey(
        Post, related_name='likes', on_delete=models.CASCADE)
    liked_by = models.ForeignKey(
        User, related_name='liked_posts', on_delete=models.CASCADE)
    liked = models.BooleanField(default=True)

    class Meta:
        unique_together = ('post', 'liked_by',)

    def __str__(self):
        like_action = 'liked' if self.liked else 'unliked'
        return f"{self.liked_by} {like_action} the post {self.post}."


class PostAttachment(BaseModel):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='attachments')
    image = thumbnail.ImageField(
        validators=[validate_image_file_extension],
        upload_to=get_post_attachment_path
    )
    caption = models.CharField(max_length=255, blank=True)

    @cached_property
    def image_extension(self):
        image_url = self.image.url
        return image_url.split(".")[-1]

    @cached_property
    def image_thumb_1(self):
        # patched thumbnail not being generated for svg files
        # for some reasons sorl-thumbnail was not being able to
        # generate thumbnail for svg files
        # TODO: @Shital list supported extensions and use in operator
        if self.image_extension.lower() != 'svg':
            return get_complete_url(thumbnail.get_thumbnail(
                self.image, '492x246',
                crop='center', quality=0
            ).url)
        return get_complete_url(self.image.url)

    @cached_property
    def image_thumb_2(self):
        # patched thumbnail not being generated for svg files
        # for some reasons sorl-thumbnail was not being able to
        # generate thumbnail for svg files
        # TODO: @Shital list supported extensions and use in operator
        if self.image_extension.lower() != 'svg':
            return get_complete_url(thumbnail.get_thumbnail(
                self.image, '115x115',
                crop='center', quality=0
            ).url)
        return get_complete_url(self.image.url)

    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return f"{self.caption}"
