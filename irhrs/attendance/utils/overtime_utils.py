import logging

from datetime import timedelta
from django.db.models import Subquery, OuterRef, F, Sum
from django.db.models.functions import Coalesce

from irhrs.attendance.constants import UNCLAIMED, APPROVED, NO_LEAVE, WORKDAY, HOLIDAY, FULL_LEAVE, \
    FIRST_HALF, SECOND_HALF, TIME_OFF, OFFDAY, BOTH, EITHER, PUNCH_IN_ONLY, PUNCH_OUT_ONLY, \
    NO_OVERTIME, GENERATE_AFTER_DEDUCTION, DECLINED, CANCELLED
from irhrs.attendance.managers.utils import get_total_unpaid_break_time
from irhrs.core.utils import nested_getattr
from irhrs.leave.models.rule import CompensatoryLeave

ZERO_OVERTIME = timedelta(minutes=0)

attendance_logger = logging.getLogger(__name__)
attendance_logger.addHandler(logging.StreamHandler())


def get_worked_minutes_for_timesheet(timesheet):
    """
    Returns the total minutes for a timesheet
    :param timesheet:
    :return: timedelta
    """
    punch_in = timesheet.punch_in
    punch_out = timesheet.punch_out
    if not all([punch_in, punch_out]):
        return timedelta(0)
    # return punch_out - punch_in
    return timesheet.worked_hours


class OvertimeTimesheet:

    def __init__(self, timesheet) -> None:
        self.timesheet = timesheet
        self.coefficient = timesheet.coefficient
        self.leave_coefficient = timesheet.leave_coefficient
        super().__init__()

    @property
    def shift_start(self):
        return self.timesheet.expected_punch_in.astimezone()
        # if self.leave_coefficient == FIRST_HALF:
        #     return self.leave.start + timedelta(
        #         minutes=self.half_day_work_time
        #     )
        # ts = self.timesheet
        # w_time = getattr(ts, 'work_time')
        # if w_time:
        #     return combine_aware(ts.timesheet_for, w_time.start_time)
        # attendance_logger.info(f'No Worktime for {self.timesheet}')
        # return None

    @property
    def shift_end(self):
        return self.timesheet.expected_punch_out.astimezone()
        # if self.leave_coefficient == SECOND_HALF:
        #     return self.leave.end - timedelta(
        #         minutes=self.half_day_work_time
        #     )
        # ts = self.timesheet
        # w_time = ts.work_time
        # which_day = ts.timesheet_for + timedelta(
        #     days=1
        # ) if (ts.work_time and ts.work_time.extends) else ts.timesheet_for
        # return combine_aware(which_day, w_time.end_time)

    @property
    def workday_work_time(self):
        timing = self.timesheet.work_time
        if timing:
            return timing.working_minutes
        return 0

    @property
    def half_day_work_time(self):
        return int(self.workday_work_time / 2)

    @property
    def leave(self):
        from irhrs.leave.models import LeaveRequest
        leave_for_the_day = LeaveRequest.objects.exclude(
            is_deleted=True
        ).filter(
            start__date=self.timesheet.timesheet_for,
            user=self.timesheet.timesheet_user
        ).first()
        return leave_for_the_day

    @property
    def timeoff_worktime(self):
        if self.leave:
            minutes_off = self.leave.end - self.leave.start
            return self.workday_work_time - int(
                minutes_off.total_seconds() / 60)
        return self.workday_work_time

    @property
    def expected_work_minutes(self):
        coefficient = self.coefficient if self.leave_coefficient == NO_LEAVE \
            else self.leave_coefficient
        expected = {
            WORKDAY: self.workday_work_time,
            HOLIDAY: 0,
            FULL_LEAVE: 0,
            FIRST_HALF: self.workday_work_time,
            SECOND_HALF: self.half_day_work_time,
            TIME_OFF: self.timeoff_worktime
        }
        return expected.get(coefficient)

    @property
    def worked_minutes(self):
        td = get_worked_minutes_for_timesheet(self.timesheet)
        return int(td.total_seconds() // 60)

    @property
    def early_overtime(self):
        timesheet = self.timesheet
        if not (timesheet.punch_in and self.shift_start):
            return ZERO_OVERTIME
        return self.shift_start - timesheet.punch_in.astimezone()

    @property
    def late_overtime(self):
        timesheet = self.timesheet
        if not (timesheet.punch_out and self.shift_end):
            return ZERO_OVERTIME
        return timesheet.punch_out.astimezone() - self.shift_end


def slot_trim_overtime(duration, overtime_setting):
    if not overtime_setting.calculate_overtime_in_slots:
        return duration

    def mod_operator(whole, part):
        return whole // part, whole % part

    slot_length_seconds = int(overtime_setting.slot_duration_in_minutes * 60)
    duration_seconds = int(duration.total_seconds())
    factor, remainder = mod_operator(duration_seconds, slot_length_seconds)
    if factor and remainder >= 0:
        slot_behavior = overtime_setting.slot_behavior_for_remainder
        if slot_behavior == 'up':
            return timedelta(seconds=slot_length_seconds * (factor + (1 if remainder else 0)))
        if slot_behavior == 'down':
            return timedelta(seconds=slot_length_seconds * factor)
        if slot_behavior == 'const':
            return duration
    return ZERO_OVERTIME


def get_early_late_overtime(timesheet, overtime_setting):
    """
    :param timesheet: for a day
    :param overtime_setting:  applicable setting
    :return: early and late overtime
    """
    # Assumption:: If Late In, Punch In delta will be negative
    # Assumption:: If Early In, Punch In delta will be positive
    # Assumption:: If Early Out, Punch Out Delta will be negative
    # Assumption:: If Late Out, Punch Out Delta will be positive

    # UPDATE: No more using Punch In Punch Out Delta from time sheet.
    # Will calculate Punch In Punch Out Delta on our own.

    # ADD: Check the coefficient before jumping here.
    if (
        timesheet.coefficient == WORKDAY
        and timesheet.leave_coefficient == FULL_LEAVE
    ) or (
        timesheet.coefficient in [OFFDAY, HOLIDAY]
    ):
        punch_out = timesheet.punch_out
        punch_in = timesheet.punch_in
        if not (punch_out and punch_in):
            return ZERO_OVERTIME, ZERO_OVERTIME
        return slot_trim_overtime(
            timedelta(
                seconds=int((punch_out - punch_in).total_seconds())
            ), overtime_setting
        ), ZERO_OVERTIME
    # unpaid_break_time = get_total_unpaid_break_time(timesheet)
    ot_sheet = OvertimeTimesheet(timesheet)
    punch_in_delta = ot_sheet.early_overtime or ZERO_OVERTIME
    punch_out_delta = ot_sheet.late_overtime or ZERO_OVERTIME

    early_overtime = max([punch_in_delta, ZERO_OVERTIME])
    late_overtime = max([punch_out_delta, ZERO_OVERTIME])

    # the compensatory flag is to be checked with `require_dedicated_work_time`
    is_compensatory_enabled = overtime_setting.require_dedicated_work_time
    if is_compensatory_enabled:

        if punch_in_delta and punch_in_delta < timedelta(0):
            late_overtime += punch_in_delta

        elif punch_out_delta and punch_out_delta < timedelta(0):
            early_overtime += punch_out_delta

        compensatory = timesheet.unpaid_break_hours
        if compensatory:
            # if early > compensatory, reduce from early only.
            if early_overtime >= compensatory:
                early_overtime = early_overtime - compensatory
            else:
                late_overtime = late_overtime - (compensatory - early_overtime)
                if late_overtime < ZERO_OVERTIME:
                    late_overtime = ZERO_OVERTIME
                early_overtime = ZERO_OVERTIME

    # Check the flag,  `overtime_applicable_only_after` flag here.
    # Reduce accordingly.
    applicable_before_after = overtime_setting.overtime_applicable_only_after

    # qualification criteria
    early_overtime_q = max([(early_overtime - timedelta(
        minutes=overtime_setting.applicable_before
    )), ZERO_OVERTIME])

    late_overtime_q = max([(late_overtime - timedelta(
        minutes=overtime_setting.applicable_after
    )), ZERO_OVERTIME])

    early_pass = True if early_overtime_q > ZERO_OVERTIME else False
    late_pass = True if late_overtime_q > ZERO_OVERTIME else False

    generate_early, generate_late = False, False
    if applicable_before_after == BOTH:
        if early_pass:
            generate_early = True
        if late_pass:
            generate_late = True

    elif applicable_before_after == EITHER:
        if early_pass or late_pass:
            generate_early = True
            generate_late = True

    early_final = early_overtime if generate_early else ZERO_OVERTIME
    late_final = late_overtime if generate_late else ZERO_OVERTIME

    ot_applicable_flag = overtime_setting.deduct_overtime_after_for

    if ot_applicable_flag:
        if ot_applicable_flag in [BOTH, PUNCH_IN_ONLY]:
            early_final = early_overtime_q
        if ot_applicable_flag in [BOTH, PUNCH_OUT_ONLY]:
            late_final = late_overtime_q
    return (
        slot_trim_overtime(early_final, overtime_setting),
        slot_trim_overtime(late_final, overtime_setting),
    )


def get_off_day_overtime(timesheet, overtime_setting):
    user = timesheet.timesheet_user
    punch_out = timesheet.punch_out
    punch_in = timesheet.punch_in
    if not (punch_out and punch_in):
        return ZERO_OVERTIME
    worked_time = punch_out - punch_in
    overtime = timedelta(seconds=worked_time.total_seconds())
    compensatory = user.leave_accounts.filter(
        rule__compensatory_rules__isnull=False
    ).first()
    if timesheet.coefficient in [OFFDAY, HOLIDAY]:
        if compensatory:
            # if compensatory: reduce
            if timesheet.coefficient == OFFDAY:
                reduction_scheme = getattr(
                    overtime_setting,
                    'overtime_after_offday'
                )
            else:
                reduction_scheme = getattr(
                    overtime_setting,
                    'overtime_after_holiday'
                )

            ot_seconds = overtime.total_seconds()
            compensatory_instance = compensatory.rule.compensatory_rules.filter(
                hours_in_off_day__lte=ot_seconds/60/60
            ).order_by('-balance_to_grant').first()
            if not compensatory_instance:
                if reduction_scheme == GENERATE_AFTER_DEDUCTION:
                    return ZERO_OVERTIME
                return timedelta(minutes=ot_seconds/60)

            hours_in_off = compensatory_instance.hours_in_off_day
            seconds_to_reduce = hours_in_off * 60 * 60
            if ot_seconds >= seconds_to_reduce:
                if reduction_scheme == NO_OVERTIME:
                    return ZERO_OVERTIME  # left for compensatory
                elif reduction_scheme == GENERATE_AFTER_DEDUCTION:
                    new = ot_seconds - seconds_to_reduce
                    overtime = timedelta(seconds=new)
    return slot_trim_overtime(overtime, overtime_setting)


def get_pre_approval_overtime_sum(sender, test_end, test_start):
    from irhrs.attendance.models import PreApprovalOvertime, OvertimeEntry

    base = PreApprovalOvertime.objects.filter(
        sender=sender,
        overtime_date__range=(test_start, test_end)
    ).exclude(
        status__in=[DECLINED, CANCELLED]
    )

    equivalent_earned = Subquery(OvertimeEntry.objects.filter(
        id=OuterRef('overtime_entry'),
        timesheet__timesheet_for=OuterRef('overtime_date')
    ).values('overtime_detail__claimed_overtime')[:1])
    base = base.annotate(
        earned_hours=Coalesce(
            equivalent_earned,
            F('overtime_duration'),
        )
    )
    existing_sum = base.aggregate(
        sum_of_requests=Sum('earned_hours')
    ).get('sum_of_requests')
    if not existing_sum:
        existing_sum = timedelta(0)
    return existing_sum
