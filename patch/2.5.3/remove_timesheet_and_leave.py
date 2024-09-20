import logging

from django.contrib.auth import get_user_model
from django.db import transaction

from irhrs.attendance.models import TimeSheet
from irhrs.core.utils import get_system_admin
from irhrs.leave.constants.model_constants import ADDED
from irhrs.leave.models import LeaveAccountHistory, LeaveRequest
from irhrs.leave.utils.timesheet import empty_timesheets

USER = get_user_model()


@transaction.atomic()
def revert_leave_for_date(leave_request):
    leave_account = leave_request.leave_account
    leave_request_balance = leave_request.balance
    actor = get_system_admin()

    # We are not going to revert leave as this is a duplication only.
    # revert_timesheet_for_leave(leave_request)

    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=actor,
        action=ADDED,
        previous_balance=leave_account.balance,
        previous_usable_balance=leave_account.usable_balance,
        remarks=f'Added Balance {leave_request.balance} after cancellation of '
                f'approved request for {leave_request.start} - {leave_request.end}'
    )
    leave_account.balance += leave_request_balance
    leave_account.usable_balance += leave_request_balance
    account_history.new_balance = leave_account.balance
    account_history.new_usable_balance = leave_account.usable_balance
    account_history.save()
    leave_account.save()

    leave_request.is_deleted = True
    leave_request.save()

    # recalibrate_overtime_due_to_leave_updates(leave_request, actor)

    logger = logging.getLogger(__name__)
    logger.info(
        f'Deleted approved request of {leave_account.user} for '
        f'{leave_request.start} - {leave_request.end}'
    )


def destroy_time_sheet_for_a_date_for_an_user(user_id, date):
    """
    Destroy TimeSheet for a date/For an user.
    :param user_id: Id of the user
    :param date: Date for which time sheets are to be destroyed.
    """
    empty_timesheets(TimeSheet.objects.filter(
        user_id=user_id,
        timesheet_for=date
    ))

#
# lrs = LeaveRequest.objects.filter(
#     start__date='2020-01-02',
#     user__email='santosh.chaudhary@merojob.com'
# ).all()
#
# if lrs.count() > 1:
#     print('Multiple Leave Requests found')
#     revert_leave_for_date(lrs[0])
# else:
#     print('Multiple leave for date not found')
