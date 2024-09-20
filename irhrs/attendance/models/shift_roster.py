from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from irhrs.attendance.models.workshift import WorkShift
from irhrs.common.models.abstract import BaseModel

USER = get_user_model()


class TimeSheetRoster(BaseModel):
    user = models.ForeignKey(
        USER,
        related_name='timesheet_rosters',
        on_delete=models.CASCADE
    )
    shift = models.ForeignKey(
        WorkShift,
        related_name='timesheet_rosters',
        on_delete=models.CASCADE
    )
    date = models.DateField()

    def __str__(self):
        return " ".join(map(str, (self.user, self.shift, self.date)))
