from django.contrib.auth import get_user_model
from django.db import models

from irhrs.attendance.constants import REQUESTED, STATUS_CHOICES, PRE_APPROVAL_STATUS_CHOICES
from irhrs.attendance.models import OvertimeClaim, OvertimeEntry
from irhrs.common.models import BaseModel

USER = get_user_model()


class ApprovalModelMixin(BaseModel):
    sender = models.ForeignKey(
        to=USER,
        related_name='+',
        on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        to=USER,
        related_name='+',
        on_delete=models.CASCADE
    )
    request_remarks = models.CharField(max_length=255)
    action_remarks = models.CharField(max_length=255)

    class Meta:
        abstract = True


class PreApprovalOvertime(ApprovalModelMixin):
    status = models.CharField(
        default=REQUESTED,
        max_length=30,
        choices=PRE_APPROVAL_STATUS_CHOICES,
        db_index=True
    )
    overtime_duration = models.DurationField(
        help_text="The duration user wants to stay in overtime."
    )
    overtime_date = models.DateField(
        help_text="The day where user wants to stay in overtime."
    )
    overtime_entry = models.OneToOneField(
        to=OvertimeEntry,
        related_name='pre_approval',
        null=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return " ".join(
            map(
                str,
                (
                    self.sender,
                    self.request_remarks,
                    self.overtime_duration,
                    self.overtime_date
                )
            )
        )


class PreApprovalOvertimeHistory(BaseModel):
    pre_approval = models.ForeignKey(
        to=PreApprovalOvertime,
        related_name='histories',
        on_delete=models.CASCADE
    )
    action_performed = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        db_index=True
    )
    remarks = models.CharField(
        max_length=255
    )
    action_performed_by = models.ForeignKey(
        to=USER,
        related_name='+',
        on_delete=models.CASCADE
    )
    action_performed_to = models.ForeignKey(
        to=USER,
        related_name='+',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return " ".join([
            self.action_performed_by.full_name,
            self.action_performed,
            self.action_performed_to.full_name,
        ])
