from irhrs.core.utils.subordinates import find_supervisor
from irhrs.leave.constants.model_constants import REQUESTED
from irhrs.leave.models.request import LeaveRequestDeleteHistory


def update_leave_cancel_request():
    requests = LeaveRequestDeleteHistory.objects.filter(status=REQUESTED)
    print('Updated Leave Cancel Request:')
    print(requests.values_list('id', flat=True))
    for request in requests:
        request.recipient_id = find_supervisor(request.leave_request.user_id)
        request.save()

