from django.db import transaction

from irhrs.leave.constants.model_constants import CREDIT_HOUR, TIME_OFF
from irhrs.leave.models import LeaveRequest
from irhrs.leave.utils.balance import update_hourly_leave_per_day_for_leave_request

HOURLY_LEAVES = (CREDIT_HOUR, TIME_OFF)

with transaction.atomic():
    requests = LeaveRequest.objects.filter(leave_rule__leave_type__category__in=HOURLY_LEAVES)
    for request in requests:
        update_hourly_leave_per_day_for_leave_request(request)
