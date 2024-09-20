import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from irhrs.attendance.tasks.overtime import generate_daily_overtime
from irhrs.attendance.models import TimeSheetEntry, TimeSheet
from irhrs.leave.tasks import add_compensatory_leaves
from irhrs.organization.models import Organization, HolidayRule, Holiday, OrganizationBranch
from irhrs.attendance.managers.utils import fix_entries_on_commit


def fix_entries_immediately(self):
    fix_entries_on_commit(self, send_notification=False)


organization_slug = 'himalayan-general-insurance-co-ltd'
User = get_user_model()
User.__str__ = lambda self: str(self.id).rjust(6, '0') + str(self.full_name)
TimeSheet.fix_entries = fix_entries_immediately
HOLIDAYS = Holiday.objects.filter(
    organization__slug=organization_slug,
    date__in=[
        '2020-10-23',
        '2020-10-24',
        '2020-10-25',
        '2020-10-26',
        '2020-10-27',
    ]
)


def empty_time_sheets(time_sheets):
    """
    Removes all time_sheet_entries, resets punch_in/punch_out/punch_in_delta/punch_out_delta
    but preserves coefficients.
    :param time_sheets: time_sheets queryset
    """
    time_sheets.update(
        punch_in=None,
        punch_out=None,
        punch_in_delta=None,
        punch_out_delta=None,
        punctuality=None,
        is_present=False
    )
    TimeSheetEntry.objects.filter(
        timesheet__in=time_sheets
    ).delete()

ul = [
    193,
    178,
    176,
    171,
    169,
    167,
    164,
    163,
    153,
    152,
    139,
    135,
    127,
    122,
    101,
    99,
    93,
    85,
    67,
    55,
    46,
    42,
    29,
    26,
    24,
    23,
    20,
    15,
    13
]

with transaction.atomic():
    for holiday in HOLIDAYS:
        holiday_rule = holiday.rule
        holiday_rule.religion.clear()
        date_to_add_holiday_for = holiday.date
        organization = holiday.organization
        organization_to_add_holiday_for = organization.slug

        ALL_LOGS = dict()
        queryset = TimeSheet.objects.filter(
            timesheet_user__in=ul,
            timesheet_for=date_to_add_holiday_for,
            timesheet_user__detail__organization=organization
        )

        # <-- Record all timestamps for the date.
        for user in User.objects.filter(
                id__in=queryset.values_list('timesheet_user', flat=True)
        ):
            ALL_LOGS[user] = list(
                TimeSheetEntry.objects.filter(
                    timesheet__timesheet_user=user,
                    timesheet__timesheet_for=date_to_add_holiday_for
                ).values_list(
                    'timestamp', 'entry_method'
                )
            )

        JSON_LOGS = {
            str(u): v for u, v in ALL_LOGS.items()
        }
        print('Begin JSON Dump')
        base_path = os.path.abspath(
            os.path.join(
                settings.ROOT_DIR,
                'backups'
            )
        )
        file_path = os.path.join(
            base_path,
            f"{organization_to_add_holiday_for}-{date_to_add_holiday_for}.json"
        )
        with open(file_path, 'w') as f:
            json.dump(JSON_LOGS, f, default=str)
        print('Attendance Dump stored in ', file_path)

        # Record all timestamps for the date. -->

        empty_time_sheets(queryset)

        for ts in queryset:
            TimeSheet.objects._create_or_update_timesheet_for_profile(
                ts.timesheet_user, ts.timesheet_for
            )

        from irhrs.attendance.tasks.timesheets import populate_timesheets

        populate_timesheets(date_to_add_holiday_for)

        for user, data_list in ALL_LOGS.items():
            for timestamp, entry_method in data_list:
                TimeSheet.objects.clock(
                    user=user,
                    date_time=timestamp,
                    entry_method=entry_method
                )

User.__str__ = lambda self: self.full_name
