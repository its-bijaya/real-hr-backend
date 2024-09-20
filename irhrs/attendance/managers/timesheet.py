import copy
import datetime
import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Manager, Q, QuerySet
from django.utils import timezone

from irhrs.attendance.constants import WORKDAY, HOLIDAY, OFFDAY, TYPE_UNKNOWN, \
    UNCATEGORIZED, OTHERS, REQUESTED
from irhrs.attendance.managers.utils import trim_timestamps
from irhrs.attendance.utils.attendance import get_timing_info
# from irhrs.attendance.utils.shift_planner import get_shift_for_user
from irhrs.core.utils.common import combine_aware

USER = get_user_model()

logger = logging.getLogger('irhrs.attendance.managers.timesheet')

user_filters = {
    'is_blocked': False,
    'is_active': True,
    'attendance_setting__isnull': False,
    'attendance_setting__is_disabled': False,
}


class TimeSheetManager(Manager):
    def create_timesheet(self, **kwargs):
        """method to create timesheet if all params are known"""
        return self.update_or_create(**kwargs)

    def present(self, *args, **kwargs):
        """
        Return a queryset containing present Timesheet objects.
        """
        return self.filter(*args, is_present=True, **kwargs)

    def on_holiday(self, **kwargs):
        """
        Return a queryset containing holiday Timesheet objects.
        """
        return self.filter(coefficient=HOLIDAY, **kwargs)

    def offday(self, **kwargs):
        """
        Return a queryset containing weekends Timesheet objects. E.g. Saturday
        """
        return self.filter(coefficient=OFFDAY, **kwargs)

    def irregular(self, **kwargs):
        """
        Returns a queryset containing Timesheets that need fixing.
        Filters can be provided as key value
        """
        return self.filter(
            Q(punchin__isnull=True) |
            Q(punchout__isnull=True) |
            Q(is_present=False),
            **kwargs)

    @staticmethod
    def _filter_valid_users():
        # Need to filter users properly here after strict finalizing of the settings
        profiles = USER.objects.all().current().filter(
            **user_filters
        ).select_related(
            'detail',
            'attendance_setting',
        )
        return profiles

    @staticmethod
    def _get_timing_info(dt, shift):
        """
        Return work timing and timesheet_for for given datetime and given shift
        """
        return get_timing_info(dt, shift)

    def _get_coefficient(self, user, date, work_shift=None):
        if user.is_holiday(date):
            coefficient = HOLIDAY
        elif user.is_offday(date):
            coefficient = OFFDAY
        else:
            coefficient = WORKDAY
        return coefficient

    def _create_or_update_timesheet_for_profile(self, user, date_):
        ''''
        This method will be used to
        create timesheets,
        Apply leave and holidays

        Create timesheets for every user on  daily basis
        If the user has requested leave we create timeshift for that day
        '''''
        created_count = 0
        updated_count = 0
        timesheets = []
        from irhrs.attendance.utils.shift_planner import get_shift_for_user
        shift = get_shift_for_user(user, date_)
        if not shift:
            return timesheets, created_count, updated_count, False
        try:
            day = shift.days[0]
        except IndexError:
            day = None
        if day:
            for time in day.work_times:
                coefficient = self._get_coefficient(user, date_)
                defaults = {
                    'coefficient': coefficient,
                    'expected_punch_in': combine_aware(
                        date_,
                        time.start_time
                    ),
                    'expected_punch_out': combine_aware(
                        date_ + timezone.timedelta(days=1),
                        time.end_time
                    ) if time.extends else combine_aware(
                        date_,
                        time.end_time
                    )
                }
                timesheet, created = self.update_or_create(
                    timesheet_for=date_,
                    timesheet_user=user,
                    work_time=time,
                    work_shift=shift,
                    defaults=defaults
                )
                timesheets.append(timesheet)

                if created:
                    created_count += 1
                else:
                    updated_count += 1
        else:
            defaults = {
                'coefficient': self._get_coefficient(user, date_)
            }
            timesheet, created = self.update_or_create(timesheet_for=date_,
                                                       timesheet_user=user,
                                                       work_shift=shift,
                                                       defaults=defaults)
            timesheets.append(timesheet)
            if created:
                created_count += 1
            else:
                updated_count += 1
        return timesheets, created_count, updated_count, True

    def create_timesheets(self, date=None):
        if not date:
            date = timezone.now().date()
        users = self._filter_valid_users()
        created_count = 0
        updated_count = 0
        failed_count = 0
        _user_count = users.count()
        for user in users:
            _, created, updated, status = self._create_or_update_timesheet_for_profile(
                user, date)
            if status:
                created_count += created
                updated_count += updated
            else:
                failed_count += 1
        return _user_count, created_count, updated_count, failed_count

    def get_timesheet(self, timestamp, user=None):
        if isinstance(user, USER):
            user_id = user.id
        elif isinstance(user, str):
            user_id = int(user)
        else:
            user_id = user
        user_specific_filter = copy.deepcopy(user_filters)
        user_specific_filter.update({'id': user_id})
        punched_dt = timestamp.astimezone()
        users = USER.objects.all().current().filter(
            **user_specific_filter
        ).select_related(
            'attendance_setting',
        )
        if not users:
            logger.info(
                'Couldnt find user instance with required filters for user_id {}'.format(user_id))
            # sometime found that the user may be blocked or something and it returns EmptyQueryset
            return None
        user_instance = users[0]
        from irhrs.attendance.utils.shift_planner import get_shift_for_user
        shift = get_shift_for_user(
            user, timestamp
        )
        if not shift:
            defaults = {
                'coefficient': WORKDAY,
                'is_present': True,
            }
            timesheet, _ = self.model.objects.update_or_create(
                timesheet_for=punched_dt,
                timesheet_user_id=user_id,
                defaults=defaults)
            return timesheet
        if shift.days:
            timing_info = self._get_timing_info(shift=shift, dt=timestamp)
            timing = timing_info.get(
                'timing'
            )
            expected_punch_in = expected_punch_out = None

            _timesheet_data = self.model.objects.filter(
                timesheet_user=user_instance,
                work_shift=shift,
                work_time=timing_info.get('timing'),
                timesheet_for=timing_info.get('date'),
            ).first()

            if not _timesheet_data:
                if timing:
                    expected_punch_in = combine_aware(
                        timing_info.get('date'),
                        timing.start_time
                    )
                    expected_punch_out = combine_aware(
                        timing_info.get('date') + timezone.timedelta(
                            # int(True) = 1
                            days=int(timing.extends)
                        ),
                        timing.end_time
                    )

                defaults = {
                    'is_present': True,
                    'coefficient': self._get_coefficient(user_instance,
                                                         timing_info.get(
                                                             'date')),
                    'expected_punch_in': expected_punch_in,
                    'expected_punch_out': expected_punch_out,
                }

                timesheet = self.model.objects.create(
                    timesheet_user=user_instance,
                    work_shift=shift,
                    work_time=timing_info.get('timing'),
                    timesheet_for=timing_info.get('date'),
                    **defaults
                )
            else:
                _timesheet_data.is_present = True
                _timesheet_data.coefficient = self._get_coefficient(
                    user_instance,
                    timing_info.get('date')
                )
                _timesheet_data.save()
                timesheet = _timesheet_data

            return timesheet
        else:
            defaults = {
                'coefficient': OFFDAY,
                'is_present': True,
            }
            timesheet, _ = self.model.objects.update_or_create(
                timesheet_for=timestamp,
                timesheet_user=user_instance,
                work_shift=shift,
                defaults=defaults)
            return timesheet

    def sync_attendance(self, user, timestamps, entry_method, **kwargs):
        if type(timestamps) == datetime.datetime:
            timestamps = [timestamps]
        valid_timestamps = trim_timestamps(timestamps)
        timesheets_generated = []
        for time in valid_timestamps:
            timesheet = self.get_timesheet(time.astimezone(), user)
            if timesheet:
                defaults = kwargs.copy()
                defaults.update({
                    'entry_method': entry_method,
                    'entry_type': TYPE_UNKNOWN,
                    'category': UNCATEGORIZED,
                })
                try:
                    timesheet.timesheet_entries.update_or_create(
                        timestamp=time,
                        defaults=defaults
                    )
                except MultipleObjectsReturned:
                    logger.error(
                        'Found MOR DB issue while trying to update_or_create timesheet entries for timesheet in sync_attendance',
                        exc_info=True)
                    timesheet.timesheet_entries.filter(timestamp=time).delete()
                    timesheet.timesheet_entries.create(timestamp=time,
                                                       **defaults)
                    logger.info(
                        'Deleted timesheet entries for timesheet and then created again with input entries due to MOR sync_attendance')
                timesheets_generated.append(timesheet)
            else:
                pass

        if not timesheets_generated:
            return False
        for i in timesheets_generated:
            i.fix_entries()
        return True

    def clock(self,
              user,
              date_time,
              entry_method,
              entry_type=TYPE_UNKNOWN,
              manual_user=None,
              remarks='',
              timesheet=None,
              remark_category=OTHERS,
              latitude=None,
              longitude=None,
              working_remotely=False,
              ):

        timesheet = timesheet or self.get_timesheet(date_time, user)
        if timesheet:
            if manual_user:
                timesheet.manual_user = manual_user
                timesheet.save(update_fields=['manual_user'])
            defaults = {
                'entry_method': entry_method,
                'entry_type': entry_type,
                'category': UNCATEGORIZED,
                'remark_category': remark_category,
                'latitude': latitude,
                'longitude': longitude,
                'is_deleted': False,  # if previously timesheet entry was deleted undo delete
            }
            try:
                timesheet.timesheet_entries.update_or_create(
                    timestamp=date_time,
                    defaults=defaults,
                    remarks=remarks
                )
            except MultipleObjectsReturned:
                timesheet.timesheet_entries.filter(timestamp=date_time).delete()
                timesheet.timesheet_entries.create(timestamp=date_time,
                                                   **defaults)
                logger.info(
                    'Deleted timesheet entries for timesheet and then created again with input entries due to MOR clock method')
            # todo @Ravi: Research on a better logic rather than re-processing all entries every time.
            # create a difference method which will handle the entry_type and doesnt process the
            # complex logic , for now process everything
            timesheet.fix_entries()
            timesheet.is_present = True
            timesheet.working_remotely = working_remotely
            timesheet.save()
            return timesheet
        return False

    def generate_approvals(self,
                           user,
                           date_time,
                           entry_method,
                           supervisor=None,
                           entry_type=TYPE_UNKNOWN,
                           timesheet=None,
                           remarks='',
                           remark_category=OTHERS,
                           latitude=None,
                           longitude=None,
                           working_remotely=False):
        timesheet = timesheet or self.get_timesheet(date_time, user)
        if timesheet:
            timesheet.working_remotely = working_remotely
            timesheet.save()
            defaults = {
                'entry_method': entry_method,
                'entry_type': entry_type,
                'category': UNCATEGORIZED,
                'remark_category': remark_category,
                'latitude': latitude,
                'longitude': longitude,
                'remarks': remarks,
                'recipient': supervisor
            }
            from irhrs.attendance.models import TimeSheetApproval
            timesheet_approval, created = TimeSheetApproval.objects.get_or_create(
                timesheet=timesheet
            )
            if not created:
                timesheet_approval.status = REQUESTED
                timesheet_approval.save()
            try:
                timesheet_approval.timesheet_entry_approval.update_or_create(
                    timestamp=date_time,
                    defaults=defaults
                )
            except MultipleObjectsReturned:
                timesheet_approval.timesheet_entry_approval.filter(timestamp=date_time).delete()
                timesheet_approval.timesheet_entry_approval.create(timestamp=date_time,
                                                                   **defaults)
                logger.info('Deleted timesheet entries for timesheet and then '
                            'created again with input entries due to MOR clock method')
            return timesheet

        return False

    # TODO: REFACTOR required .@Ravi
    # create a helper and place these helpers methods in utils or somewhere
    def _get_date_from_any(self, dt):
        if type(dt) == datetime.datetime:
            if dt.tzinfo == timezone.utc:
                dt = timezone.localtime(dt)
            dt = dt.date()
        return dt

    def _combined(self, date, time):
        _dt = datetime.datetime.combine(date, time)
        _dt = timezone.make_aware(_dt)
        return _dt.astimezone(timezone.utc)

    @staticmethod
    def get_coefficient(user, date):
        if user.is_holiday(date):
            return HOLIDAY
        elif user.is_offday(date):
            return OFFDAY
        else:
            return WORKDAY


class OvertimeClaimManager(Manager):
    def get_queryset(self):
        return QuerySet(
            self.model,
            using=self._db
        ).filter(
            overtime_entry__user__is_active=True
        )


class AttendanceAdjustmentManager(Manager):
    def get_queryset(self):
        return QuerySet(
            self.model,
            using=self._db
        ).filter(
            sender__is_active=True
        )
