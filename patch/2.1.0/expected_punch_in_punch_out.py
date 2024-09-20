from datetime import timedelta

from django.utils import timezone

from irhrs.attendance.constants import OFFDAY
from irhrs.attendance.models import TimeSheet
from irhrs.core.utils.common import combine_aware
from irhrs.leave.constants.model_constants import APPROVED, FIRST_HALF, \
    SECOND_HALF
from irhrs.leave.models import LeaveRequest

initiated = timezone.now().astimezone()
print('Initiated on ', initiated)

update_list = list()

for ts in TimeSheet.objects.exclude(
    coefficient=OFFDAY
):
    timing = ts.work_time
    if not timing:
        continue
    print('Set expected in/out for ', ts)
    shift_starts_at = combine_aware(
        ts.timesheet_for,
        timing.start_time
    )
    end_time = ts.timesheet_for + timedelta(
        days=1
    ) if timing.extends else ts.timesheet_for
    shift_ends_at = combine_aware(
        end_time,
        timing.end_time
    )
    ts.expected_punch_in = shift_starts_at
    ts.expected_punch_out = shift_ends_at
    ts.save(update_fields=['expected_punch_in', 'expected_punch_out'])
    update_list.append(ts)

# TimeSheet.objects.bulk_update(
#     update_list,
#     fields=['expected_punch_in', 'expected_punch_out']
# )

terminated = timezone.now().astimezone()

print('Ended on ', terminated)
print('Total Execution Time', terminated - initiated)

initiated = timezone.now().astimezone()
print('Timesheet Patch for leave days Initiated on ', initiated)

updates = list()
for leave_request in LeaveRequest.objects.filter(
    status=APPROVED,
    part_of_day__in=[FIRST_HALF, SECOND_HALF]
):
    # first half or second half is a one-day-leave
    timesheet = leave_request.user.timesheets.filter(
        timesheet_for=leave_request.start.date()
    ).first()
    if not (timesheet and timesheet.work_time):
        continue
    mins = timedelta(minutes=timesheet.work_time.working_minutes // 2)
    if leave_request.part_of_day == FIRST_HALF:
        expected = timesheet.expected_punch_in + mins
        timesheet.expected_punch_in = expected
    elif leave_request.part_of_day == SECOND_HALF:
        expected = timesheet.expected_punch_out - mins
        timesheet.expected_punch_out = expected
    print('Set expected in/out for leave range ', leave_request)
    timesheet.save(update_fields=['expected_punch_in', 'expected_punch_out'])

    # updates.append(timesheet)

# TimeSheet.objects.bulk_update(
#     updates,
#     fields=['expected_punch_in', 'expected_punch_out']
# )

terminated = timezone.now().astimezone()

print('Timesheet Patch for leave days Ended on ', terminated)
print('Total Execution Time', terminated - initiated)
