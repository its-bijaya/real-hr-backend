from itertools import chain

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from irhrs.common.models import BaseModel
from irhrs.worklog.utils import get_work_log_attachment_path


def validate_score(score):
    if not (1 <= score <= 10):
        raise ValidationError("Must be from 1-10")
    return score


class WorkLog(BaseModel):
    date = models.DateField()
    description = models.TextField()

    score = models.PositiveSmallIntegerField(null=True, blank=True,
                                             validators=[validate_score])
    score_remarks = models.TextField(null=True, blank=True)

    verified_by = models.ForeignKey(get_user_model(),
                                    on_delete=models.SET_NULL,
                                    null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (self.description[:15] + '...') if len(
            self.description) > 15 else self.description

    @property
    def is_verified(self):
        return bool(self.score) or bool(self.verified_by) or bool(
            self.verified_at)

    @property
    def status(self):
        if self.is_verified:
            return 'reviewed'
        return 'pending'


class WorkLogAttachment(BaseModel):
    log = models.ForeignKey(WorkLog, on_delete=models.CASCADE,
                            related_name='worklog_attachments')
    attachment = models.FileField(
        upload_to=get_work_log_attachment_path,
        validators=[FileExtensionValidator(
            allowed_extensions=list(chain.from_iterable(settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )
    description = models.TextField()

    def __str__(self):
        return self.log


class WorkLogComment(BaseModel):
    comment = models.TextField(max_length=1000)
    work_log = models.ForeignKey(WorkLog, on_delete=models.CASCADE,
                                 related_name='worklog_comments')

    def __str__(self):
        return self.comment
