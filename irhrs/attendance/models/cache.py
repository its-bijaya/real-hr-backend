from django.db import models
from irhrs.common.models import BaseModel

from .source import AttendanceSource

from ..constants import ATTENDANCE_CACHE_REASONS, SYNC_PENDING


class AttendanceEntryCache(BaseModel):
    created = models.DateTimeField(auto_now_add=True)
    source = models.ForeignKey(AttendanceSource, on_delete=models.SET_NULL,
                               related_name='entry_cache', null=True)
    bio_id = models.CharField(max_length=11)
    timestamp = models.DateTimeField()
    entry_category = models.CharField(max_length=11, help_text='Entry Category from Device')
    reason = models.PositiveSmallIntegerField(choices=ATTENDANCE_CACHE_REASONS,
                                              default=SYNC_PENDING)
    sync_tries = models.IntegerField(default=0)
    sync_description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.source} -> {self.bio_id}"

    class Meta:
        ordering = ('timestamp',)
        unique_together = (('source', 'bio_id', 'timestamp'),)
