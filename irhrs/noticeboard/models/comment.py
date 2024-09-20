from django.db import models
from irhrs.common.models import BaseModel
from irhrs.core.validators import validate_image_file_extension

from irhrs.noticeboard.utils.file_path import get_comment_attachment_path
from .post import Post
from django.contrib.auth import get_user_model
User = get_user_model()


class PostComment(BaseModel):
    post = models.ForeignKey(
        Post, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField(blank=True, max_length=1000)
    commented_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='post_comments', editable=False)
    image = models.ImageField(
        upload_to=get_comment_attachment_path, blank=True, null=True,
        validators=[validate_image_file_extension]
    )

    def __str__(self):
        return f"{self.content}"


class CommentLike(BaseModel):
    comment = models.ForeignKey(
        PostComment, related_name='likes', on_delete=models.CASCADE)
    liked_by = models.ForeignKey(
        User, related_name='comment_likes', on_delete=models.CASCADE)
    liked = models.BooleanField(default=True)

    class Meta:
        unique_together = ('comment', 'liked_by',)

    def __str__(self):
        like_action = 'liked' if self.liked else 'unliked'
        return f"{self.liked_by} {like_action} the comment {self.comment}."


class CommentReply(BaseModel):
    comment = models.ForeignKey(
        PostComment, related_name='replies', on_delete=models.CASCADE)
    reply_by = models.ForeignKey(
        User, related_name='comment_replies', on_delete=models.CASCADE)
    reply = models.TextField(blank=False, max_length=1000)

    def __str__(self):
        return f"Comment reply by: {self.reply_by}"
