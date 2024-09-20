from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.functional import cached_property

from irhrs.common.models import BaseModel, TimeStampedModel
from irhrs.common.models.payroll import AbstractApprovals, AbstractHistory
from irhrs.core.constants.payroll import APPROVED_BY, SUPERVISOR, SUPERVISOR_LEVEL, \
    ADVANCE_EXPENSE_REQUEST_STATUS_CHOICES, REQUESTED, PENDING, CANCELED
from irhrs.core.validators import validate_future_date
from irhrs.hris.models import EmployeeSeparationType
from irhrs.organization.models import Organization

USER = get_user_model()


class ResignationApprovalSetting(BaseModel):
    organization = models.ForeignKey(
        Organization,
        related_name='resignation_setting',
        on_delete=models.CASCADE
    )
    approve_by = models.CharField(max_length=10, choices=APPROVED_BY, default=SUPERVISOR,
                                  db_index=True)
    supervisor_level = models.CharField(
        choices=SUPERVISOR_LEVEL,
        max_length=6,
        blank=True,
        null=True,
        db_index=True
    )
    employee = models.ForeignKey(
        USER,
        related_name='resignation_setting',
        on_delete=models.CASCADE,
        null=True
    )
    approval_level = models.IntegerField()

    class Meta:
        unique_together = ('organization', 'employee')
        ordering = ('-created_at',)

    def __str__(self):
        _str = f'Resignation request approved by '
        return _str + (
            f'{self.employee}.',
            f'{self.supervisor_level} level supervisor.'
        )[self.approve_by == SUPERVISOR]

    @classmethod
    def exists_for_organization(cls, organization):
        return cls.objects.filter(organization=organization).exists()


class UserResignation(BaseModel):
    employee = models.ForeignKey(
        USER,
        related_name='resignation',
        on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        USER,
        related_name='resignation_recipient',
        on_delete=models.CASCADE,
        null=True
    )
    release_date = models.DateField(validators=[validate_future_date])
    reason = models.TextField(max_length=settings.TEXT_FIELD_MAX_LENGTH)
    remarks = models.TextField(max_length=settings.TEXT_FIELD_MAX_LENGTH)
    status = models.CharField(
        max_length=25,
        choices=ADVANCE_EXPENSE_REQUEST_STATUS_CHOICES,
        default=REQUESTED,
        db_index=True
    )

    def __str__(self):
        return "Resignation for: " + self.employee.full_name

    class Meta:
        ordering = ('-created_at',)

    @cached_property
    def active_approval(self):
        return self.approvals.filter(
            status__in=[PENDING, CANCELED]
        ).order_by('level').first()


class HRApprovalUserResignation(BaseModel):
    resignation = models.OneToOneField(
        UserResignation,
        related_name='hr_approval',
        on_delete=models.CASCADE
    )
    remarks = models.TextField(max_length=settings.TEXT_FIELD_MAX_LENGTH)
    separation_type = models.ForeignKey(
        EmployeeSeparationType,
        on_delete=models.CASCADE,
        null=True
    )


class UserResignationApproval(BaseModel, AbstractApprovals):
    """
    Approvals according to approval setting of advance expense
    """
    resignation = models.ForeignKey(
        UserResignation,
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    user = models.ForeignKey(
        USER,
        on_delete=models.CASCADE,
        related_name='resignation_approvals'
    )

    class Meta:
        ordering = ('level',)


class UserResignationHistory(TimeStampedModel, AbstractHistory):
    """
    Model to record change in advance expense
    """
    request = models.ForeignKey(
        UserResignation,
        on_delete=models.CASCADE,
        related_name='histories'
    )

    def __str__(self):
        return f"{self.actor.full_name} {self.action} " \
               f"{(self.target + ' ') if self.target else ''}" \
               f"{f'with remarks {self.remarks}.' if self.remarks else '.'}"

    class Meta:
        ordering = ('-created_at',)
