import json

from django.conf import settings
from irhrs.attendance.constants import ADMS
from irhrs.attendance.models import AttendanceSource
from irhrs.attendance.models._adms import DeviceTimesheet

ADMS_DIRECT = getattr(settings, 'ADMS_DIRECT', 'adms_direct')

date_after_which_attendance_entries_will_be_synced = '2020-04-20T00:00+05:45'
for device in AttendanceSource.objects.filter(
    sync_method=ADMS
):
    # Filter the date. and select the first id. and save as id-1 (last_pulled_id)
    last_attendance_entry_to_set_pointer_at = DeviceTimesheet.objects.select_related(
        'employee'
    ).using(
        ADMS_DIRECT
    ).filter(
        device_sn=device.serial_number
    ).filter(
        check_time__lte=date_after_which_attendance_entries_will_be_synced
    ).order_by(
        '-check_time'
    ).first()
    if not last_attendance_entry_to_set_pointer_at:
        data = {
            'last_pulled_data_id': 0,
            'last_pulled_data_timestamp': date_after_which_attendance_entries_will_be_synced
        }
    else:
        data = {
            'last_pulled_data_id': last_attendance_entry_to_set_pointer_at.id,
            'last_pulled_data_timestamp': str(last_attendance_entry_to_set_pointer_at.checktime)
        }
    print(
        'Device', device.serial_number,
        '\n',
        json.dumps(data, indent=2)
    )
    device.extra_data = data
    # device.save()
