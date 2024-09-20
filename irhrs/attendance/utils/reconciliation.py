from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Q

from irhrs.attendance.constants import SYNC_PENDING, SYNC_FAILED
from irhrs.attendance.models.cache import AttendanceEntryCache
from irhrs.attendance.models.attendance import AttendanceUserMap, IndividualAttendanceSetting
from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.attendance.utils.break_in_break_out import get_total_lost


def get_attendance_entries_for_given_timesheet(timesheet):
    user = timesheet.timesheet_user
    setting = IndividualAttendanceSetting.objects.filter(user=user).first()
    if not setting:
        return []
    user_map_qs = AttendanceUserMap.objects.filter(setting=setting)
    logs = []
    for user_map in user_map_qs:
        logs += list(AttendanceEntryCache.objects.filter(
            timestamp__date=timesheet.timesheet_for,
            bio_id=user_map.bio_user_id,
            source=user_map.source
        ).values_list('timestamp__time', flat=True))
    return logs


def has_unsynced_attendance_entries(timesheet):
    user = timesheet.timesheet_user
    setting = getattr(user, 'attendance_setting', None)
    if not setting:
        return True
    user_map_qs = AttendanceUserMap.objects.filter(setting=setting)

    attendance_entry_qs = AttendanceEntryCache.objects.filter(
        timestamp__date=timesheet.timesheet_for,
        bio_id__in=user_map_qs.values_list('bio_user_id', flat=True),
        source__id__in=user_map_qs.values_list('source', flat=True),
        reason__in=[SYNC_PENDING, SYNC_FAILED]
    )

    if attendance_entry_qs:
        return True

    if not timesheet.timesheet_entries.filter(is_deleted=False).exists():
        return True
    return False


def get_late_in_from_timesheet(timesheet, humanized=False):
    late_in = max(int(timesheet.late_in.total_seconds()), 0) if timesheet.late_in else 0
    if humanized:
        return humanize_interval(late_in)[:-3]
    return late_in


def get_early_out_from_timesheet(timesheet, humanized=False):
    early_out = max(int(timesheet.early_out.total_seconds()), 0) if timesheet.early_out else 0
    if getattr(settings, "IGNORE_SECOND_IN_TOTAL_LOST_HOURS", False):
        if early_out % 60 > 0:
            early_out += 60
    if humanized:
        return humanize_interval(early_out)[:-3]
    return early_out

def get_total_lost_hours_from_timesheet(timesheet):
    early_out = max(get_early_out_from_timesheet(timesheet), 0)
    late_in = max(get_late_in_from_timesheet(timesheet), 0)
    total_lost_hours = early_out + late_in
    return humanize_interval(total_lost_hours)[:-3]

def break_in_out_lost_hour(instance):
    queryset = instance.timesheet_entries.filter(
            Q(entry_type='Break In') | Q(entry_type='Break Out')
        )
    return get_total_lost(queryset)


def get_ktm_time(time):
    if time:
        dummy_date = datetime(2023, 1, 1)
        dummy_datetime = datetime.combine(dummy_date, time)
        result_datetime = dummy_datetime + timedelta(hours=5, minutes=45)
        return result_datetime.time()
    else:
        return None
