from django.db import models

from irhrs.common.models.abstract import BaseModel


class NoticeBoardSetting(BaseModel):
    """
    Model that determines  either to allow user to post, and post need approval to
    be appear on noticeboard. The model encapsulates allow_to_post and need_approval.
    Both fields allow_to_post and need_approval are boolean type
    """

    allow_to_post = models.BooleanField(default=True)
    need_approval = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.allow_to_post}"
