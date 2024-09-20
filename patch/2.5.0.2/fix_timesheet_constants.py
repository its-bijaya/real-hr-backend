from irhrs.attendance.constants import FIRST_HALF, SECOND_HALF
from irhrs.attendance.models import TimeSheet

TimeSheet.objects.filter(
    leave_coefficient='first'
).update(
    leave_coefficient=FIRST_HALF
)

TimeSheet.objects.filter(
    leave_coefficient='second'
).update(
    leave_coefficient=SECOND_HALF
)
