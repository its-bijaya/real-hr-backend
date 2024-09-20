from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.constants.payroll import APPROVED_BY, SUPERVISOR, SUPERVISOR_LEVEL
from irhrs.organization.models import EmploymentStatus, Organization
from irhrs.payroll.models import Heading

User = get_user_model()


class AdvanceSalarySetting(BaseModel):
    organization = models.OneToOneField(
        Organization,
        related_name='advance_salary_setting',
        on_delete=models.CASCADE
    )
    time_of_service_completion = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=182,  # in days
        help_text="Time of Service Completion"
    )
    request_limit = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=6,
        help_text="Maximum number of requests in fiscal year"
    )
    request_interval = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=60,  # in days
        help_text="Interval between requests"
    )
    complete_previous_request = models.BooleanField(
        default=True,
        help_text="Previous request to be completed?"
    )
    excluded_employment_type = models.ManyToManyField(
        to=EmploymentStatus,
        help_text="Exclude employees with certain employment types"
    )
    limit_upto = models.FloatField(
        null=True,
        help_text="Limit up to which user can request for advance salary"
    )
    disbursement_limit_for_repayment = models.IntegerField(
        default=6,
        validators=[MinValueValidator(0)],
        help_text="Maximum duration of repayment"
    )
    deduction_heading = models.ForeignKey(
        null=True,
        to=Heading,
        help_text="Heading used to deduct advance salary repayments.",
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.organization.name


class AmountSetting(BaseModel):
    advance_salary_setting = models.ForeignKey(
        AdvanceSalarySetting,
        related_name='amount_setting',
        on_delete=models.CASCADE
    )
    payroll_heading = models.ForeignKey(
        Heading,
        related_name='amount_setting',
        on_delete=models.CASCADE
    )
    multiple = models.FloatField(validators=[MinValueValidator(0)])

    def __str__(self):
        return 'Payroll heading `{}` has amount {} for organization {}'.format(
            self.payroll_heading,
            self.multiple,
            self.advance_salary_setting
        )

    class Meta:
        unique_together = ('advance_salary_setting', 'payroll_heading')


class ApprovalSetting(BaseModel):
    advance_salary_setting = models.ForeignKey(
        AdvanceSalarySetting,
        related_name='approval_setting',
        on_delete=models.CASCADE
    )
    approve_by = models.CharField(max_length=10, choices=APPROVED_BY, default=SUPERVISOR)
    supervisor_level = models.CharField(
        choices=SUPERVISOR_LEVEL,
        max_length=6,
        blank=True,
        null=True
    )
    employee = models.ForeignKey(
        User,
        related_name='approval_setting',
        on_delete=models.CASCADE,
        null=True
    )
    approval_level = models.IntegerField()

    class Meta:
        unique_together = [
            ['advance_salary_setting', 'supervisor_level'],
            ['advance_salary_setting', 'employee'],
            ['advance_salary_setting', 'approval_level']
        ]

    def __str__(self):
        _str = f'Advance salary request approved by '
        return _str + (
            f'{self.employee}.',
            f'{self.supervisor_level} level supervisor.'
        )[self.approve_by == SUPERVISOR]
