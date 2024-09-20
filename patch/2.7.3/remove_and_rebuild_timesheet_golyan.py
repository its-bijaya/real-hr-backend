import itertools
import json
import os

from dateutil.parser import parse
from dateutil.rrule import DAILY, rrule
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Sum

from irhrs.attendance.constants import NO_LEAVE
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.models import TimeSheet, TimeSheetEntry

User = get_user_model()


def custom_fix_entries(self):
    fix_entries_on_commit(self, send_notification=False)


TimeSheet.fix_entries = custom_fix_entries

email_date_map = [
    ('asmit.t@golyanagro.com', '2020-07-16',),
    ('santosh.bishwakarma@ga.com', '2020-07-16',),
    ('hari.phuyal@ga.com', '2020-07-16',),
    ('som.g@golyanagro.com', '2020-08-31',),
    ('sita.sherpa@ga.com', '2020-07-16',),
    ('sunisha.sherpa@ga.com', '2020-07-17',),
    ('milan.sherpa@ga.com', '2020-07-18',),
]

# BISHOP-THE DESTROYER
for email, date_from in email_date_map:
    qs = TimeSheet.objects.filter(timesheet_user__email=email, timesheet_for__gte=date_from)
    print(qs.count(), 'deleted')
    # qs.delete()

email_filters = [
    'asmit.t@golyanagro.com'
]

_from = '2020-08-01'
_to = '2020-09-18'


def find_duplicate_time_sheets():
    qs = TimeSheet.objects.filter(
        timesheet_user__email__in=email_filters,
        timesheet_for__range=(_from, _to)
    ).order_by().values(
        'timesheet_user',
        'timesheet_for',
        'work_shift',
        'work_time',
    )
    return tuple(qs.values_list('id', flat=True))


date_iterator = rrule(
    DAILY,
    dtstart=parse(_from),
    until=parse(_to)
)


def backup_logs(list_of_drop_ids):
    all_logs = dict()

    queryset = TimeSheet.objects.filter(
        id__in=list_of_drop_ids
    )

    # <-- Record all timestamps for all dates.
    for user, tses in itertools.groupby(queryset, key=lambda ts: ts.timesheet_user):
        all_logs[user] = list(
            TimeSheetEntry.objects.filter(
                timesheet__in=tses
            ).values_list(
                'timestamp', 'entry_method'
            )
        )
    required_pads = len(str(User.objects.order_by('-id').first().id))
    User.__str__ = lambda self: str(self.id).rjust(required_pads, '0') + str(self.full_name)
    JSON_LOGS = {
        str(u): v for u, v in all_logs.items()
    }
    print('Begin JSON Dump')
    base_path = os.path.abspath(
        os.path.join(
            settings.ROOT_DIR,
            'backups'
        )
    )
    file_path = os.path.join(
        base_path,
        f"all_entries.json"
    )
    with open(file_path, 'w') as f:
        json.dump(JSON_LOGS, f, default=str)
    print('Attendance Dump stored in ', file_path)
    User.__str__ = lambda u: u.full_name
    return all_logs


def delete_entries(time_sheets):
    """
    Removes all time_sheet_entries, resets punch_in/punch_out/punch_in_delta/punch_out_delta
    but preserves coefficients.
    :param time_sheets: time_sheets queryset
    """
    TimeSheet.objects.filter(
        id__in=time_sheets
    ).delete()


with transaction.atomic():
    # Find duplicates; no_drop means ts with reference to Att Adjustment.
    drop = find_duplicate_time_sheets()
    # Create a json dump of all entries.
    user_entries_dict = backup_logs(list_of_drop_ids=drop)
    # Remove all entries belonging to TS.
    delete_entries(drop)
    # because all is deleted, we repopulate all.

    for user in User.objects.filter(
            email__in=email_filters
    ):
        print(user)
        for da_te in date_iterator:
            (
                timesheets, created_count, updated_count, success
            ) = TimeSheet.objects._create_or_update_timesheet_for_profile(user, da_te)
            print(da_te, success, end='\t')

    for user, entries in user_entries_dict.items():
        for stamp, method in entries:
            TimeSheet.objects.clock(user, stamp, method)
