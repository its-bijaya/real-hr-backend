from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models

from irhrs.attendance.managers.timesheet import OvertimeClaimManager
from irhrs.attendance.utils.overtime_utils import get_early_late_overtime, \
    get_off_day_overtime
from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.attendance.utils.validators import validate_daily_overtime_limit, \
    validate_off_day_overtime_limit, validate_overtime_delta, validate_weekly_overtime_limit, \
    validate_monthly_overtime_limit
from irhrs.common.models import SlugModel, BaseModel
from irhrs.core.utils import get_system_admin
from irhrs.core.validators import validate_title
from irhrs.attendance.models.attendance import TimeSheet
from irhrs.attendance.constants import STATUS_CHOICES, OVERTIME_CALCULATION_CHOICES, \
    OVERTIME_RATE_CHOICES, OT_WORKDAY, WORKDAY, OFFDAY, OT_HOLIDAY, \
    HOLIDAY, OT_OFFDAY, OT_LEAVE, FULL_LEAVE, FIRST_HALF, SECOND_HALF, NO_LEAVE, \
    UNCLAIMED, DECLINED, OVERTIME_APPLICATION_AFTER_CHOICES, \
    OVERTIME_AFTER_COMPENSATORY, GENERATE_BOTH, BOTH, NEITHER, \
    EXPIRATION_CHOICES, OVERTIME_REDUCTION_CHOICES, DAYS, DURATION_UNIT_CHOICES

USER = get_user_model()
UNLIMITED_HRS = 24 * 60 * 60
UNLIMITED_MINUTES = UNLIMITED_HRS * 60
UNLIMITED_SECONDS = UNLIMITED_MINUTES * 60


class OvertimeSetting(BaseModel, SlugModel):
    organization = models.ForeignKey(
        to='organization.Organization',
        related_name='overtime_settings',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=150,
        validators=[validate_title]
    )
    daily_overtime_limit_applicable = models.BooleanField(null=True,
        help_text='Flag for daily_overtime_limit is applicable in system.'
    )
    daily_overtime_limit = models.PositiveSmallIntegerField(
        validators=[validate_daily_overtime_limit],
        null=True,
        help_text='Usage: A employee can not work more than 3 hrs overtime in any day.'
    )
    weekly_overtime_limit_applicable = models.BooleanField(null=True,
        help_text='Flag for weekly_overtime_limit is applicable in system.'
    )
    weekly_overtime_limit = models.PositiveSmallIntegerField(
        validators=[validate_weekly_overtime_limit],
        null=True,
        help_text='Usage: A employee can not work more than 10 hrs overtime in any week.'
    )
    monthly_overtime_limit_applicable = models.BooleanField(null=True,
        help_text='Flag for monthly_overtime_limit is applicable in system.'
    )
    monthly_overtime_limit = models.PositiveSmallIntegerField(
        validators=[validate_monthly_overtime_limit],
        null=True,
        help_text='Usage: A employee can not work more than 40 hrs overtime in any month.'
    )
    off_day_overtime = models.BooleanField(default=False)
    off_day_overtime_limit = models.PositiveSmallIntegerField(
        validators=[validate_off_day_overtime_limit],
        null=True
    )
    applicable_before = models.PositiveSmallIntegerField(
        validators=[validate_overtime_delta]
    )
    applicable_after = models.PositiveSmallIntegerField(
        validators=[validate_overtime_delta]
    )

    overtime_calculation = models.PositiveSmallIntegerField(
        choices=OVERTIME_CALCULATION_CHOICES
    )
    paid_holiday_affect_overtime = models.BooleanField(default=True)
    holiday_overtime_limit = models.PositiveSmallIntegerField(
        validators=[validate_off_day_overtime_limit],
        null=True
    )
    leave_affect_overtime = models.BooleanField(default=True)
    leave_overtime_limit = models.PositiveSmallIntegerField(
        validators=[validate_off_day_overtime_limit],
        null=True
    )
    is_archived = models.BooleanField(default=False)

    overtime_applicable_only_after = models.CharField(
        max_length=20,
        choices=OVERTIME_APPLICATION_AFTER_CHOICES,
        default=BOTH,
        db_index=True
    )  # EITHER, BOTH

    deduct_overtime_after_for = models.CharField(
        max_length=20,
        choices=OVERTIME_REDUCTION_CHOICES,
        default=NEITHER,
        help_text='Generate overtime to calculate only after criteria deducted',
        db_index=True
    )  # If `True`: 16 mins will calculate 1 min; if `False`, will generate 16

    overtime_after_offday = models.CharField(
        max_length=20,
        db_column='overtime_compensatory',
        help_text='Deduct the hours consumed by compensatory leave and '
                  'generate overtime',
        choices=OVERTIME_AFTER_COMPENSATORY,
        default=GENERATE_BOTH,
        db_index=True
    )

    overtime_after_holiday = models.CharField(
        max_length=20,
        db_column='overtime_holiday',
        help_text='Deduct the hours consumed by compensatory leave and '
                  'generate overtime for holiday.',
        choices=OVERTIME_AFTER_COMPENSATORY,
        default=GENERATE_BOTH,
        db_index=True
    )

    # applied
    require_dedicated_work_time = models.BooleanField(
        db_column='dedicated_required',
        help_text='If `ON`: Late-in, Late-out may not generate OT. Check only '
                  'if the user must work dedicated minutes in his/her shift.',
        default=True
    )

    flat_reject_value = models.PositiveSmallIntegerField(
        help_text='The total overtime less than this value will be rejected',
        default=0
    )

    claim_expires = models.BooleanField(default=False)
    expires_after = models.PositiveSmallIntegerField(null=True)
    expires_after_unit = models.CharField(
        max_length=1,
        choices=EXPIRATION_CHOICES,
        blank=True,
        db_index=True
    )

    require_prior_approval = models.BooleanField(null=True,
        help_text="Prior Approval is a flag to ignore overtime from being created by default. "
                  "Settings with this flag will be excluded from default logic of creating overtime."
    )
    require_post_approval_of_pre_approved_overtime = models.BooleanField(null=True,
        db_column='require_post_approval',
        help_text='If Enabled: pre-approved overtime have to be Requested/Approved again.'
                  'If Disabled: generated overtime min(allowed, earned) shall automatically be approved.'
    )
    grant_compensatory_time_off_for_exceeded_minutes = models.BooleanField(null=True,
        db_column='compensatory_time_off',
        help_text="If enabled; will grant exceeded overtime to CompensatoryTimeOff."
    )
    reduce_ot_if_actual_ot_lt_approved_ot = models.BooleanField(null=True,
        db_column='min_worked_approved',
        help_text="Expanded: Reduce Overtime If Actual Overtime is Less Than Approved Overtime."
                  " FUNC: MIN(worked_hours, approved_hours)"
    )
    actual_ot_if_actual_gt_approved_ot = models.BooleanField(null=True,
        db_column='max_worked_approved',
        help_text="Expanded: Actual Overtime If Actual Overtime is greater Than Approved Overtime."
                  "FUNC: MAX(worked_hours, approved_hours)"
    )
    allow_edit_of_pre_approved_overtime = models.BooleanField(null=True,
        db_column='editable_pre_approved_overtime',
        help_text="If ON; Allows Pre Approved OT to be edited and re-flowed."
                  "If OFF; Pre Approved OT is Finalized."
    )
    minimum_request_duration = models.DurationField(
        null=True,
        help_text="Requests below this limit can not be requested."
    )
    # Change Request [#2845: Option to define overtime slots.]
    calculate_overtime_in_slots = models.BooleanField(null=True,
        help_text="Allow users to define slots in Overtime Setting?"
    )
    slot_duration_in_minutes = models.PositiveSmallIntegerField(
        null=True,
        help_text="The slots for overtime calculation in minutes."
    )
    slot_behavior_for_remainder = models.CharField(
        max_length=10,
        blank=True,
        choices=(
            ('up', 'up'),
            ('down', 'down'),
            ('const', 'constant'),
        ),
        db_index=True
    )

    def __str__(self):
        return f"OT Setting {self.name} " \
               f"{'Active' if not self.is_archived else 'Archived'}"

    @property
    def editable(self):
        # not editable if it is being used in Settings or Overtime Entries.
        being_used = self.individual_settings.exists(
        ) or self.overtimeentry_set.exists()
        return not being_used


class OvertimeRate(models.Model):
    """
    applicable_from is `created` field
    applicable_to is `date field for today`
    """
    overtime_settings = models.ForeignKey(OvertimeSetting, related_name='rates',
                                          on_delete=models.CASCADE)
    overtime_after = models.PositiveSmallIntegerField()
    rate = models.FloatField()
    rate_type = models.CharField(choices=OVERTIME_RATE_CHOICES, max_length=25, default=OT_WORKDAY,
                                 db_index=True)

    def __str__(self):
        return f'Overtime Rate for {self.overtime_settings}'


class OvertimeEntry(BaseModel):
    user = models.ForeignKey(
        to=USER, related_name='overtime_entries',
        on_delete=models.CASCADE
    )
    overtime_settings = models.ForeignKey(OvertimeSetting,
                                          on_delete=models.CASCADE)
    timesheet = models.OneToOneField(TimeSheet, on_delete=models.CASCADE,
                                     related_name='overtime')

    def __str__(self):
        return f"{self.user} {self.timesheet.timesheet_for} " \
               f"early->{self.overtime_detail.punch_in_overtime}" \
               f"late->{self.overtime_detail.punch_out_overtime}"


class OvertimeEntryDetail(BaseModel):
    punch_in_overtime = models.DurationField()
    punch_out_overtime = models.DurationField()
    claimed_overtime = models.DurationField(null=True)
    normalized_overtime = models.DurationField(null=True)
    overtime_entry = models.OneToOneField(
        to=OvertimeEntry, on_delete=models.CASCADE,
        related_name='overtime_detail'
    )

    def __str__(self):
        return f"Early : {self.punch_in_overtime} | Late : " \
               f"{self.punch_out_overtime}| Claimed: {self.claimed_overtime}"

    def recalibrate(self, remarks=''):
        # Do not use this method. Use recalibrate from OvertimeClaim instead.
        # Recalibrate overtime entry detail after the adjustment has been
        # approved.
        # The Overtime claim must be in `Unclaimed` or `Declined` state.
        # UPDATE: If this detail has pre_approval, this isn't mean to be re-calibrated.
        if getattr(self.overtime_entry, 'pre_approval', None):
            return False, "Overtime belonging to Pre Approval won't be re-calibrated."
        old_punch_in = self.punch_in_overtime
        old_punch_out = self.punch_out_overtime
        old_claimable = self.claimed_overtime
        timesheet = self.overtime_entry.timesheet
        setting = self.overtime_entry.overtime_settings

        if timesheet.coefficient == WORKDAY:
            new_punch_in, new_punch_out = get_early_late_overtime(
                timesheet,
                setting
            )
            claimable = self.get_claimable_overtime(format=False)
            # if same with previous, ignore.
            if (
                    old_punch_in == new_punch_in
                    and old_punch_out == new_punch_out
                    and old_claimable == timedelta(seconds=int(claimable))
            ):
                return False, "Overtime was equal"
            self.histories.create(
                actor=get_system_admin(),
                previous_punch_in_overtime=old_punch_in,
                previous_punch_out_overtime=old_punch_out,
                current_punch_in_overtime=new_punch_in,
                current_punch_out_overtime=new_punch_out,
                remarks=remarks
            )
            self.punch_in_overtime = new_punch_in
            self.punch_out_overtime = new_punch_out
            self.claimed_overtime = timedelta(
                seconds=self.get_claimable_overtime(format=False)
            )
            self.normalized_overtime = timedelta(
                seconds=self.normalized_overtime_seconds
            )
            self.save()
            return True, "Overtime re-calibrated"
        else:
            ot_setting = self.overtime_entry.overtime_settings
            new_overtime = get_off_day_overtime(
                timesheet=timesheet,
                overtime_setting=ot_setting
            )
            new_punch_out_overtime = timedelta(seconds=0)
            claimable = self.get_claimable_overtime(format=False)
            if new_overtime == old_punch_in and old_claimable == claimable:
                return False, "Overtime was same"
            self.histories.create(
                actor=get_system_admin(),
                previous_punch_in_overtime=old_punch_in,
                previous_punch_out_overtime=old_punch_out,
                current_punch_in_overtime=new_overtime,
                current_punch_out_overtime=new_punch_out_overtime,
                remarks=remarks
            )
            self.punch_in_overtime = new_overtime
            self.punch_out_overtime = new_punch_out_overtime
            self.claimed_overtime = timedelta(
                seconds=self.get_claimable_overtime(format=False)
            )
            self.normalized_overtime = timedelta(
                seconds=self.normalized_overtime_seconds
            )
            self.save()
            return True, "Overtime was re-calibrated."

    @staticmethod
    def normalize_seconds_with_rate(instance, worked_overtime,
                                    rate_coefficient, trail=False):
        steps = []
        initial_overtime = worked_overtime
        timesheet = instance.overtime_entry.timesheet
        if worked_overtime < 1:
            return 0
        rates = instance.overtime_entry.overtime_settings.rates.filter(
            rate_type=rate_coefficient
        ).order_by(
            '-overtime_after'
        )
        if rates:
            normalized = 0
            parsed_rates = list()
            for r in rates:
                ot_after = r.overtime_after * 60 * 60
                # Because rates is defined as per hour, and overtime is
                # processed in seconds.
                if ot_after in parsed_rates:
                    # this check will exclude future applicable rates.
                    continue
                if ot_after > worked_overtime:
                    continue
                seconds_applicable = worked_overtime - ot_after
                if seconds_applicable <= 0:
                    continue
                session = r.rate * seconds_applicable
                normalized += session
                worked_overtime -= seconds_applicable
                parsed_rates.append(r.overtime_after)
                steps.append([
                    humanize_interval(seconds_applicable),
                    r.overtime_after,
                    humanize_interval(session),
                    r.rate
                ])
            if worked_overtime > 0:
                if 0 not in parsed_rates:
                    steps.append([
                        humanize_interval(worked_overtime),
                        0,
                        humanize_interval(worked_overtime),
                        1
                    ])
                normalized = normalized + worked_overtime
        else:
            steps.append([
                humanize_interval(worked_overtime),
                0, humanize_interval(worked_overtime), 1
            ])
            normalized = worked_overtime
        if trail:
            header = ['worked', 'rate_begin', 'normalized', 'rate']
            return {
                'steps': reversed([dict(zip(header, step)) for step in steps]),
                'total_overtime': humanize_interval(initial_overtime),
                'normalized': humanize_interval(normalized)
            }
        return normalized

    @property
    def total_seconds(self):
        instance = self
        early_ot = instance.punch_in_overtime
        late_ot = instance.punch_out_overtime

        ot_1 = early_ot.total_seconds() if early_ot else 0
        ot_2 = late_ot.total_seconds() if late_ot else 0

        total_seconds = ot_1 + ot_2
        return int(total_seconds)

    def get_normalized_overtime_early(self, trail=False):
        timesheet = self.overtime_entry.timesheet
        if timesheet.leave_coefficient != FIRST_HALF:
            coefficient_mapper = {
                WORKDAY: OT_WORKDAY,
                OFFDAY: OT_OFFDAY,
                HOLIDAY: OT_HOLIDAY
            }
            rate_coefficient = coefficient_mapper.get(timesheet.coefficient)
        else:
            rate_coefficient = OT_LEAVE
        worked_overtime = self.punch_in_overtime.total_seconds() or 0
        return self.normalize_seconds_with_rate(
            self,
            worked_overtime,
            rate_coefficient,
            trail=trail
        )

    @property
    def normalized_overtime_early(self):
        return self.get_normalized_overtime_early()

    def get_normalized_overtime_late(self, trail=False):
        timesheet = self.overtime_entry.timesheet
        if timesheet.leave_coefficient != SECOND_HALF:
            coefficient_mapper = {
                WORKDAY: OT_WORKDAY,
                OFFDAY: OT_OFFDAY,
                HOLIDAY: OT_HOLIDAY
            }
            rate_coefficient = coefficient_mapper.get(timesheet.coefficient)
        else:
            rate_coefficient = OT_LEAVE
        worked_overtime = self.punch_out_overtime.total_seconds() or 0
        return self.normalize_seconds_with_rate(
            self,
            worked_overtime,
            rate_coefficient,
            trail=trail
        )

    @property
    def normalized_overtime_late(self):
        return self.get_normalized_overtime_late()

    @property
    def normalized_overtime_seconds(self):
        return self.get_normalized_overtime_seconds()

    def get_normalized_overtime_seconds(self, trail=False):
        # Generate Normalized Overtime for cases except Half Leave and Overtime.
        # Else generate values in a single shot.
        instance = self
        timesheet = instance.overtime_entry.timesheet
        # Generating Normalized overtime for Claimed OT, that does not exceed
        #  the limit defined in settings INITIALLY, can be altered later.
        if timesheet.leave_coefficient in [FIRST_HALF, SECOND_HALF]:
            if trail:
                return {
                    'total': None,
                    'early': self.get_normalized_overtime_early(trail=True),
                    'late': self.get_normalized_overtime_late(trail=True)
                }
            return (
                self.normalized_overtime_early +
                self.normalized_overtime_late
            )
        else:
            if timesheet.leave_coefficient != FULL_LEAVE:
                coefficient_mapper = {
                    WORKDAY: OT_WORKDAY,
                    OFFDAY: OT_OFFDAY,
                    HOLIDAY: OT_HOLIDAY
                }
                rate_coefficient = coefficient_mapper.get(timesheet.coefficient)
            else:
                rate_coefficient = OT_LEAVE
            worked_overtime = instance.get_claimable_overtime(format=False)
            if trail:
                return {
                    'total': self.normalize_seconds_with_rate(
                        self,
                        worked_overtime,
                        rate_coefficient,
                        trail=True
                    ),
                    'early': None,
                    'late': None
                }
            return self.normalize_seconds_with_rate(
                self,
                worked_overtime,
                rate_coefficient,
            )

    def get_claimable_overtime(self, format=True):
        overtime_entry = self.overtime_entry
        overtime_setting = overtime_entry.overtime_settings
        leave = overtime_setting.leave_overtime_limit
        if overtime_entry.timesheet.leave_coefficient != NO_LEAVE:
            selected = leave
        else:
            selected = {
                HOLIDAY: overtime_setting.holiday_overtime_limit,
                OFFDAY: overtime_setting.off_day_overtime_limit,
                WORKDAY: overtime_setting.daily_overtime_limit
            }.get(overtime_entry.timesheet.coefficient)
        limit = (selected or UNLIMITED_MINUTES) * 60
        # multiplied by `60` because limit is in minutes
        generated = self.total_seconds
        if overtime_setting.actual_ot_if_actual_gt_approved_ot and generated > limit:
            ret = generated
        else:
            ret = int(min([limit, generated]))
        m, s = divmod(ret, 60)
        h, m = divmod(m, 60)
        return '{:d}:{:02d}:{:02d}'.format(h, m, s) if format else ret

    @property
    def claimable_overtime(self):
        return self.get_claimable_overtime()


class OvertimeEntryDetailHistory(BaseModel):
    detail = models.ForeignKey(
        to=OvertimeEntryDetail,
        related_name='histories',
        on_delete=models.CASCADE
    )
    actor = models.ForeignKey(
        to=USER,
        related_name='overtime_adjustments_performed',
        on_delete=models.CASCADE
    )
    previous_punch_in_overtime = models.DurationField()
    previous_punch_out_overtime = models.DurationField()
    current_punch_in_overtime = models.DurationField()
    current_punch_out_overtime = models.DurationField()
    remarks = models.CharField(max_length=200)

    def __str__(self):
        old_ot = (
                self.previous_punch_in_overtime
                + self.previous_punch_out_overtime
        )
        new_ot = (
                self.current_punch_in_overtime
                + self.current_punch_out_overtime
        )
        return f"{old_ot} -> {new_ot} performed by {self.actor}"


class OvertimeClaim(BaseModel):
    overtime_entry = models.OneToOneField(OvertimeEntry,
                                          on_delete=models.CASCADE,
                                          related_name='claim')
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, null=True,
        db_index=True
    )
    description = models.CharField(max_length=255)
    recipient = models.ForeignKey(
        to=USER,
        related_name='overtime_requests_received',
        on_delete=models.SET_NULL,
        null=True
    )
    is_archived = models.BooleanField(
        default=False
    )

    objects = OvertimeClaimManager()

    def __str__(self):
        return f"{self.overtime_entry.user} {self.status} {self.recipient}"

    def recalibrate(self, remarks=''):
        # The recalibrate in overtime entry detail is not to be used.
        # filter only unclaimed
        if self.status not in [UNCLAIMED, DECLINED]:
            return False, f"Overtime is in {self.get_status_display()} state."
        detail = self.overtime_entry.overtime_detail
        return detail.recalibrate(remarks=remarks)


class OvertimeClaimHistory(BaseModel):
    overtime = models.ForeignKey(
        OvertimeClaim,
        related_name='overtime_histories',
        on_delete=models.CASCADE
    )
    action_performed = models.CharField(
        max_length=15, choices=STATUS_CHOICES, db_index=True)
    action_performed_by = models.ForeignKey(
        to=USER, related_name='sent_overtimes',
        on_delete=models.CASCADE
    )
    action_performed_to = models.ForeignKey(
        to=USER, related_name='received_overtimes',
        on_delete=models.CASCADE
    )
    remark = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.action_performed_by} {self.action_performed} {self.action_performed_to}"
