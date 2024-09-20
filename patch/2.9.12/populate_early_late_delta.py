# TimeSheet conditions
from irhrs.attendance.constants import FULL_LEAVE, WORKDAY
from irhrs.attendance.models.attendance import TimeSheet
conditions = {
    'coefficient': WORKDAY,
    'leave_coefficient': FULL_LEAVE
}

timesheet_list = TimeSheet.objects.filter(**conditions)

total_timesheet_count = timesheet_list.count()
for index, timesheet in enumerate(timesheet_list):
    print(f'{index}/{total_timesheet_count}', end='\r')
    timesheet.fix_entries()
