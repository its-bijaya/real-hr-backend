import datetime

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import Q, Prefetch
from django.utils import timezone
from django.utils.functional import cached_property

from irhrs.attendance.constants import (
    WORKDAY, TIMESHEET_COEFFICIENTS, TIMESHEET_ENTRY_METHODS,
    TIMESHEET_ENTRY_TYPES, TIMESHEET_ENTRY_CATEGORIES, PUNCH_IN, PUNCH_OUT,
    UNCATEGORIZED, WORKING_HOURS_DURATION_CHOICES,
    TIMESHEET_ENTRY_REMARKS, OTHERS, LEAVE_COEFFICIENTS, NO_LEAVE,
    OFFDAY, HOLIDAY, HOUR_OFF_COEFFICIENT, ATTENDANCE_APPROVAL_STATUS_CHOICES, REQUESTED)
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.utils.helpers import get_weekday
from irhrs.attendance.utils.validators import validate_CIDR
from irhrs.common.models import BaseModel
from irhrs.core.utils.common import get_today
from irhrs.core.validators import MinMaxValueValidator
from .source import AttendanceSource
from .workshift import WorkShift, WorkTiming, WorkDay
from ..managers.timesheet import TimeSheetManager

# from ..utils.shift_planner import get_shift_for_user

USER = get_user_model()


def get_tomorrows_date():
    return (timezone.now() + timezone.timedelta(days=1)).date()


class IndividualAttendanceSetting(BaseModel):
    user = models.OneToOneField(
        to=USER, on_delete=models.CASCADE, related_name='attendance_setting'
    )

    web_attendance = models.BooleanField(default=False)

    late_in_notification_email = models.BooleanField(default=False)
    absent_notification_email = models.BooleanField(default=False)
    weekly_attendance_report_email = models.BooleanField(default=False)

    # Subjected to removal [Overtime to be tested with OT setting, the flag seems
    enable_overtime = models.BooleanField(default=False)
    overtime_remainder_email = models.BooleanField(default=False)

    overtime_setting = models.ForeignKey(
        to='attendance.OvertimeSetting',
        related_name='individual_settings',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    enable_credit_hour = models.BooleanField(default=False)
    credit_hour_setting = models.ForeignKey(
        to='attendance.CreditHourSetting',
        related_name='individual_settings',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    penalty_setting = models.ForeignKey(
        to='attendance.BreakOutPenaltySetting',
        related_name='individual_settings',
        on_delete=models.SET_NULL,
        null=True
    )

    is_disabled = models.BooleanField(default=False)
    enable_hr_notification = models.BooleanField(default=False)
    enable_supervisor_notification = models.BooleanField(default=False)
    enable_approval = models.BooleanField(default=False)

    def __str__(self):
        return f"Attendance Setting: {self.user}"

    @property
    def work_shift(self):
        _date_time_for_work_shift = getattr(
            self,
            'force_work_shift_for_date',
            timezone.now().astimezone().date()
        )

        fil = Q(
            applicable_from__lte=_date_time_for_work_shift) & Q(
            Q(
                applicable_to__gte=_date_time_for_work_shift
            ) | Q(
                applicable_to__isnull=True
            )
        )
        if hasattr(self, 'force_prefetch_for_work_shift'):
            # days to prefetch
            days_ = [get_weekday(_date_time_for_work_shift)]

            # in case of extended shift we need to check for previous days last timing also
            if hasattr(self, 'force_prefetch_for_previous_day'):
                days_.append(get_weekday(
                    _date_time_for_work_shift - timezone.timedelta(days=1)))

            shifts_obj = self.individual_setting_shift.filter(
                fil
            ).select_related('shift').prefetch_related(
                Prefetch('shift__work_days',
                         queryset=WorkDay.objects.today().filter(
                             day__in=days_).prefetch_related(
                             Prefetch('timings', to_attr='work_times')
                         ), to_attr='days'),
            ).first()
            return shifts_obj.shift if shifts_obj else None
        else:
            shifts_obj = self.individual_setting_shift.filter(fil).first()
            return shifts_obj.shift if shifts_obj else None

    @work_shift.setter
    def work_shift(self, shift):
        if self.pk:
            if shift is None:
                self.individual_setting_shift.filter(applicable_to__isnull=True).update(applicable_to=get_today())
            elif shift == '':
                pass
            else:
                if self.individual_setting_working_hours.count() == 0 and self.individual_setting_shift.count() == 0:
                    set_to = today = get_today()
                    if TimeSheet.objects.filter(
                        timesheet_user=self.user,
                        timesheet_for=today,
                    ).exists():
                        set_to = get_tomorrows_date()
                    self.individual_setting_shift.create(shift=shift, applicable_from=set_to)
                elif (shift != self.work_shift) or self.working_hour:

                    # set all currently active settings effective till today
                    self.individual_setting_shift.filter(
                        applicable_to__isnull=True).update(
                        applicable_to=timezone.now())
                    self.individual_setting_working_hours.filter(
                        applicable_to__isnull=True).update(applicable_to=get_today())

                    self.individual_setting_shift.create(shift=shift)

    @property
    def working_hour(self):
        working_hours_for = get_today()

        fil = Q(
            applicable_from__lte=working_hours_for) & Q(
            Q(
                applicable_to__gte=working_hours_for
            ) | Q(
                applicable_to__isnull=True
            )
        )

        return self.individual_setting_working_hours.filter(fil).first()

    @working_hour.setter
    def working_hour(self, work_hour):
        """
        :param work_hour: A object with `working_hour`  and `working_hours_duration` attribute
        :return:
        """
        if self.pk:
            if work_hour is None:
                # Delete Case
                self.individual_setting_working_hours.filter(
                    applicable_to__isnull=True).update(
                    applicable_to=timezone.now()
                )
            else:
                if self.individual_setting_working_hours.count() == 0 and self.individual_setting_shift.count() == 0:
                    # if none exist update
                    self.individual_setting_working_hours.create(
                        working_hours=work_hour.working_hours,
                        working_hours_duration=work_hour.working_hours_duration,
                        applicable_from=get_today()
                    )
                elif ((
                          self.working_hour and
                          (
                              self.working_hour.working_hours != work_hour.working_hours or
                              self.working_hour.working_hours_duration != work_hour.working_hours_duration)
                      ) or self.work_shift):

                    # set all currently active settings effective till today
                    self.individual_setting_working_hours.filter(
                        applicable_to__isnull=True).update(applicable_to=get_today())
                    self.individual_setting_shift.filter(
                        applicable_to__isnull=True).update(
                        applicable_to=timezone.now())

                    self.individual_setting_working_hours.create(
                        working_hours=work_hour.working_hours,
                        working_hours_duration=work_hour.working_hours_duration,
                        applicable_from=get_today() + timezone.timedelta(days=1)
                    )

    @cached_property
    def working_hour_cache(self):
        """Cache working hour for property working_hours and working_hours_duration"""
        return self.working_hour

    @property
    def working_hours(self):
        return getattr(self.working_hour_cache, 'working_hours', None)

    @property
    def working_hours_duration(self):
        return getattr(self.working_hour_cache, 'working_hours_duration', None)

    def work_shift_for(self, date):
        from irhrs.attendance.utils.shift_planner import get_shift_for_user
        return get_shift_for_user(user=self.user, date_=date)
        # setattr(self, 'force_work_shift_for_date', date)
        # return self.work_shift

    def work_day_for(self, date):
        if isinstance(date, str):
            from dateutil.parser import parse as p
            _date = p(date)
        else:
            _date = date
        shift_for_this_day = self.work_shift_for(_date)
        if shift_for_this_day:
            weekday = get_weekday(_date)
            work_day = shift_for_this_day.work_days.filter(
                day=weekday,
            ).filter(
                Q(
                    applicable_from__lte=date,
                ) & Q(
                    Q(applicable_to__isnull=True) |
                    Q(applicable_to__gte=date)
                )
            ).first()
            return work_day
        return None


class IndividualUserShift(BaseModel):
    individual_setting = models.ForeignKey(
        IndividualAttendanceSetting,
        on_delete=models.CASCADE,
        related_name='individual_setting_shift'
    )
    shift = models.ForeignKey(
        to=WorkShift, on_delete=models.CASCADE,
        related_name='individual_shifts'
    )
    applicable_from = models.DateField(default=get_tomorrows_date)
    applicable_to = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.individual_setting} for shift {self.shift} " \
               f"from {self.applicable_from} to {self.applicable_to}"

    class Meta:
        ordering = '-created_at',


class IndividualWorkingHour(BaseModel):
    individual_setting = models.ForeignKey(
        IndividualAttendanceSetting,
        on_delete=models.CASCADE,
        related_name='individual_setting_working_hours'
    )

    applicable_from = models.DateField(default=get_tomorrows_date)
    applicable_to = models.DateField(null=True, blank=True)

    working_hours = models.PositiveIntegerField()
    working_hours_duration = models.CharField(
        choices=WORKING_HOURS_DURATION_CHOICES,
        max_length=10,
        db_index=True
    )

    def __str__(self):
        return f"{self.individual_setting} for working hour {self.working_hours} {self.working_hours_duration}" \
               f"from {self.applicable_from} to {self.applicable_to}"

    class Meta:
        ordering = '-created_at',


class WebAttendanceFilter(models.Model):
    setting = models.ForeignKey(
        IndividualAttendanceSetting,
        related_name='ip_filters',
        on_delete=models.CASCADE
    )
    allow = models.BooleanField(default=True)
    cidr = models.CharField(max_length=18, validators=[validate_CIDR])

    class Meta:
        unique_together = ('setting', 'allow', 'cidr')

    def __str__(self):
        return f"{self.cidr} - {'Allow' if self.allow else 'Block'}"


class AttendanceUserMap(BaseModel):
    setting = models.ForeignKey(IndividualAttendanceSetting,
                                on_delete=models.CASCADE)
    bio_user_id = models.CharField(max_length=50)
    source = models.ForeignKey(AttendanceSource, on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('bio_user_id', 'source'),
            ('setting', 'source')
        )

    def __str__(self):
        return f"Attendance Map: {self.setting}"


class TimeSheet(BaseModel):
    manual_user = models.ForeignKey(
        to=USER, related_name='created_timesheets', null=True, blank=True,
        on_delete=models.SET_NULL
    )
    timesheet_user = models.ForeignKey(
        to=USER, related_name='timesheets', on_delete=models.CASCADE
    )
    work_shift = models.ForeignKey(
        to=WorkShift, on_delete=models.SET_NULL, related_name='timesheets',
        null=True, blank=True
    )
    work_time = models.ForeignKey(
        to=WorkTiming, on_delete=models.SET_NULL, null=True, blank=True
    )
    timesheet_for = models.DateField()
    coefficient = models.PositiveSmallIntegerField(
        choices=TIMESHEET_COEFFICIENTS, default=WORKDAY
    )
    expected_punch_in = models.DateTimeField(null=True, blank=True)
    punch_in = models.DateTimeField(null=True, blank=True)
    expected_punch_out = models.DateTimeField(null=True, blank=True)
    punch_out = models.DateTimeField(null=True, blank=True)
    worked_hours = models.DurationField(null=True, blank=True)
    unpaid_break_hours = models.DurationField(null=True, blank=True)
    punch_in_delta = models.DurationField(null=True, blank=True)
    punch_out_delta = models.DurationField(null=True, blank=True)

    is_present = models.BooleanField(default=False)
    leave_coefficient = models.CharField(
        max_length=20,
        choices=LEAVE_COEFFICIENTS,
        default=NO_LEAVE,
        db_index=True
    )
    hour_off_coefficient = models.CharField(
        max_length=20,
        choices=HOUR_OFF_COEFFICIENT,
        help_text='Indication of Time Off or Credit Hour Used.',
        blank=True,
        db_index=True
    )
    punctuality = models.FloatField(
        null=True
    )
    working_remotely = models.BooleanField(default=False)
    objects = TimeSheetManager()

    class Meta:
        unique_together = ('timesheet_user', 'work_shift', 'work_time', 'timesheet_for')

    def __str__(self):
        if self.leave_coefficient == NO_LEAVE:
            ret = f"{self.get_coefficient_display()} for "
        else:
            ret = f"{self.get_leave_coefficient_display()} for "
        return ret + f"{self.timesheet_user} on {self.timesheet_for}"

    @classmethod
    def get_for_user(cls, user, date_time):
        timesheet = cls.objects.get_timesheet(
            date_time, user)
        return timesheet

    @cached_property
    def attendance_category(self):
        # TODO @Ravi: Find a workaround.
        # Research on possible way out. [Filtered Relation works??]
        # Prefetched at irhrs.attendance.api.v1.views.attendance.TimeSheetViewSet
        punch_in = self._prefetched_timesheet_entries.filter(
            entry_type=PUNCH_IN).first() \
            if hasattr(self, '_prefetched_timesheet_entries') \
            else self.timesheet_entries.filter(is_deleted=False, entry_type=PUNCH_IN).first()
        punch_out = self._prefetched_timesheet_entries.filter(
            entry_type=PUNCH_OUT).first() \
            if hasattr(self, '_prefetched_timesheet_entries') \
            else self.timesheet_entries.filter(
            entry_type=PUNCH_OUT, is_deleted=False).first()
        category = (
            punch_in.category if punch_in else "Missing Punch In",
            punch_out.category if punch_out else "Missing Punch Out"
        )
        return "-".join(category)

    @cached_property
    def punch_in_category(self):
        punch_in = self._prefetched_timesheet_entries.filter(
            entry_type=PUNCH_IN).first() \
            if hasattr(self, '_prefetched_timesheet_entries') \
            else self.timesheet_entries.filter(is_deleted=False, entry_type=PUNCH_IN).first()
        return punch_in.category if punch_in else "Missing Punch In"

    @cached_property
    def punch_out_category(self):
        punch_out = self._prefetched_timesheet_entries.filter(
            entry_type=PUNCH_OUT).first() \
            if hasattr(self, '_prefetched_timesheet_entries') \
            else self.timesheet_entries.filter(is_deleted=False, entry_type=PUNCH_OUT).first()
        return punch_out.category if punch_out else "Missing Punch Out"

    @staticmethod
    def _get_date_from_any(dt):
        """
        takes either datetime or date and
        returns date object in local timezone
        :rtype: datetime.datetime
        """
        if type(dt) == datetime.datetime:
            # if its a datetime, convert it to date
            # but if it is on UTC, change it back to
            # localtime because shift start and end are expressed
            # in local time
            if dt.tzinfo == timezone.utc:
                dt = timezone.localtime(dt)
            dt = dt.date()
        return dt

    @property
    def day(self):
        return self.timesheet_for.strftime("%A")

    @staticmethod
    def _combined(date, time):
        """
        helper that combines, makes aware and returns an UTC
        version of given date and time
        :rtype: datetime.datetime
        """
        _dt = datetime.datetime.combine(date, time)
        _dt = timezone.make_aware(_dt)
        return _dt.astimezone(timezone.utc)

    def fix_entries(self, commit=True):
        # transaction.on_commit is required because if this is
        # running inside a transaction block during attendance sync, it could
        # find no Time Sheet Entries because they wouldn't have been committed
        if commit:
            # on commit takes a function that takes no arguments
            # hence, wrapping our function inside a lambda that itself takes
            # no argument but calls a function that takes an argument.
            transaction.on_commit(lambda: fix_entries_on_commit(self))
        else:
            self.fix_entries()

    # Useful for a string representation of time sheet in FE
    @cached_property
    def get_pretty_name(self):
        not_applicable_display = 'N/A'
        missing_display = 'Missing'

        if self.leave_coefficient != NO_LEAVE:
            from irhrs.leave.models import LeaveRequest
            leave = LeaveRequest.objects.filter(
                user=self.timesheet_user,
                start__date__lte=self.timesheet_for,
                end__date__gte=self.timesheet_for).first()
            if leave:
                _prefix = ''.join([x[0].upper() for x in
                                   self.leave_coefficient.split(' ')])
                return f'[{_prefix}] {leave.leave_rule.leave_type.name}'
            leave_part = self.get_leave_coefficient_display()
            return leave_part + ' Leave' \
                if 'leave' not in leave_part.lower() else leave_part
        else:
            def _entry_pretty_name(work_time):
                if self.timesheet_for < timezone.now().date():
                    return missing_display
                elif self.timesheet_for == timezone.now().date():
                    if work_time and timezone.now().time() > work_time:
                        return missing_display
                    else:
                        return not_applicable_display
                else:  # a future condition
                    return not_applicable_display

            if self.coefficient in [WORKDAY, OFFDAY]:
                if self.punch_in or self.punch_out:
                    _punch_in_part = "{} - ".format(
                        self.punch_in.astimezone().strftime('%X')
                    ) if self.punch_in else _entry_pretty_name(
                        self.work_time.start_time if self.work_time else None
                    )

                    _punch_out_part = "{}".format(
                        self.punch_out.astimezone().strftime('%X')
                    ) if self.punch_out else _entry_pretty_name(
                        self.work_time.end_time if self.work_time else None
                    )
                    return _punch_in_part + _punch_out_part

                if not self.is_present and self.coefficient != OFFDAY:
                    if self.timesheet_for < get_today():
                        return 'Absent'
                    elif self.timesheet_for == get_today():
                        if self.work_time and \
                                get_today(with_time=True).time() > \
                                self.work_time.start_time:
                            return 'Absent'
                        else:
                            pass
                    else:  # a future condition
                        return not_applicable_display
            elif self.coefficient == HOLIDAY:
                holidays = self.timesheet_user.holiday_for_date(
                    self.timesheet_for
                )
                if holidays:
                    return ','.join([h.name.upper() for h in holidays])

        return self.get_coefficient_display()

    def recalculate_is_present(self):
        """
        Recalculate is_present value
        Called after fix entries in timesheet entry soft delete
        """
        self.is_present = self.timesheet_entries.filter(is_deleted=False).exists()
        self.save()


class TimeSheetEntry(BaseModel):
    timesheet = models.ForeignKey(TimeSheet,
                                  related_name='timesheet_entries',
                                  on_delete=models.CASCADE)
    timestamp = models.DateTimeField(blank=False, null=False)
    entry_method = models.CharField(
        max_length=15, choices=TIMESHEET_ENTRY_METHODS, null=True, db_index=True
    )
    entry_type = models.CharField(
        max_length=15, choices=TIMESHEET_ENTRY_TYPES, null=True, db_index=True
    )
    category = models.CharField(
        max_length=15, choices=TIMESHEET_ENTRY_CATEGORIES,
        default=UNCATEGORIZED, db_index=True
    )
    remark_category = models.CharField(
        max_length=30,
        choices=TIMESHEET_ENTRY_REMARKS,
        default=OTHERS,
        db_index=True
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    # location of entry
    latitude = models.FloatField(null=True, blank=True,
                                 validators=[MinMaxValueValidator(min_value=-90, max_value=90)])
    longitude = models.FloatField(null=True, blank=True,
                                  validators=[MinMaxValueValidator(min_value=-180, max_value=180)])

    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.timestamp}-{self.entry_method}"

    def soft_delete(self):
        self.is_deleted = True
        self.save()

        self.timesheet.punch_in = None
        self.timesheet.punch_out = None
        self.timesheet.punch_in_delta = None
        self.timesheet.punch_out_delta = None

        self.timesheet.punctuality = None
        self.timesheet.save()

        self.timesheet.fix_entries()

        self.timesheet.recalculate_is_present()

    def revert_soft_delete(self):
        self.is_deleted = False
        self.save()

        self.timesheet.fix_entries()
        self.timesheet.recalculate_is_present()
