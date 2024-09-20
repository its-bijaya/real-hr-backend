from django.contrib import admin
from .models import (Post, PostLike, PostAttachment, PostComment, CommentLike, CommentReply,
                     HRNoticeAcknowledgement, NoticeBoardSetting)

from irhrs.core.utils.admin.filter import AdminFilterByStatus, AdminFilterByDate

# Comment
admin.site.register(PostComment, AdminFilterByDate)
admin.site.register(CommentLike, AdminFilterByDate)
admin.site.register(CommentReply, AdminFilterByDate)

# HR notice
admin.site.register(HRNoticeAcknowledgement, AdminFilterByDate)

# Noticeboard setting
admin.site.register(NoticeBoardSetting, AdminFilterByDate)

# Post
admin.site.register(Post, AdminFilterByStatus)
admin.site.register(PostLike, AdminFilterByDate)
admin.site.register(PostAttachment, AdminFilterByDate)
