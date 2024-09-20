from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.functional import cached_property

from config import settings
from irhrs.attendance.models import TimeSheet
from irhrs.common.models import BaseModel
from irhrs.core.utils import nested_getattr
from irhrs.leave.constants.model_constants import LEAVE_ACCOUNT_ACTION_CHOICES, \
    ENCASHMENT_CHOICE_TYPES, LEAVE_ENCASHMENT_SOURCE_CHOICES, LEAVE_RENEW, HOURLY_LEAVE_CATEGORIES
from .rule import LeaveRule
from ..managers.leave_account import LeaveAccountHistoryManager
from ...core.utils.common import humanize_interval
from ...core.validators import validate_multiple_of_half

User = get_user_model()


class LeaveAccount(BaseModel):
    user = models.ForeignKey(
        User,
        related_name='leave_accounts',
        on_delete=models.CASCADE
    )
    rule = models.ForeignKey(
        LeaveRule,
        related_name='accounts',
        on_delete=models.CASCADE
    )

    balance = models.FloatField(default=0, validators=[validate_multiple_of_half])
    usable_balance = models.FloatField(default=0, validators=[validate_multiple_of_half])

    is_archived = models.BooleanField(default=False)

    # last renewed works as a pointer for renewals of accounts
    last_renewed = models.DateTimeField(null=True, blank=True)

    # ########## DISCONTINUED FIELDS ########## #
    # The field next_accrue is no longer valid.
    # The origin logic is modified to sync according to Leave Fiscal Year Month's start date.
    next_renew = models.DateTimeField(null=True, blank=True)
    # ########## // DISCONTINUED FIELDS ########## #

    last_accrued = models.DateTimeField(null=True, blank=True)
    # ########## DISCONTINUED FIELDS ########## #
    # The field next_accrue is no longer valid.
    # The origin logic is modified to sync according to Leave Fiscal Year Month's start date.
    next_accrue = models.DateTimeField(null=True, blank=True)
    # ########## //DISCONTINUED FIELDS ########## #

    # For deduction rules to be applicable.
    last_deduction = models.DateTimeField(null=True)
    next_deduction = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.user.full_name}"

    @cached_property
    def master_setting(self):
        return nested_getattr(
            self,
            'rule.leave_type.master_setting'
        )


class CompensatoryLeaveAccount(BaseModel):
    leave_account = models.ForeignKey(
        to=LeaveAccount,
        related_name='compensatory_leave',
        on_delete=models.CASCADE
    )
    timesheet = models.ForeignKey(
        to=TimeSheet,
        related_name='compensatory_leave',
        on_delete=models.CASCADE
    )
    # the DateField ensures that multiple leaves are not granted for same day.
    leave_for = models.DateField()
    balance_granted = models.FloatField(validators=[validate_multiple_of_half])
    balance_consumed = models.FloatField(default=0, validators=[validate_multiple_of_half])

    def __str__(self):
        return f"{self.timesheet.timesheet_user} -> " \
               f"{self.timesheet.timesheet_for} -> {self.balance_granted}"


class LeaveAccountHistory(BaseModel):
    account = models.ForeignKey(
        LeaveAccount,
        related_name='history',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name='leave_account_history',
        on_delete=models.CASCADE
    )
    actor = models.ForeignKey(
        User,
        related_name='acted_accounts_history',
        null=True,
        on_delete=models.SET_NULL
    )
    action = models.CharField(
        choices=LEAVE_ACCOUNT_ACTION_CHOICES,
        max_length=11,
        db_index=True
    )
    objects = LeaveAccountHistoryManager()

    previous_balance = models.FloatField()
    previous_usable_balance = models.FloatField()

    new_balance = models.FloatField()
    new_usable_balance = models.FloatField()

    remarks = models.TextField(blank=True)

    """
    UPDATE: Add fields:
    * accrued
    * renewed
    * encashed
    * forwarded
    * deducted/collapsed
    to maintain a ledger sheet for leave balance.
    This will make report calculation faster.
    """
    accrued = models.FloatField(null=True)
    renewed = models.FloatField(null=True)
    encashed = models.FloatField(null=True)
    carry_forward = models.FloatField(null=True)
    deducted = models.FloatField(null=True)

    def __str__(self):
        prev, curr = self.previous_usable_balance, self.new_usable_balance
        u = self.user.full_name
        actor = self.actor.full_name
        return f"{actor} {self.action} {prev} to {curr} for {u}"


class LeaveEncashment(BaseModel):
    user = models.ForeignKey(
        User,
        related_name='leave_encashments',
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        LeaveAccount,
        related_name='encashments',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=15,
        choices=ENCASHMENT_CHOICE_TYPES,
        db_index=True
    )
    balance = models.FloatField(
        validators=[MinValueValidator(limit_value=1)]
    )

    # for internal use only, to send encashed amount based on approved date
    approved_on = models.DateTimeField(null=True)
    source = models.CharField(
        max_length=20,
        choices=LEAVE_ENCASHMENT_SOURCE_CHOICES,
        default=LEAVE_RENEW,
        db_index=True
    )

    @property
    def balance_display(self):
        if self.account.rule.leave_type.category in HOURLY_LEAVE_CATEGORIES:
            return humanize_interval(self.balance * 60)
        return round(self.balance) if settings.ROUND_LEAVE_BALANCE else round(self.balance, 2)


class LeaveEncashmentHistory(BaseModel):
    actor = models.ForeignKey(
        to=User,
        null=True,
        on_delete=models.CASCADE,
        related_name='acted_leave_encashment_histories'
    )
    encashment = models.ForeignKey(
        to=LeaveEncashment,
        related_name='history',
        on_delete=models.CASCADE
    )

    action = models.CharField(
        max_length=15,
        db_index=True
    )

    previous_balance = models.FloatField(null=True)
    new_balance = models.FloatField(null=True)

    remarks = models.CharField(max_length=255, blank=True)

    @property
    def previous_balance_display(self):
        if self.previous_balance:
            if self.encashment.account.rule.leave_type.category in HOURLY_LEAVE_CATEGORIES:
                return humanize_interval(self.previous_balance * 60)
            return round(self.previous_balance, 2)
        return self.previous_balance

    @property
    def new_balance_display(self):
        if self.new_balance:
            if self.encashment.account.rule.leave_type.category in HOURLY_LEAVE_CATEGORIES:
                return humanize_interval(self.new_balance * 60)
            return round(self.new_balance, 2)
        return self.new_balance

    def __str__(self):
        actor = getattr(self.actor, 'full_name', '')
        action = f"{self.action.lower()}"
        balance_change = f"balance from {self.previous_balance_display or '0.0'} to " \
                         f"{self.new_balance_display}" \
            if self.previous_balance != self.new_balance else ''
        remarks = f"with remarks {self.remarks}" if self.remarks else ""
        return f"{actor} {action} {balance_change} {remarks}"


class AdjacentTimeSheetOffdayHolidayPenalty(BaseModel):
    penalty_for = models.DateField()
    penalty = models.FloatField(default=1.0)
    leave_account = models.ForeignKey(
        to=LeaveAccount,
        related_name='+',
        on_delete=models.CASCADE
    )
    processed = models.BooleanField(null=True, )

    def __str__(self):
        return "%.2f Penalty for %s for %s" % (
            self.penalty, self.penalty_for, self.leave_account
        )
