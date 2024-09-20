from django.contrib.auth import get_user_model
from django.db import transaction

from irhrs.attendance.models import TimeSheetEntry, TimeSheet
from irhrs.attendance.tasks.overtime import generate_daily_overtime
from irhrs.attendance.tasks.timesheets import populate_timesheets
from irhrs.core.constants.common import DANGER
from irhrs.core.utils.common import get_today
from irhrs.leave.tasks import add_compensatory_leaves
from irhrs.notification.utils import notify_organization
from irhrs.permission.constants.permissions import ORGANIZATION_PERMISSION, \
    ORGANIZATION_SETTINGS_PERMISSION, HOLIDAY_PERMISSION


USER = get_user_model()


def empty_timesheets(timesheets):
    """
    Removes all timesheet_entries, resets punch_in/punch_out/punch_in_delta/punch_out_delta
    but preserves coefficients.
    :param timesheets: timesheets queryset
    """
    timesheets.update(
        punch_in=None,
        punch_out=None,
        punch_in_delta=None,
        punch_out_delta=None,
        punctuality=None,
        is_present=False
    )
    TimeSheetEntry.objects.filter(
        timesheet__in=timesheets
    ).delete()


def refresh_timesheets(timesheet_for, organization, filters=None):
    """
    Removes all timesheet entries for day, Updates timesheets with new changes, clocks again,
    regenerate overtime, adds compensatory leaves
    """

    if not filters:
        filters = dict()

    all_logs = dict()

    time_begin = get_today(with_time=True).isoformat()

    # acquire lock on timesheets
    queryset = TimeSheet.objects.select_for_update().filter(
        timesheet_for=timesheet_for,
        timesheet_user__detail__organization=organization,
        **filters
    )
    with transaction.atomic():
        # <-- Record all timestamps for the date.
        for user in USER.objects.filter(
                id__in=queryset.values_list('timesheet_user', flat=True)
        ):
            all_logs[user] = list(
                TimeSheetEntry.objects.filter(
                    timesheet__timesheet_user=user,
                    timesheet__timesheet_for=timesheet_for
                ).values_list(
                    'timestamp', 'entry_method'
                )
            )

        empty_timesheets(queryset)

        for ts in queryset:
            TimeSheet.objects._create_or_update_timesheet_for_profile(
                ts.timesheet_user, ts.timesheet_for
            )

        populate_timesheets(timesheet_for)

        for user, data_list in all_logs.items():
            for timestamp, entry_method in data_list:
                TimeSheet.objects.clock(
                    user=user,
                    date_time=timestamp,
                    entry_method=entry_method
                )

    generate_daily_overtime(
        str(time_begin),
        schedule_next_task=False  # so that it won't interfere with daily task
    )
    add_compensatory_leaves(
        *(timesheet_for,) * 4
    )


def past_holiday_added_post_action(holiday):
    """
    Holiday update post actions
    """
    holiday_date = holiday.date
    organization = holiday.organization
    try:
        refresh_timesheets(timesheet_for=holiday_date, organization=organization)
    except Exception as e:
        notify_organization(
            text=f"Timesheets update after holiday addition for past date {holiday_date} has"
                 f" failed. Please contact support.",
            organization=organization,
            permissions=[
                ORGANIZATION_PERMISSION,
                ORGANIZATION_SETTINGS_PERMISSION,
                HOLIDAY_PERMISSION
            ],
            label=DANGER,
            action=holiday,
        )
        raise e

