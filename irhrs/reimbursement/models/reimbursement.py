from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import JSONField
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models
from django.utils.functional import cached_property
from irhrs.attendance.models.travel_attendance import TravelAttendanceRequest

from irhrs.common.constants import CURRENCIES
from irhrs.common.models import BaseModel, TimeStampedModel
from irhrs.common.models.payroll import AbstractApprovals, AbstractHistory
from irhrs.core.constants.payroll import ADVANCE_EXPENSE_REQUEST_STATUS_CHOICES, \
    PENDING, CANCELED, REQUESTED, ADVANCE_EXPENSE_REQUEST_CANCEL_STATUS_CHOICES, APPROVED
from irhrs.core.utils.common import get_upload_path
from irhrs.reimbursement.constants import EXPENSE_TYPE, TRAVEL, NPR

USER = get_user_model()


class AdvanceExpenseRequest(BaseModel):
    employee = models.ForeignKey(
        USER,
        on_delete=models.CASCADE,
        related_name='advance_expense_request_by'
    )
    recipient = models.ManyToManyField(
        USER,
        related_name='advance_expense_requests_to_act'
    )
    advance_code = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text='Auto generated TAARF code.'
    )
    reason = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=EXPENSE_TYPE, default=TRAVEL)
    associates = models.ManyToManyField(USER, related_name='expense_request')
    description = models.TextField(max_length=settings.TEXT_FIELD_MAX_LENGTH, blank=True)
    remarks = models.TextField(max_length=settings.TEXT_FIELD_MAX_LENGTH, blank=True)
    status = models.CharField(
        choices=ADVANCE_EXPENSE_REQUEST_STATUS_CHOICES,
        default=REQUESTED,
        max_length=25,
        db_index=True
    )
    total_amount = models.FloatField(default=0, validators=[MinValueValidator(0)])
    advance_amount = models.FloatField(default=0, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=6, choices=CURRENCIES, default=NPR)
    add_signature = models.BooleanField(default=False)
    detail = JSONField()
    requested_amount = models.FloatField(default=0)

    # remarks = models.TextField(max_length=settings.TEXT_FIELD_MAX_LENGTH, blank=True)

    def __str__(self):
        return f'Advance expense requested by {self.employee.full_name}'

    @cached_property
    def active_approval(self):
        return self.approvals.filter(
            status__in=[PENDING, CANCELED]
        ).order_by('level').first()


class AdvanceExpenseRequestDocuments(BaseModel):
    expense = models.ForeignKey(
        AdvanceExpenseRequest,
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


class AdvanceExpenseRequestApproval(BaseModel, AbstractApprovals):
    """
    Approvals according to approval setting of advance expense
    """
    expense = models.ForeignKey(AdvanceExpenseRequest, on_delete=models.CASCADE,
                                related_name='approvals')
    user = models.ManyToManyField(
        USER,
        related_name='approvals'
    )
    acted_by = models.ForeignKey(
        USER,
        related_name='request_actors',
        on_delete=models.SET_NULL,
        null=True
    )
    add_signature = models.BooleanField(default=False)

    class Meta:
        ordering = ('level',)


class AdvanceExpenseRequestHistory(TimeStampedModel, AbstractHistory):
    """
    Model to record change in advance expense
    """
    request = models.ForeignKey(AdvanceExpenseRequest, on_delete=models.CASCADE,
                                related_name='histories')

    def __str__(self):
        return f"{self.actor.full_name} {self.action} " \
               f"{(self.target + ' ') if self.target else ''}" \
               f"{f'with remarks {self.remarks}.' if self.remarks else '.'}"

    class Meta:
        ordering = ('created_at',)


class TravelRequestFromAdvanceRequest(BaseModel):
    advance_expense_request = models.OneToOneField(
    AdvanceExpenseRequest, on_delete=models.CASCADE, related_name='travel_request_from_advance'
    )
    start = models.DateField()
    start_time = models.TimeField()
    end = models.DateField()
    end_time = models.TimeField()

    def __str__(self) -> str:
        return self.advance_expense_request.employee.full_name


class AdvanceExpenseCancelHistory(BaseModel):
    advance_expense = models.ForeignKey(
        to=AdvanceExpenseRequest,
        on_delete=models.CASCADE,
        related_name='cancel_history'
    )
    recipient = models.ManyToManyField(
        USER,
        related_name='cancel_request_to_act'
    )
    status = models.CharField(
        max_length=20,
        choices=ADVANCE_EXPENSE_REQUEST_CANCEL_STATUS_CHOICES,
        default=REQUESTED,
        db_index=True
    )
    remarks = models.CharField(
        max_length=255
    )

    def __str__(self):
        return self.status

    @cached_property
    def active_approval(self):
        return self.approvals.filter(
            status__in=[PENDING, CANCELED]
        ).order_by('level').first()


class AdvanceExpenseCancelRequestApproval(BaseModel, AbstractApprovals):
    """
    Approvals according to approval setting of advance expense
    """
    expense_cancel = models.ForeignKey(
        AdvanceExpenseCancelHistory,
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    user = models.ManyToManyField(
        USER,
        related_name='cancel_approvals'
    )
    acted_by = models.ForeignKey(
        USER,
        related_name='cancel_actors',
        on_delete=models.SET_NULL,
        null=True
    )
    add_signature = models.BooleanField(default=False)

    class Meta:
        ordering = ('level',)
