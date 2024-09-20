import logging

from django.db import models
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model

from irhrs.attendance.constants import (
    REQUESTED, ADJUSTMENT_STATUS_CHOICES, ATT_ADJUSTMENT, APPROVED, CANCELLED,
    TIMESHEET_ENTRY_CATEGORIES, ADJUSTMENT_ACTION_CHOICES, ADD, DELETE, UPDATE,
    TIMESHEET_ENTRY_REMARKS
)
from irhrs.attendance.managers.timesheet import AttendanceAdjustmentManager
from irhrs.common.models import BaseModel
from irhrs.core.validators import validate_past_datetime
from .attendance import TimeSheet, TimeSheetEntry

USER = get_user_model()

logger = logging.getLogger(__name__)


class AttendanceAdjustment(BaseModel):
    timesheet = models.ForeignKey(
        to=TimeSheet,
        related_name='adjustment_requests',
        on_delete=models.CASCADE
    )
    category = models.CharField(
        max_length=15,
        choices=TIMESHEET_ENTRY_REMARKS,
        blank=True,
        db_index=True
    )
    timestamp = models.DateTimeField(null=True, validators=[validate_past_datetime])
    timesheet_entry = models.ForeignKey(
        to=TimeSheetEntry,
        on_delete=models.SET_NULL,  # TimeSheet Entry has soft-delete only.
        null=True,
        related_name='adjustments'
    )
    action = models.CharField(
        choices=ADJUSTMENT_ACTION_CHOICES,
        default=ADD,
        max_length=15,
        db_index=True
    )
    old_punch_in = models.DateTimeField(null=True, validators=[validate_past_datetime])
    old_punch_out = models.DateTimeField(null=True, validators=[validate_past_datetime])
    new_punch_in = models.DateTimeField(null=True, validators=[validate_past_datetime])
    new_punch_out = models.DateTimeField(null=True, validators=[validate_past_datetime])

    status = models.CharField(
        choices=ADJUSTMENT_STATUS_CHOICES,
        default=REQUESTED,
        max_length=15,
        db_index=True
    )
    description = models.CharField(max_length=255)

    sender = models.ForeignKey(
        to=USER,
        related_name='adjustment_requests',
        on_delete=models.SET_NULL,
        null=True
    )

    receiver = models.ForeignKey(
        to=USER,
        related_name='adjustment_requests_received',
        on_delete=models.SET_NULL,
        null=True
    )

    objects = AttendanceAdjustmentManager()

    def __str__(self):
        return f"Attendance Adjustment of {self.timesheet}"

    def approve(self, approved_by, remark=''):
        logger.debug(f"Adjusting {self.timesheet}.")
        if self.action == ADD:
            logger.debug(f"Adjusting {self.timesheet} -->> Clocking at: {self.timestamp}")
            TimeSheet.objects.clock(
                user=self.timesheet.timesheet_user,
                timesheet=self.timesheet,
                entry_method=ATT_ADJUSTMENT,
                date_time=self.timestamp,
                remark_category=self.category,
                remarks=self.description
            )
        elif self.action == DELETE:
            self.timesheet_entry.soft_delete()
        elif self.action == UPDATE:
            entry = self.timesheet_entry
            entry.remark_category = self.category
            entry.entry_method = ATT_ADJUSTMENT
            entry.remarks = self.description
            entry.save()
            entry.timesheet.fix_entries()
        self.status = APPROVED
        self.save()
        AttendanceAdjustmentHistory.objects.create(
            adjustment=self,
            action_performed=APPROVED,
            action_performed_by=approved_by,
            action_performed_to=approved_by,
            remark=remark
        )
        logger.debug(f"Adjusting {self.timesheet}. -->> Complete")

    def cancel(self, cancelled_by, remark):
        logger.info(f"Adjusting {self.timesheet}. -->> Deleting adjustment.")
        if self.new_punch_in:
            entry = self.timesheet.timesheet_entries.filter(
                timestamp=self.new_punch_in,
                entry_method=ATT_ADJUSTMENT
            ).first()
            if entry:
                entry.soft_delete()
                logger.info(f"Attendance adjustment punch in entry deleted.")
            else:
                logger.warning(
                    f"Canceling adjustment request id {self.id}, punch in entry not found"
                )

        if self.new_punch_out:
            entry = self.timesheet.timesheet_entries.filter(
                timestamp=self.new_punch_out,
                entry_method=ATT_ADJUSTMENT
            ).first()
            if entry:
                entry.soft_delete()
                logger.info(f"Attendance adjustment punch out entry deleted.")
            else:
                logger.warning(
                    f"Canceling adjustment request id {self.id}, punch out entry not found"
                )
        self.status = CANCELLED
        self.save()

        AttendanceAdjustmentHistory.objects.create(
            adjustment=self,
            action_performed=CANCELLED,
            action_performed_by=cancelled_by,
            action_performed_to=cancelled_by,
            remark=remark
        )

        logger.info(f"Adjusting {self.timesheet}. -->> Complete")


class AttendanceAdjustmentHistory(BaseModel):
    adjustment = models.ForeignKey(
        AttendanceAdjustment, related_name='adjustment_histories',
        on_delete=models.CASCADE
    )
    action_performed = models.CharField(
        choices=ADJUSTMENT_STATUS_CHOICES,
        max_length=15,
        db_index=True
    )
    action_performed_by = models.ForeignKey(
        to=USER, related_name='sent_adjustments', on_delete=models.CASCADE
    )
    action_performed_to = models.ForeignKey(
        to=USER, related_name='received_adjustments',
        on_delete=models.SET_NULL, null=True
    )
    remark = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.action_performed_by} " \
               f"{self.get_action_performed_display()} to " \
               f"{self.action_performed_to} for " \
               f"{self.adjustment} with remarks {self.remark}"
