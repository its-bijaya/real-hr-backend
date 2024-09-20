"""@irhrs_docs"""
from logging import getLogger


from irhrs.leave.models.request import LeaveSheet
from irhrs.leave.utils.balance import get_leave_balance

logger = getLogger(__name__)


def create_leave_sheets(leave_request, steps=None, force_recalculate=False):
    """Create Leave Sheets for given leave request"""

    logger_prefix = f"{leave_request} [id:{leave_request.id} -->"
    logger.info(f"{logger_prefix} Creating Leave Sheet for request")

    if leave_request.sheets.all().exists():
        if force_recalculate:
            leave_request.sheets.all().delete()
        else:
            return

    if not steps:
        logger.info(f"{logger_prefix} No steps passed, recomputing steps for the request.")
        balance, steps = get_leave_balance(
                    leave_request.start,
                    leave_request.end,
                    leave_request.leave_account.user,
                    leave_request.leave_account,
                    leave_request.part_of_day
                )
        logger.info(f"{logger_prefix}Steps computed successfully")
        if balance != leave_request.balance:
            logger.warning(f"{logger_prefix} Recalculated balance did not match "
                           f"the actual balance.")

    logger.info(f"{logger_prefix} Filtering out sheets with balance 0")

    sheets = [
        LeaveSheet(
            request=leave_request,
            leave_for=s["leave_for"],
            balance=s["balance"],
            start=s["start_time"],
            end=s["end_time"],
            balance_minutes=s.get('balance_minutes')
        )
        for s in steps if (s["balance"] and s["balance"] > 0) or s.get('balance_minutes')
    ]

    LeaveSheet.objects.bulk_create(sheets)
    logger.info(f"{logger_prefix} Created Leave Sheets")
