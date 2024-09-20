from django.contrib.auth import get_user_model
from django.db import models

from irhrs.attendance.constants import TIMESHEET_ENTRY_METHODS, TIMESHEET_ENTRY_TYPES, \
    TIMESHEET_ENTRY_CATEGORIES, UNCATEGORIZED, TIMESHEET_ENTRY_REMARKS, OTHERS, REQUESTED, \
    TIMESHEET_APPROVAL_CHOICES
from irhrs.attendance.models import TimeSheet
from irhrs.common.models import BaseModel
from irhrs.core.validators import MinMaxValueValidator

USER = get_user_model()


class TimeSheetApproval(BaseModel):
    timesheet = models.OneToOneField(
        TimeSheet,
        related_name='timesheet_approval',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=16,
        choices=TIMESHEET_APPROVAL_CHOICES,
        default=REQUESTED,
        db_index=True
    )


class TimeSheetEntryApproval(BaseModel):
    timesheet_approval = models.ForeignKey(TimeSheetApproval,
                                  related_name='timesheet_entry_approval',
                                  on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=TIMESHEET_APPROVAL_CHOICES,
        default=REQUESTED,
        db_index=True
    )
    recipient = models.ForeignKey(
        USER,
        related_name='timesheet_entry_approvals',
        on_delete=models.SET_NULL,
        null=True
    )
    timestamp = models.DateTimeField(blank=False, null=False)
    entry_method = models.CharField(
        max_length=15, choices=TIMESHEET_ENTRY_METHODS, null=True, db_index=True
    )
    entry_type = models.CharField(
        max_length=15, choices=TIMESHEET_ENTRY_TYPES, null=True, db_index=True
    )
    category = models.CharField(
        max_length=15, choices=TIMESHEET_ENTRY_CATEGORIES,
        default=UNCATEGORIZED, db_index=True
    )
    remark_category = models.CharField(
        max_length=30,
        choices=TIMESHEET_ENTRY_REMARKS,
        default=OTHERS,
        db_index=True
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    # location of entry
    latitude = models.FloatField(null=True, blank=True,
                                 validators=[MinMaxValueValidator(min_value=-90, max_value=90)])
    longitude = models.FloatField(null=True, blank=True,
                                  validators=[MinMaxValueValidator(min_value=-180, max_value=180)])
