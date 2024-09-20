from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import JSONField
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models
from django.utils.functional import cached_property

from irhrs.common.constants import CURRENCIES
from irhrs.common.models import BaseModel, TimeStampedModel
from irhrs.common.models.payroll import AbstractApprovals, AbstractHistory
from irhrs.core.constants.payroll import ADVANCE_EXPENSE_REQUEST_STATUS_CHOICES, PENDING, \
    REQUESTED, CANCELED
from irhrs.core.utils.common import get_upload_path
from irhrs.reimbursement.constants import EXPENSE_TYPE, TRAVEL, SETTLEMENT_OPTION, CASH, NPR

from irhrs.reimbursement.models import AdvanceExpenseRequest

USER = get_user_model()


class ExpenseSettlement(BaseModel):
    advance_expense = models.ForeignKey(
        AdvanceExpenseRequest,
        related_name='settlement',
        on_delete=models.CASCADE,
        null=True
    )
    employee = models.ForeignKey(
        USER,
        on_delete=models.CASCADE,
        related_name='settlement_request_by'
    )
    recipient = models.ManyToManyField(
        USER,
        related_name='settlement_requests_to_act'
    )
    reason = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=EXPENSE_TYPE, default=TRAVEL)
    description = models.TextField(max_length=settings.TEXT_FIELD_MAX_LENGTH, blank=True)
    remark = models.TextField(max_length=settings.TEXT_FIELD_MAX_LENGTH, blank=True)
    status = models.CharField(
        choices=ADVANCE_EXPENSE_REQUEST_STATUS_CHOICES,
        default=REQUESTED,
        max_length=25,
        db_index=True
    )
    total_amount = models.FloatField(default=0, validators=[MinValueValidator(0)])
    advance_amount = models.FloatField(default=0, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=6, choices=CURRENCIES, default=NPR)
    is_taxable = models.BooleanField(default=False)
    add_signature = models.BooleanField(default=False)
    detail = JSONField()
    travel_report = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST)],
        null=True
    )

    def __str__(self):
        return self.reason

    @cached_property
    def active_approval(self):
        return self.approvals.filter(
            status__in=[PENDING, CANCELED]
        ).order_by('level').first()

    @property
    def has_advance_expense(self):
        return bool(self.advance_expense)


class SettlementDocuments(BaseModel):
    settle = models.ForeignKey(
        ExpenseSettlement,
        related_name='documents',
        on_delete=models.CASCADE
    )
    attachment = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST)]
    )
    name = models.CharField(max_length=255, default='Unnamed')

    def __str__(self):
        return self.name


class SettlementOption(BaseModel):
    settle = models.OneToOneField(
        ExpenseSettlement,
        related_name='option',
        on_delete=models.CASCADE
    )
    settle_with = models.CharField(max_length=20, choices=SETTLEMENT_OPTION, default=CASH)
    attachment = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST)]
    )
    remark = models.CharField(max_length=225)

    def __str__(self):
        return self.settle_with


class SettlementApproval(BaseModel, AbstractApprovals):
    """
    Approvals according to approval setting of advance expense
    """
    settle = models.ForeignKey(
        ExpenseSettlement,
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    user = models.ManyToManyField(
        USER,
        related_name='settle_approvals'
    )
    acted_by = models.ForeignKey(
        USER,
        related_name='approved_requests',
        on_delete=models.SET_NULL,
        null=True
    )
    add_signature = models.BooleanField(default=False)

    class Meta:
        ordering = ('level',)


class SettlementHistory(TimeStampedModel, AbstractHistory):
    """
    Model to record change in settlement
    """
    request = models.ForeignKey(ExpenseSettlement, on_delete=models.CASCADE,
                                related_name='histories')

    def __str__(self):
        return f"{self.actor.full_name} {self.action} " \
               f"{(self.target + ' ') if self.target else ''}" \
               f"{f'with remarks {self.remarks}.' if self.remarks else '.'}"

    class Meta:
        ordering = ('created_at',)
