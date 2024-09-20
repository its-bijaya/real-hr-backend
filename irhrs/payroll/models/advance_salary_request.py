from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import JSONField
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models
from django.db.models import Sum
from django.utils.functional import cached_property

from irhrs.common.models import BaseModel, TimeStampedModel
from irhrs.core.constants.payroll import (
    ADVANCE_SALARY_REQUEST_STATUS_CHOICES, REQUESTED, PENDING, DENIED, COMPLETED,
    REPAYMENT_TYPES, APPROVAL_STATUS_CHOICES, SURPLUS_REQUEST_STATUS_CHOICES)
from irhrs.core.utils.common import get_upload_path
from irhrs.core.validators import validate_future_date
from irhrs.payroll.models import EmployeePayroll
from irhrs.payroll.models.advance_salary_settings import APPROVED_BY

Employee = get_user_model()


class AdvanceSalaryRequest(BaseModel):
    """
    AdvanceSalaryRequest

    This model stores requests for advance salary.
    """

    # separate employee field is maintained because
    # HR may also request advance salary directly
    # on behalf of employee
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE,
        related_name='advance_salary_requests'
    )
    recipient = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='advance_salary_requests_to_act'
    )

    amount = models.FloatField()
    requested_for = models.DateField(validators=[validate_future_date])
    above_limit = models.BooleanField(default=False)
    reason_for_request = models.TextField(max_length=600)

    status = models.CharField(
        choices=ADVANCE_SALARY_REQUEST_STATUS_CHOICES,
        default=REQUESTED,
        max_length=25,
        db_index=True
    )
    payslip_generation_date = models.DateField(null=True)

    disbursement_count_for_repayment = models.IntegerField(
        validators=[MinValueValidator(limit_value=1)],
        null=True,
        help_text="Number of salary disbursements required to repay the salary."
    )

    # Repayment plan JSON
    # Used to create Repayment instances when approved
    repayment_plan = JSONField(null=True)

    # used in reporting
    paid_amount = models.FloatField(null=True)

    def __str__(self):
        return f"Advance salary request of {self.employee.full_name} for {self.amount}"

    @cached_property
    def active_approval(self):
        return self.approvals.filter(
            status__in=[PENDING, DENIED],
            user=self.recipient
        ).order_by('level').first()

    def calculate_paid_amount(self):
        self.paid_amount = self.repayments.filter(
            paid=True).aggregate(sum=Sum('amount'))['sum'] or 0.0

        if self.paid_amount == self.amount:
            self.status = COMPLETED

        self.save()


class AdvanceSalaryRepayment(BaseModel):
    """
    Repayment instance
    """
    request = models.ForeignKey(AdvanceSalaryRequest, on_delete=models.CASCADE,
                                related_name='repayments')
    amount = models.FloatField()

    # order field to maintain which repayment to pay first
    order = models.IntegerField()

    paid = models.BooleanField(default=False)
    paid_on = models.DateField(null=True)
    payment_type = models.CharField(choices=REPAYMENT_TYPES, max_length=25, blank=True)
    payroll_reference = models.ForeignKey(
        EmployeePayroll,
        on_delete=models.SET_NULL,
        null=True
    )

    # settlement remarks
    remarks = models.TextField(max_length=600, blank=True)
    attachment = models.FileField(
        upload_to=get_upload_path,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST)]
    )

    def __str__(self):
        return f"Repayment {self.order} with amount {self.amount}" \
               f" {'paid' if self.paid else 'unpaid'} for request id {self.request_id}."

    def save(self, **kwargs):
        super().save(**kwargs)

        if self.paid:
            # if paid update paid amount in request instance
            self.request.calculate_paid_amount()

    class Meta:
        ordering = ('order', 'created_at')


class AdvanceSalaryRequestDocument(BaseModel):
    """
    Support Documents for advance salary request.
    """
    name = models.CharField(max_length=255, default='Unnamed')
    attachment = models.FileField(validators=[FileExtensionValidator(
        allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST)], upload_to=get_upload_path)
    request = models.ForeignKey(AdvanceSalaryRequest, on_delete=models.CASCADE,
                                related_name='documents')


class AdvanceSalaryRequestApproval(BaseModel):
    """
    Approvals according to approval setting of advance salary
    """
    request = models.ForeignKey(AdvanceSalaryRequest, on_delete=models.CASCADE,
                                related_name='approvals')

    user = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='salary_approvals'
    )
    status = models.CharField(max_length=25, choices=APPROVAL_STATUS_CHOICES, db_index=True)
    role = models.CharField(max_length=25, choices=APPROVED_BY)
    level = models.IntegerField(
        validators=[MinValueValidator(limit_value=1)]
    )

    remarks = models.TextField(max_length=600)

    class Meta:
        ordering = ('level',)


class AdvanceSalaryRequestHistory(TimeStampedModel):
    """
    Model to record change in advance salary
    """
    request = models.ForeignKey(AdvanceSalaryRequest, on_delete=models.CASCADE,
                                related_name='histories')
    actor = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20)
    target = models.CharField(max_length=40, blank=True)  # extra description
    remarks = models.TextField(max_length=600, blank=True)

    def __str__(self):
        return f"{self.actor.full_name} {self.action} " \
               f"{(self.target + ' ') if self.target else ''}" \
               f"{f'with remarks {self.remarks}.' if self.remarks else '.'}"

    class Meta:
        ordering = ('created_at',)


class AdvanceSalarySurplusRequest(BaseModel):
    """
    Request to temporarily raise limit of advance salary amount.
    After this request is approved, limit is temporarily raised
    and employee can request beyond limit.
    """
    employee = models.ForeignKey(Employee, related_name='surplus_requests',
                                 on_delete=models.CASCADE)
    amount = models.FloatField()
    limit_amount = models.FloatField()

    reason_for_request = models.TextField(max_length=600)

    status = models.CharField(choices=SURPLUS_REQUEST_STATUS_CHOICES,
                              default=REQUESTED,
                              max_length=25,
                              db_index=True)

    # reference to advance salary request after raising the limit
    advance_salary_request = models.OneToOneField(
        AdvanceSalaryRequest,
        related_name='surplus_request',
        null=True,
        on_delete=models.SET_NULL
    )

    acted_by = models.ForeignKey(Employee, related_name='acted_surplus_requests',
                                 on_delete=models.SET_NULL, null=True)
    acted_on = models.DateTimeField(null=True)
    action_remarks = models.TextField(max_length=600)
