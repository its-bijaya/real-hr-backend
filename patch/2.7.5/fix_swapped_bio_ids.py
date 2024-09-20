from django.db import transaction

from irhrs.attendance.constants import SYNC_PENDING, DONT_SYNC
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.models import TimeSheetEntry, TimeSheet, AttendanceEntryCache, AttendanceSource
from irhrs.attendance.tasks.timesheets import sync_attendance

user1_id = 6
user1_bio_id = '1048'

user2_id = 96
user2_bio_id = '1012'

# everything will be reprocessed after this date.
date_start = '2020-05-01T00:00+05:45'
date_until = '2020-10-31T00:00+05:45'
DEVICE = 'Device'


def empty_time_sheets():
    """
    Delete Existing TimeSheet Entries
    """
    time_sheets = TimeSheet.objects.filter(
        timesheet_user_id__in=[user1_id, user2_id],
    )
    uc=time_sheets.update(
        punch_in=None,
        punch_out=None,
        punch_in_delta=None,
        punch_out_delta=None,
        punctuality=None,
        is_present=False
    )
    print('Timesheet updated', uc)
    TimeSheetEntry.objects.filter(
        timesheet__in=time_sheets,
        entry_method=DEVICE
    ).delete()


def reprocess_attendance_entries():
    """
    Fake the attendance entries as SYNC_PENDING.
    All pending sync caches are processed with `pull_attendance` method.
    """
    uc = AttendanceEntryCache.objects.filter(
        bio_id__in=[user1_bio_id, user2_bio_id],
    ).filter(
        timestamp__range=(date_start, date_until)
    ).update(
        reason=SYNC_PENDING
    )
    print('Updated Count', uc)


def fix_entries_immediately(self):
    fix_entries_on_commit(self, send_notification=False)


TimeSheet.fix_entries = fix_entries_immediately


with transaction.atomic():
    empty_time_sheets()
    reprocess_attendance_entries()
    for device in AttendanceSource.objects.exclude(
        sync_method=DONT_SYNC
    ):
        handler = device.handler
        if handler:
            print('Sync Progress', device)
            sync_count = handler.sync(pull=False)
            print('Total Synced', sync_count)
        else:
            print('No Handler', device)
