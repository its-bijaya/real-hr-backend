from irhrs.leave.models import LeaveRequest
from irhrs.leave.utils.leave_sheet import create_leave_sheets

import logging

logger = logging.getLogger(__name__)


def create_leave_sheet_for_leave_requests():
    failed_requests = {}
    qs = LeaveRequest.objects.all().filter(sheets__isnull=True)

    for l in qs:
        try:
            create_leave_sheets(l)
        except Exception as e:
            failed_requests.update({l.id: f"{e}"})
    return failed_requests


failed = create_leave_sheet_for_leave_requests()
logging.warn("Failed records while creating leave sheets.")
logging.info(failed)

print(failed)
