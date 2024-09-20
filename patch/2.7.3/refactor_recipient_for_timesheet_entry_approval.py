from django.db.models import F

timesheet_entries = []


def take_backup(apps, scheme):
    global timesheet_entries
    TimeSheetEntryApproval = apps.get_model('attendance', 'TimeSheetEntryApproval')
    timesheet_entries = TimeSheetEntryApproval.objects.all().annotate(
        recipient=F('timesheet_approval__recipient_id')
    ).values('id', 'recipient')


def set_data(apps, scheme):
    global timesheet_entries
    TimeSheetEntryApproval = apps.get_model('attendance', 'TimeSheetEntryApproval')
    updated_id = []
    for datum in timesheet_entries:
        _id = datum.pop('id')
        updated_id.append(_id)
        _ = TimeSheetEntryApproval.objects.filter(id=_id).update(recipient_id=datum['recipient'])
    print(f'Updated data are: ')
    print(updated_id)
