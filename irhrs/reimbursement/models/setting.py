from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.constants.payroll import SUPERVISOR, APPROVED_BY, SUPERVISOR_LEVEL_FOR_RECRUITMENT
from irhrs.core.validators import MinMaxValueValidator
from irhrs.organization.models import Organization, MinValueValidator
from irhrs.reimbursement.constants import SETTLEMENT_OPTION

USER = get_user_model()


class ReimbursementSetting(BaseModel):
    organization = models.OneToOneField(
        Organization,
        related_name='reimbursement_setting',
        on_delete=models.CASCADE
    )
    advance_code = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    approve_multiple_times = models.BooleanField(default=True)
    per_diem_rate = models.FloatField(MinMaxValueValidator(0,1), default=1.0)
    lodging_rate = models.FloatField(MinMaxValueValidator(0,1), default=1.0)
    others_rate = models.FloatField(MinMaxValueValidator(0,1), default=1.0)
    travel_report_mandatory = models.BooleanField(default=False)


class ApprovalSetting(BaseModel):
    approve_by = models.CharField(max_length=10, choices=APPROVED_BY, default=SUPERVISOR)
    supervisor_level = models.CharField(
        choices=SUPERVISOR_LEVEL_FOR_RECRUITMENT,
        max_length=6,
        blank=True,
        null=True
    )
    approval_level = models.IntegerField()
    select_employee = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            ['organization', 'supervisor_level'],
            ['organization', 'approval_level']
        ]
        abstract = True

    def __str__(self):
        _str = f'Reimbursement request approved by '
        return _str + (
            f'{self.employee}.',
            f'{self.supervisor_level} level supervisor.'
        )[self.approve_by == SUPERVISOR]

class ExpenseApprovalSetting(ApprovalSetting):
    organization = models.ForeignKey(
        Organization,
        related_name='expense_setting',
        on_delete=models.CASCADE
    )
    employee = models.ManyToManyField(
        USER,
        related_name='expense_settings',
    )

class SettlementApprovalSetting(ApprovalSetting):
    organization = models.ForeignKey(
        Organization,
        related_name='settlement_setting',
        on_delete=models.CASCADE
    )
    employee = models.ManyToManyField(
        USER,
        related_name='settlement_settings',
    )

class SettlementOptionSetting(BaseModel):
    setting = models.ForeignKey(
        ReimbursementSetting,
        related_name='options',
        on_delete=models.CASCADE
    )
    option = models.CharField(max_length=20, choices=SETTLEMENT_OPTION)

