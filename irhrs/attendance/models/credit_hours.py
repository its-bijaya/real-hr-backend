from django.contrib.auth import get_user_model
from django.db import models

from irhrs.attendance.constants import CREDIT_STATUS, NOT_ADDED, REQUESTED, STATUS_CHOICES, \
    OVERTIME_CALCULATION_CHOICES, CREDIT_HOUR_CALCULATION_CHOICES, OVERTIME_REDUCTION_CHOICES, \
    CREDIT_HOUR_REDUCTION_CHOICES, NEITHER, EXPIRATION_CHOICES, CREDIT_HOUR_STATUS_CHOICES
from irhrs.attendance.models import OvertimeClaim, OvertimeEntry, OvertimeSetting, TimeSheet
from irhrs.common.models import BaseModel, SlugModel
from .pre_approval import ApprovalModelMixin
from ..utils.validators import validate_daily_overtime_limit, validate_weekly_overtime_limit, \
    validate_monthly_overtime_limit, validate_off_day_overtime_limit
from ...core.validators import validate_title

USER = get_user_model()


class CreditHourSetting(SlugModel, BaseModel):
    """
    Taking Credit Hour as Approval based Only.
    For non-approval Credit Hours System,
        Reusing most of overtime utils,
        append the total seconds to Leave.
    """
    organization = models.ForeignKey(
        to='organization.Organization',
        related_name='credit_hour_settings',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=150,
        validators=[validate_title]
    )
    minimum_credit_request = models.DurationField(
        help_text="Eg: User can not request less than 15 minutes."
    )
    daily_credit_hour_limit_applicable = models.BooleanField(null=True,
        help_text='Flag for daily_credit_hour_limit is applicable in system.'
    )
    daily_credit_hour_limit = models.PositiveSmallIntegerField(
        validators=[validate_daily_overtime_limit],
        null=True,
        help_text='Usage: A employee can not work more than 3 hrs credit in any day.'
    )
    weekly_credit_hour_limit_applicable = models.BooleanField(null=True,
        help_text='Flag for weekly_credit_hour_limit is applicable in system.'
    )
    weekly_credit_hour_limit = models.PositiveSmallIntegerField(
        validators=[validate_weekly_overtime_limit],
        null=True,
        help_text='Usage: A employee can not work more than 10 hrs credit in any week.'
    )
    monthly_credit_hour_limit_applicable = models.BooleanField(null=True,
        help_text='Flag for monthly_credit_hour_limit is applicable in system.'
    )
    monthly_credit_hour_limit = models.PositiveSmallIntegerField(
        null=True,
        help_text='Usage: A employee can not work more than 40 hrs credit in any month.'
    )
    off_day_credit_hour = models.BooleanField(default=False)
    off_day_credit_hour_limit = models.PositiveSmallIntegerField(
        validators=[validate_off_day_overtime_limit],
        null=True
    )
    holiday_credit_hour = models.BooleanField(default=False)
    holiday_credit_hour_limit = models.PositiveSmallIntegerField(
        validators=[validate_off_day_overtime_limit],
        null=True
    )
    credit_hour_calculation = models.PositiveSmallIntegerField(
        help_text="At the end of day? week? month? to append the earned balance to leave.",
        choices=CREDIT_HOUR_CALCULATION_CHOICES
    )
    is_archived = models.BooleanField(
        default=False,
        help_text="Archiving a credit hour setting will not be assignable to employees."
                  "Use it when no longer applicable to org policy. Keep for past computed data."
    )
    deduct_credit_hour_after_for = models.CharField(
        max_length=20,
        choices=CREDIT_HOUR_REDUCTION_CHOICES,
        default=NEITHER,
        help_text='Generate credit to calculate only after criteria deducted'
                  'Eg: If `True`: 16 min will calculate 1 min; if `False`, will generate 16',
        db_index=True
    )
    flat_reject_value = models.PositiveSmallIntegerField(
        help_text='The total overtime less than this value will be rejected',
        default=0
    )
    credit_hour_expires = models.BooleanField(null=True, )
    expires_after = models.PositiveSmallIntegerField(null=True)
    expires_after_unit = models.CharField(
        max_length=1,
        choices=EXPIRATION_CHOICES,
        blank=True,
        db_index=True
    )
    require_prior_approval = models.BooleanField(null=True,
        help_text="Prior Approval is a flag to ignore overtime from being created by default. "
                  "Settings with this flag will be excluded from default logic of creating credit hours."
    )
    grant_overtime_for_exceeded_minutes = models.BooleanField(null=True,
        db_column='compensatory_time_off',
        help_text="If enabled; will grant exceeded overtime to CompensatoryTimeOff."
    )
    overtime_setting = models.ForeignKey(
        to=OvertimeSetting,
        null=True,
        on_delete=models.SET_NULL
    )
    reduce_credit_if_actual_credit_lt_approved_credit = models.BooleanField(null=True,
        db_column='min_worked_approved',
        help_text="Expanded: Reduce Overtime If Actual Overtime is Less Than Approved Overtime."
                  " FUNC: MIN(worked_hours, approved_hours)"
    )
    allow_edit_of_pre_approved_credit_hour = models.BooleanField(null=True,
        db_column='editable_pre_approved_credit_hrs',
        help_text="If ON; Allows Pre Approved OT to be edited and re-flowed."
                  "If OFF; Pre Approved OT is Finalized."
    )

    # allow_delete = models.BooleanField(null=True,
    #     db_column='allow_delete',
    #     help_text="If enabled; user can delete approved credit hour."
    # )

    class Meta:
        unique_together = ('organization', 'slug')

    def __str__(self):
        return f"{self.name} {self.organization} {'Active' if not self.is_archived else 'Archived'}"

    @property
    def editable(self):
        # not editable if it is being used in Settings or Overtime Entries.
        being_used = self.individual_settings.exists()
        return not being_used


class CreditHourRequest(ApprovalModelMixin):
    status = models.CharField(
        default=REQUESTED,
        max_length=30,
        choices=CREDIT_HOUR_STATUS_CHOICES,
        db_index=True
    )
    credit_hour_duration = models.DurationField(
        help_text="The duration user wants to request for."
    )
    credit_hour_date = models.DateField(
        help_text="The day where user wants to request for credit hours."
    )
    credit_entry = models.OneToOneField(
        to='attendance.CreditHourTimeSheetEntry',
        null=True,
        on_delete=models.SET_NULL,
        related_name='credit_request'
    )
    is_deleted = models.BooleanField(null=True, )
    travel_attendance_request = models.ForeignKey(
        to='attendance.TravelAttendanceRequest',
        related_name='credit_hour_requests',
        on_delete=models.SET_NULL,
        null=True
    )
    credit_hour_status = models.CharField(
        max_length=30,
        default=NOT_ADDED,
        choices=CREDIT_STATUS
    )

    def __str__(self):
        return " ".join(
            map(
                str,
                (
                    self.sender,
                    self.request_remarks,
                    self.credit_hour_duration,
                    self.credit_hour_date
                )
            )
        )


class CreditHourRequestHistory(BaseModel):
    credit_hour = models.ForeignKey(
        to=CreditHourRequest,
        related_name='histories',
        on_delete=models.CASCADE
    )
    action_performed = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        db_index=True
    )
    remarks = models.CharField(
        max_length=255
    )
    action_performed_by = models.ForeignKey(
        to=USER,
        related_name='+',
        on_delete=models.CASCADE
    )
    action_performed_to = models.ForeignKey(
        to=USER,
        related_name='+',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return " ".join([
            self.action_performed_by.full_name,
            self.action_performed,
            self.action_performed_to.full_name,
        ])


class CreditHourTimeSheetEntry(BaseModel):
    # Credit Hour  TimeSheet Maps each/group of timesheets for their credit hours earned.
    timesheet = models.ForeignKey(
        to=TimeSheet,
        on_delete=models.CASCADE,
        related_name='credit_entries'
    )
    credit_setting = models.ForeignKey(
        to=CreditHourSetting,
        on_delete=models.CASCADE,
        related_name='credit_entries'
    )
    earned_credit_hours = models.DurationField()
    consumed_credit_hours = models.DurationField(
        null=True,
        help_text="This tracks down which credit hour to consume first."
    )
    status = models.CharField(
        default=REQUESTED,
        max_length=30,
        choices=STATUS_CHOICES,
        db_index=True
    )
    is_archived = models.BooleanField(null=True, )

    def __str__(self):
        return "Entry: {} -> {}".format(
            self.timesheet,
            self.earned_credit_hours
        )


class CreditHourDeleteRequest(ApprovalModelMixin):
    status = models.CharField(
        default=REQUESTED,
        max_length=30,
        choices=CREDIT_HOUR_STATUS_CHOICES,
        db_index=True
    )
    request = models.ForeignKey(
        to=CreditHourRequest,
        related_name='delete_requests',
        on_delete=models.CASCADE
    )


class CreditHourDeleteRequestHistory(BaseModel):
    delete_request = models.ForeignKey(
        to=CreditHourDeleteRequest,
        related_name='histories',
        on_delete=models.CASCADE
    )
    action_performed = models.CharField(
        max_length=30,
        choices=CREDIT_HOUR_STATUS_CHOICES,
        db_index=True
    )
    remarks = models.CharField(
        max_length=255
    )
    action_performed_by = models.ForeignKey(
        to=USER,
        related_name='+',
        on_delete=models.CASCADE
    )
    action_performed_to = models.ForeignKey(
        to=USER,
        related_name='+',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return " ".join([
            self.action_performed_by.full_name,
            self.action_performed,
            self.action_performed_to.full_name,
        ])
