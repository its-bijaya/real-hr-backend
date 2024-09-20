from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from irhrs.common.models import BaseModel
from irhrs.core.validators import validate_multiple_of_half
from irhrs.leave.constants.model_constants import (
    LEAVE_LIMIT_DURATION_CHOICES, LEAVE_DURATION_CHOICES,
    PRIOR_APPROVAL_UNITS, ADJACENT_OFFDAY_HOLIDAY_INCLUSIVE_OPTION)
from irhrs.leave.utils.validations import validate_rule_limits
from irhrs.leave.constants.model_constants import (
    HOLIDAY_INCLUSIVE_OPTION
)


class LeaveRule(BaseModel):
    leave_type = models.ForeignKey(
        'leave.LeaveType',
        on_delete=models.CASCADE,
        related_name='leave_rules'
    )
    irregularity_report = models.BooleanField(default=False)

    name = models.CharField(max_length=155)
    description = models.TextField(max_length=600)

    # is set to true when master setting expires
    is_archived = models.BooleanField(default=False)

    # limit leave in given year/days
    limit_leave_to = models.FloatField(
        help_text=_("Number of leave user can take in given duration"),
        null=True
    )
    limit_leave_duration = models.PositiveIntegerField(
        null=True,
        validators=[validate_rule_limits]
    )
    limit_leave_duration_type = models.CharField(
        choices=LEAVE_LIMIT_DURATION_CHOICES,
        max_length=7,
        null=True,
        db_index=True
    )

    # min/max balance
    min_balance = models.FloatField(
        help_text=_("Minimum balance user can have at any moment. Deduction "
                    "rules will not be applied below this limit."),
        null=True
    )
    max_balance = models.FloatField(
        help_text=_("Maximum balance user can have at any moment. Accumulation "
                    "rules will not be applied above this limit."),
        null=True
    )

    # leave occurrence
    limit_leave_occurrence = models.SmallIntegerField(
        help_text=_("Limit leave request occurrence."),
        null=True
    )
    limit_leave_occurrence_duration = models.PositiveIntegerField(
        null=True,
        validators=[validate_rule_limits]
    )
    limit_leave_occurrence_duration_type = models.CharField(
        choices=LEAVE_LIMIT_DURATION_CHOICES,
        max_length=7,
        null=True
    )

    # continuous leave limits
    maximum_continuous_leave_length = models.FloatField(
        help_text=_("Maximum days user can take continuous leave. In case of "
                    "time off maximum minutes"),
        null=True,
        validators=[validate_rule_limits]
    )
    minimum_continuous_leave_length = models.FloatField(
        help_text=_("Minimum days user can take continuous leave. In case of "
                    "time off minimum minutes"),
        null=True,
        validators=[validate_rule_limits]
    )
    year_of_service = models.IntegerField(
        validators=[MinValueValidator(0)],
        null=True,
        help_text=_("In months. If user crosses year of service limit, s/he "
                    "doesn't have max and min continuous leave validation.")
    )

    holiday_inclusive = models.BooleanField(null=True,
        help_text=_("Include Holidays/Off days ?")
    )
    inclusive_leave = models.CharField(
        max_length=32,
        choices=HOLIDAY_INCLUSIVE_OPTION,
        null=True,
        db_index=True
    )
    inclusive_leave_number = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        null=True
    )

    is_paid = models.BooleanField()
    proportionate_on_joined_date = models.BooleanField(null=True,
        help_text=_("Proportionate leave on joined date.")
    )
    proportionate_on_contract_end_date = models.BooleanField(null=True,
        help_text=_("Proportionate leave on contract_end_date.")
    )
    proportionate_on_probation_end_date = models.BooleanField(null=True,
        help_text=_("Proportionate leave on probation end date.")
    )
    can_apply_half_shift = models.BooleanField(null=True, )
    employee_can_apply = models.BooleanField()
    admin_can_assign = models.BooleanField()

    can_apply_beyond_zero_balance = models.BooleanField(null=True,
        help_text=_("Can apply beyond zero balance")
    )
    beyond_limit = models.FloatField(
        help_text=_("Beyond limit."),
        null=True
    )

    required_experience = models.FloatField(
        null=True,
        validators=[validate_rule_limits]
    )
    required_experience_duration = models.CharField(
        choices=LEAVE_DURATION_CHOICES,
        max_length=7,
        null=True,
        db_index=True
    )

    require_prior_approval = models.BooleanField(
        validators=[validate_rule_limits]
    )
    prior_approval = models.IntegerField(null=True)
    prior_approval_unit = models.CharField(
        max_length=20,
        blank=True,
        choices=PRIOR_APPROVAL_UNITS
    )

    require_docs = models.BooleanField(null=True, )
    require_docs_for = models.FloatField(
        help_text=_("Require docs upon leave for more than this days/minutes "
                    "in case of time off."),
        null=True
    )

    # Only accept leave requests within this range
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

    depletion_required = models.BooleanField(null=True, )
    depletion_leave_types = models.ManyToManyField(
        'leave.LeaveType',
        related_name="need_depletion",
    )

    adjacent_offday_inclusive = models.BooleanField(default=False)
    adjacent_offday_inclusive_type = models.CharField(
        max_length=32,
        choices=ADJACENT_OFFDAY_HOLIDAY_INCLUSIVE_OPTION,
        blank=True,
        db_index=True
    )
    # adjacent_offday_inclusive_leave_types = models.ManyToManyField('leave.LeaveType')

    cloned_from = models.ForeignKey(
        to='leave.LeaveRule',
        related_name='cloned_leave_rules',
        on_delete=models.SET_NULL,
        null=True,
    )

    def __str__(self):
        return f"{self.name} of type {self.leave_type}"

    @property
    def adjacent_offday_inclusive_leave_types(self):
        return self.reduction_leave_types.order_by('order_field')


class AdjacentLeaveReductionTypes(BaseModel):
    leave_rule = models.ForeignKey(
        to=LeaveRule,
        on_delete=models.CASCADE,
        related_name='reduction_leave_types'
    )
    leave_type = models.ForeignKey(
        to='leave.LeaveType',
        on_delete=models.CASCADE,
        related_name='+'
    )
    order_field = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = 'order_field',


class LeaveIrregularitiesRule(BaseModel):
    leave_rule = models.OneToOneField(
        to=LeaveRule,
        on_delete=models.CASCADE,
        related_name='leave_irregularity',
        null=True
    )
    weekly_limit = models.FloatField(
        null=True,
        validators=[validate_rule_limits]
    )
    fortnightly_limit = models.FloatField(
        null=True,
        validators=[validate_rule_limits]
    )
    monthly_limit = models.FloatField(
        null=True,
        validators=[validate_rule_limits]
    )
    quarterly_limit = models.FloatField(
        null=True,
        validators=[validate_rule_limits]
    )
    semi_annually_limit = models.FloatField(
        null=True,
        validators=[validate_rule_limits]
    )
    annually_limit = models.FloatField(
        null=True,
        validators=[validate_rule_limits]
    )

    def __str__(self):
        return f"Weekly->{self.weekly_limit} " \
               f"Monthly->{self.monthly_limit} " \
               f"Annually->{self.annually_limit}"


class AccumulationRule(BaseModel):
    rule = models.OneToOneField(
        LeaveRule,
        related_name="accumulation_rule",
        on_delete=models.CASCADE
    )
    duration = models.IntegerField(
        validators=[validate_rule_limits]
    )
    duration_type = models.CharField(
        choices=LEAVE_DURATION_CHOICES,
        max_length=7,
        db_index=True
    )
    balance_added = models.FloatField()

    # rules for counting days of accumulation
    exclude_absent_days = models.BooleanField(default=False)

    exclude_off_days = models.BooleanField(default=False)
    count_if_present_in_off_day = models.BooleanField(default=False)

    exclude_holidays = models.BooleanField(default=False)
    count_if_present_in_holiday = models.BooleanField(default=False)

    exclude_unpaid_leave = models.BooleanField(default=False)
    exclude_paid_leave = models.BooleanField(default=False)
    exclude_half_leave = models.BooleanField(default=False)


class RenewalRule(BaseModel):
    rule = models.OneToOneField(
        LeaveRule,
        related_name="renewal_rule",
        on_delete=models.CASCADE
    )
    duration = models.IntegerField()
    duration_type = models.CharField(
        choices=LEAVE_DURATION_CHOICES,
        max_length=7,
        db_index=True
    )
    initial_balance = models.FloatField()
    max_balance_encashed = models.FloatField(null=True)
    max_balance_forwarded = models.FloatField(null=True)
    is_collapsible = models.BooleanField(null=True, )
    back_to_default_value = models.BooleanField(default=False)


class DeductionRule(BaseModel):
    rule = models.OneToOneField(
        LeaveRule,
        related_name="deduction_rule",
        on_delete=models.CASCADE
    )
    duration = models.IntegerField(
        validators=[validate_rule_limits]
    )
    duration_type = models.CharField(
        choices=LEAVE_DURATION_CHOICES,
        max_length=7,
        db_index=True
    )
    balance_deducted = models.FloatField()


class YearsOfServiceRule(BaseModel):
    rule = models.OneToOneField(
        LeaveRule,
        related_name="yos_rule",
        on_delete=models.CASCADE
    )
    years_of_service = models.IntegerField(
        validators=[validate_rule_limits]
    )
    balance_added = models.FloatField()

    collapse_after = models.FloatField(
        null=True,
        validators=[validate_rule_limits]
    )
    collapse_after_unit = models.CharField(
        choices=LEAVE_DURATION_CHOICES,
        max_length=7,
        null=True
    )


class CompensatoryLeave(BaseModel):
    rule = models.ForeignKey(
        LeaveRule,
        related_name="compensatory_rules",
        on_delete=models.CASCADE
    )
    balance_to_grant = models.FloatField()
    hours_in_off_day = models.FloatField()
    class Meta:
        ordering = ('created_at', 'modified_at')

class CompensatoryLeaveCollapsibleRule(BaseModel):
    rule = models.OneToOneField(
        LeaveRule,
        related_name="leave_collapsible_rule",
        on_delete=models.CASCADE
    )
    collapse_after = models.FloatField(
        null=True,
        validators=[validate_rule_limits]
    )
    collapse_after_unit = models.CharField(
        choices=LEAVE_DURATION_CHOICES,
        max_length=7,
        null=True,
        db_index=True
    )


class TimeOffRule(BaseModel):
    rule = models.OneToOneField(
        LeaveRule,
        related_name='time_off_rule',
        on_delete=models.CASCADE
    )
    total_late_minutes = models.IntegerField()
    leave_type = models.ForeignKey(
        to='leave.LeaveType',
        on_delete=models.CASCADE,
    )
    reduce_leave_by = models.FloatField(validators=[validate_multiple_of_half])


class CreditHourRule(BaseModel):
    rule = models.OneToOneField(
        LeaveRule,
        related_name='credit_hour_rule',
        on_delete=models.CASCADE
    )

    minimum_request_duration_applicable = models.BooleanField()
    minimum_request_duration = models.DurationField(null=True)

    maximum_request_duration_applicable = models.BooleanField()
    maximum_request_duration = models.DurationField(null=True)

    def __str__(self):
        return f"{self.rule}"


class PriorApprovalRule(BaseModel):
    rule = models.ForeignKey(
        LeaveRule,
        related_name='prior_approval_rules',
        on_delete=models.CASCADE
    )
    prior_approval_request_for = models.IntegerField(null=True)
    prior_approval = models.IntegerField(null=True)
    prior_approval_unit = models.CharField(
        choices=PRIOR_APPROVAL_UNITS,
        max_length=20,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ('created_at', 'modified_at')

    def __str__(self):
        return f"{self.rule}"
