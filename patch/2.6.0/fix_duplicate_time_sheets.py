import itertools
import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Sum

from irhrs.attendance.constants import NO_LEAVE
from irhrs.attendance.models import TimeSheet, TimeSheetEntry

User = get_user_model()


def find_duplicate_time_sheets():
    qs = TimeSheet.objects.order_by().values(
        'timesheet_user',
        'timesheet_for',
        'work_shift',
        'work_time',
    ).annotate(
        timesheets_count=Count(
            'timesheet_for'
        )
    ).filter(
        timesheets_count__gt=1
    )
    # Reporting
    print(qs.aggregate(tc=Sum('timesheets_count')).get('tc'), 'duplicate')

    drop_ids = list()
    for q in qs:
        # we shall order by present status, and delete other duplicates.
        base = list(TimeSheet.objects.filter(
            timesheet_user=q.get('timesheet_user'),
            timesheet_for=q.get('timesheet_for'),
            leave_coefficient=NO_LEAVE
        ).exclude(
            adjustment_requests__isnull=False
        ).order_by(
            '-is_present'
        ).values_list('id', flat=True))[1:]
        drop_ids.append(base)  # iterable of iterables, shall use chain to flatten.
    all_ids = list(itertools.chain.from_iterable(drop_ids))
    with_adj = qs.exclude(id__in=all_ids)

    if with_adj.exists():
        print(with_adj.count(), 'needs manual work.')
        for q in with_adj:
            for t in TimeSheet.objects.filter(
                timesheet_user=q.get('timesheet_user'),
                timesheet_for=q.get('timesheet_for'),
            ).exclude(
                adjustment_requests__isnull=False
            ).order_by(
                'is_present'
            ):
                print(t.id, t.adjustment_requests.all(), t)
    return all_ids, list(with_adj.values_list('id', flat=True))


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
    return all_logs


def delete_entries(time_sheets):
    """
    Removes all time_sheet_entries, resets punch_in/punch_out/punch_in_delta/punch_out_delta
    but preserves coefficients.
    :param time_sheets: time_sheets queryset
    """
    TimeSheet.objects.filter(
        id__in=time_sheets
    ).update(
        punch_in=None,
        punch_out=None,
        punch_in_delta=None,
        punch_out_delta=None,
        punctuality=None,
        is_present=False
    )
    TimeSheetEntry.objects.filter(
        timesheet__in=time_sheets
    ).delete()


with transaction.atomic():
    # Find duplicates; no_drop means ts with reference to Att Adjustment.
    drop, no_drop = find_duplicate_time_sheets()
    if drop:
        # Create a json dump of all entries.
        user_entries_dict = backup_logs(list_of_drop_ids=drop)
        # Remove all entries belonging to TS.
        delete_entries(drop)
        TimeSheet.objects.filter(id__in=drop).delete()
        for user, entries in user_entries_dict.items():
            for stamp, method in entries:
                TimeSheet.objects.clock(user, stamp, method)

print('No Drop', no_drop)
