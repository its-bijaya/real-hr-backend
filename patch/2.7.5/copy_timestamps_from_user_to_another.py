from django.contrib.auth import get_user_model
from django.db import transaction

from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.models import TimeSheetEntry, TimeSheet


def fix_entries_immediately(ts):
    return fix_entries_on_commit(ts, send_notification=False)


TimeSheet.fix_entries = fix_entries_immediately


def get_old_timestamps(user):
    entries = TimeSheetEntry.objects.filter(timesheet__timesheet_user=user)
    return entries


def populate_timestamps(user, new_timestamps):
    for timesheet_entry in new_timestamps:
        print(timesheet_entry.timestamp.astimezone().date(), end='\r')
        TimeSheet.objects.clock(
            user,
            timesheet_entry.timestamp,
            timesheet_entry.entry_method,
            entry_type=timesheet_entry.entry_type,
            remarks=timesheet_entry.remarks,
            remark_category=timesheet_entry.remark_category,
            latitude=timesheet_entry.latitude,
            longitude=timesheet_entry.longitude
        )


User = get_user_model()
id_list = [
    (8, 211),
    (7, 212),
    (79, 213),
    (89, 214),
    (82, 215),
    (80, 233),
    (3, 210),
    (85, 208),
    (22, 234),
]

with transaction.atomic():
    for old_id, new_id in id_list:
        new_user = User.objects.get(pk=new_id)
        old_user = User.objects.get(pk=old_id)
        print(new_user.full_name, 'populating')
        populate_timestamps(
            new_user,
            get_old_timestamps(old_user)
        )

"""
id_list = [
    (8, 211),
    (7, 212),
    (79, 213),
    (89, 214),
    (82, 215),
    (80, 233),
    (3, 210),
    (85, 208),
    (22, 234),
]
for _, new_id in id_list:
    rs = TimeSheet.objects.filter(timesheet_user=new_id).delete()
    print('deleting old time-sheets for', new_id, rs)
    print('Populating TimeSheets')
    usr = User.objects.get(pk=new_id)
    iterator = list(
        rrule(
            DAILY, 
            dtstart=usr.detail.joined_date, 
            until=datetime.datetime.now().date())
            )
    for d in map(lambda dt: dt.date(), iterator):
        print(d, end='\r')
        TimeSheet.objects._create_or_update_timesheet_for_profile(usr, d)
    print()

id_list = [
    (8, 211),
    (7, 212),
    (79, 213),
    (89, 214),
    (82, 215),
    (80, 233),
    (3, 210),
    (85, 208),
    (22, 234),
]
for old, _ in User.objects.filter(id__in=[x[0] for x in id_list]):
    print('deactivate', new)
    new.is_blocked = True
    new.is_active = False
    new.save()
    
"""