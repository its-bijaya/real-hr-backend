"""@irhrs_docs
TimeSheet related utils
"""
from datetime import date
from dateutil import rrule

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction

from irhrs.attendance.constants import WORKDAY, UNCLAIMED, DAILY
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.models import WorkShift, TimeSheet, OvertimeClaim
from irhrs.attendance.models.shift_roster import TimeSheetRoster
from irhrs.attendance.tasks.overtime import generate_overtime
from irhrs.attendance.utils.helpers import get_weekday
from irhrs.core.utils import nested_getattr, get_system_admin
from irhrs.core.utils.common import get_today
from irhrs.leave.constants.model_constants import COMPENSATORY, DEDUCTED
from irhrs.leave.models.account import LeaveAccountHistory

USER = get_user_model()


def simulate_timesheets(
    user: USER, work_shift: WorkShift,
    start_date: date, end_date: date,
    ignore_holidays: bool = False
) -> dict:
    """
    Simulate time sheets of user for given date range
    :param user: User instance
    :param work_shift: Work shift used to simulate
    :param start_date: start date of simulation
    :param end_date: end date of simulation
    :param ignore_holidays: Ignore holidays or not
        ( If true, Holiday status will not be sent and counted as workday )
    :return:

         {
             '2018-01-01': 'Workday',
             '2018-01-02': 'Offday',
             '2019-01-02': 'Holiday'
         }
    """

    assert isinstance(start_date, date)
    assert isinstance(end_date, date)

    dates = list(rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date))

    # can not consider applicable from as shift may not exist for these dates
    # so taking currently applicable days
    work_days = list(work_shift.work_days.applicable().values_list('day', flat=True))

    return_dict = dict()

    for d in dates:
        if not ignore_holidays and user.is_holiday(d):
            return_dict[str(d)] = 'Holiday'
        elif get_weekday(d) in work_days:
            return_dict[str(d)] = 'Workday'
        else:
            return_dict[str(d)] = 'Offday'

    return return_dict


def create_timesheet_roster_and_update_timesheet(user: USER, roster_data,
                                                 last_payroll_generated_date, error_msg):
    for data in roster_data:
        if last_payroll_generated_date and last_payroll_generated_date >= data['date']:
            cache.set('roster_errors', {f"{user}":error_msg})
            return
        work_shift = data['shift']
        date = data['date']
        TimeSheetRoster.objects.create(
            user=user,
            shift=work_shift,
            date=date
        )
        if date <= get_today():
            timesheet = user.timesheets.filter(timesheet_for=date).first()
            if timesheet:
                update_work_shift_in_timesheet(timesheet, work_shift)


def update_timesheet_rooster_and_time_sheet(timesheet_roster, work_shift: WorkShift):
    timesheet_roster.shift = work_shift
    timesheet_roster.save()
    if timesheet_roster.date <= get_today():
        timesheet = timesheet_roster.user.timesheets.filter(
            timesheet_for=timesheet_roster.date
        ).first()
        if timesheet:
            update_work_shift_in_timesheet(timesheet, work_shift)


class TimeSheetBaseMixin:
    def __init__(self, timesheet: TimeSheet):
        self.timesheet = timesheet
        self.timesheet_for = timesheet.timesheet_for
        self.user = timesheet.timesheet_user

    @property
    def existing_overtime_claim(self):
        return OvertimeClaim.objects.filter(
            overtime_entry__timesheet=self.timesheet,
            status=UNCLAIMED,
            is_archived=False
        ).first()

    @property
    def overtime_setting(self):
        return nested_getattr(self.timesheet, 'timesheet_user.attendance_setting.overtime_setting')

    @property
    def attendance_setting(self):
        return getattr(self.user, 'attendance_setting', None)


class OvertimeFixer(TimeSheetBaseMixin):
    def __init__(self, timesheet: TimeSheet):
        super().__init__(timesheet)

    def _generate_overtime(self):
        return generate_overtime(self.timesheet_for, self.timesheet_for, DAILY, fix_missing=True,
                                 fix_ids=[self.timesheet.id])

    @transaction.atomic()
    def update_existing_overtime_claim(self):
        if self.existing_overtime_claim and self.overtime_setting:
            self.existing_overtime_claim.overtime_entry.delete()
            self._generate_overtime()

    @transaction.atomic()
    def create_overtime_claim(self):
        if not self.existing_overtime_claim and self.overtime_setting:
            if not (self.timesheet.punch_out_delta and self.timesheet.punch_in_delta):
                fix_entries_on_commit(self.timesheet, False)
            self._generate_overtime()

    def generate_overtime(self):
        self.update_existing_overtime_claim()
        self.create_overtime_claim()


class GenerateCompensatoryLeave(TimeSheetBaseMixin):
    def __init__(self, timesheet: TimeSheet):
        super().__init__(timesheet)

    def get_compensatory_leaves(self):
        if not self.attendance_setting:
            return []
        return self.user.leave_accounts.filter(
            is_archived=False,
            rule__leave_type__category=COMPENSATORY
        )

    def generate(self):
        if self.timesheet.coefficient == WORKDAY:
            return
        from irhrs.leave.tasks import add_compensatory_leave
        for leave_account in self.get_compensatory_leaves():
            add_compensatory_leave(leave_account, self.timesheet)


class RevertCompensatoryLeave(TimeSheetBaseMixin):
    def __init__(self, timesheet: TimeSheet):
        super().__init__(timesheet)

    def revert(self):
        from irhrs.leave.tasks import unchanged
        if self.timesheet.coefficient != WORKDAY:
            return
        compensatory_leaves = self.timesheet.compensatory_leave.all()
        if not compensatory_leaves:
            return
        for compensatory_leave in compensatory_leaves:
            leave_account = compensatory_leave.leave_account
            balance_to_deduct = compensatory_leave.balance_granted
            account_history = LeaveAccountHistory(
                account=leave_account,
                user=leave_account.user,
                actor=get_system_admin(),
                action=DEDUCTED,
                previous_balance=leave_account.balance,
                previous_usable_balance=leave_account.usable_balance,
                remarks=f"Deducted {balance_to_deduct} due to shift change on {self.timesheet_for}."
            )
            leave_account.balance -= balance_to_deduct
            leave_account.usable_balance -= balance_to_deduct
            account_history.new_usable_balance = leave_account.usable_balance
            account_history.new_balance = leave_account.balance
            if unchanged(account_history):
                return
            leave_account.save()
            account_history.save()
        self.timesheet.compensatory_leave.all().delete()


class GenerateOrRevertCompensatoryLeave(GenerateCompensatoryLeave, RevertCompensatoryLeave):
    def __init__(self, timesheet):
        super().__init__(timesheet)

    def run(self):
        self.generate()
        self.revert()


@transaction.atomic
def update_work_shift_in_timesheet(timesheet: TimeSheet, work_shift: WorkShift):
    weekday_mapper = {
        'Sunday': 1,
        'Monday': 2,
        'Tuesday': 3,
        'Wednesday': 4,
        'Thursday': 5,
        'Friday': 6,
        'Saturday': 7
    }
    timesheet.work_shift = work_shift
    timesheet.save()
    day_of_week = timesheet.timesheet_for.strftime("%A")
    work_day = work_shift.work_days.filter(day=weekday_mapper[day_of_week]).first()
    if work_day:
        work_timing = work_day.timings.first()
        # work_timing should be set to prevent multiple timesheet creation
        timesheet.work_time = work_timing
        timesheet.save()
        update_leave_request_while_updating_work_shift(timesheet)

    TimeSheet.objects._create_or_update_timesheet_for_profile(
        timesheet.timesheet_user,
        timesheet.timesheet_for
    )
    timesheet.refresh_from_db()
    timesheet.fix_entries()
    timesheet.title = timesheet.get_pretty_name
    timesheet.save()
    GenerateOrRevertCompensatoryLeave(timesheet).run()
    OvertimeFixer(timesheet).generate_overtime()


def update_leave_request_while_updating_work_shift(timesheet: TimeSheet):
    from irhrs.leave.utils.leave_request import leave_request_for_timesheet, get_shift_end, \
        get_shift_start
    leaves_that_day = leave_request_for_timesheet(
        timesheet, requested_only=False
    )
    if not leaves_that_day:
        return
    for leave in leaves_that_day:
        part = nested_getattr(leave, 'request.part_of_day')
        if not part:
            continue
        request = leave.request
        start = get_shift_start(timesheet.timesheet_user, timesheet.timesheet_for, part)
        end = get_shift_end(timesheet.timesheet_user, timesheet.timesheet_for, part)
        leave.start = start
        leave.end = end
        leave.save()
        request.start = start
        request.end = end
        request.save()
