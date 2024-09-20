from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from irhrs.attendance.constants import (
    REDUCTION_TYPE_CHOICES, PENALTY_COUNTER_UNIT_CHOICES, BREAK_OUT_STATUS_CHOICES,
    TIMESHEET_PENALTY_CALCULATION_CHOICES, GENERATED
)

from irhrs.common.models import BaseModel
from irhrs.core.validators import validate_title
from irhrs.leave.models import LeaveType
from irhrs.organization.models import Organization, FiscalYearMonth


class BreakOutPenaltySetting(BaseModel):
    organization = models.ForeignKey(
        to=Organization,
        related_name='break_out_penalty_settings',
        on_delete=models.CASCADE
    )
    title = models.CharField(
        max_length=255,
        validators=[validate_title]
    )
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return "%s - %s" % (self.title, self.organization)


class BreakoutPenaltyLeaveDeductionSetting(BaseModel):
    leave_type_to_reduce = models.ForeignKey(
        to=LeaveType,
        related_name='+',
        on_delete=models.CASCADE,
        help_text="Select a leave type to reduce penalty days from."
    )
    penalty_setting = models.ForeignKey(
        to=BreakOutPenaltySetting,
        related_name='leave_types_to_reduce',
        on_delete=models.CASCADE
    )

    # order = models.PositiveIntegerField()

    # class Meta:
    #     ordering = 'order',
    #     unique_together = ('penalty_setting', 'order')

    def __str__(self):
        return "Reduce %s from %s" % (
            self.leave_type_to_reduce.name,
            self.penalty_setting.title
        )


class PenaltyRule(BaseModel):
    penalty_setting = models.ForeignKey(
        to=BreakOutPenaltySetting,
        related_name='rules',
        on_delete=models.CASCADE
    )
    penalty_duration_in_days = models.FloatField(
        help_text="How many to reduce from payroll/leave?",
        validators=[MinValueValidator(limit_value=0)]
    )
    penalty_counter_value = models.PositiveIntegerField(
        help_text="Resets every? Take it as: 1 month, or every 3 days, regularly late.",
        validators=[MinValueValidator(limit_value=0)]
    )
    penalty_counter_unit = models.CharField(
        max_length=20,
        choices=PENALTY_COUNTER_UNIT_CHOICES,
        db_index=True
    )
    calculation_type = models.CharField(
        max_length=20,
        choices=TIMESHEET_PENALTY_CALCULATION_CHOICES,
        db_index=True
    )
    # the following threshold can be used for either count or sum
    # resets at fiscal year month
    tolerated_duration_in_minutes = models.PositiveIntegerField(
        help_text="Threshold: Break-outs that do not exceed this value, "
                  "is considered grace.",
        validators=[MinValueValidator(limit_value=0)]
    )
    tolerated_occurrences = models.PositiveIntegerField(
        help_text="occurrences threshold.",
        validators=[MinValueValidator(limit_value=0)],
        default=0,
    )
    consider_late_in = models.BooleanField(default=True)
    consider_early_out = models.BooleanField(default=True)
    consider_in_between_breaks = models.BooleanField(default=False)
    penalty_accumulates = models.BooleanField(
        default=True,
        help_text="If false: 100 hours results in 10 times 10 hour scheme."
    )

    def __str__(self):
        return self.calculation_type


class BreakOutReportView(models.Model):
    remark_category = models.CharField(
        max_length=255,
    )
    total_lost = models.DurationField()
    timesheet_for = models.DateField()
    timesheet = models.ForeignKey(
        to='attendance.TimeSheet',
        on_delete=models.DO_NOTHING,
        related_name='break_out_report_view'
    )
    user = models.ForeignKey(
        to=get_user_model(),
        on_delete=models.DO_NOTHING,
        related_name='+'
    )

    class Meta:
        managed = False
        db_table = 'attendance_break_out_report_view'


class BreakOutAggregatedReportView(models.Model):
    total_lost = models.DurationField()
    timesheet = models.OneToOneField(
        to='attendance.TimeSheet',
        on_delete=models.DO_NOTHING,
        related_name='break_out_aggregated_report'
    )

    class Meta:
        managed = False
        db_table = 'attendance_aggregate_breakout_result'


class TimeSheetUserPenalty(BaseModel):
    user = models.ForeignKey(
        to=get_user_model(),
        on_delete=models.CASCADE,
        related_name='break_out_penalty_records',
    )
    rule = models.ForeignKey(
        to=PenaltyRule,
        on_delete=models.CASCADE,
        related_name='+'
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    fiscal_month = models.ForeignKey(
        to=FiscalYearMonth,
        related_name='timesheet_penalties',
        on_delete=models.SET_NULL,
        null=True
    )
    loss_accumulated = models.DurationField()
    lost_days_count = models.PositiveIntegerField()
    penalty_accumulated = models.FloatField()
    status = models.CharField(
        max_length=12,
        default=GENERATED,
        choices=BREAK_OUT_STATUS_CHOICES,
        db_index=True
    )
    remarks = models.CharField(
        max_length=255,
        blank=True
    )

    def __str__(self):
        return "%s lost %s days, %s hours, hence, %s days penalty." % (
            self.user, self.lost_days_count, self.loss_accumulated, self.penalty_accumulated
        )


class TimeSheetPenaltyToPayroll(models.Model):
    user_penalty = models.ForeignKey(
        to=TimeSheetUserPenalty,
        related_name='+',
        on_delete=models.CASCADE
    )
    confirmed_on = models.DateTimeField()
    days = models.FloatField()
    is_archived = models.BooleanField(default=False)


class TimeSheetUserPenaltyStatusHistory(BaseModel):
    break_out_user_record = models.ForeignKey(
        to=TimeSheetUserPenalty,
        related_name='histories',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=12,
        choices=BREAK_OUT_STATUS_CHOICES,
        db_index=True
    )
    remarks = models.CharField(
        max_length=255,
    )
    old_loss_accumulated = models.DurationField()
    new_loss_accumulated = models.DurationField()
    old_lost_days_count = models.PositiveIntegerField()
    new_lost_days_count = models.PositiveIntegerField()
    old_penalty_accumulated = models.FloatField()
    new_penalty_accumulated = models.FloatField()
