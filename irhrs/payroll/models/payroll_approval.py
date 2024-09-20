from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.constants.payroll import PENDING, APPROVED
from .payroll import Payroll, REJECTED

USER = get_user_model()


PAYROLL_APPROVAL_STATUS_CHOICES = (
    (PENDING, 'Pending'),
    (APPROVED, 'Approved'),
    (REJECTED, 'Rejected')
)


class PayrollApproval(BaseModel):
    payroll = models.ForeignKey(
        Payroll,
        related_name='payroll_approvals',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        USER,
        related_name='payroll_approvals',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        choices=PAYROLL_APPROVAL_STATUS_CHOICES,
        default=PENDING,
        max_length=15,
        db_index=True
    )
    approval_level = models.SmallIntegerField(validators=[MinValueValidator(limit_value=0)])

    class Meta:
        unique_together = ('user', 'payroll')

    def __str__(self):
        return f"USER: {self.user}, APPROVAL_LEVEL: {self.approval_level}, status: {self.status}"


class PayrollApprovalHistory(BaseModel):
    payroll = models.ForeignKey(
        Payroll,
        related_name='payroll_approval_histories',
        on_delete=models.CASCADE
    )
    actor = models.ForeignKey(
        USER,
        related_name='payroll_action_histories',
        on_delete=models.CASCADE
    )
    action = models.CharField(max_length=25)
    remarks = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.actor.full_name} {self.action}" \
               f"{' with remarks ' + self.remarks if self.remarks else ''}."
