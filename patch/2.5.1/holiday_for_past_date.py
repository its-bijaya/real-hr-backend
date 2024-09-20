import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from irhrs.attendance.tasks.overtime import generate_daily_overtime
from irhrs.attendance.models import TimeSheetEntry, TimeSheet
from irhrs.leave.tasks import add_compensatory_leaves
from irhrs.organization.models import Organization, HolidayRule, Holiday

organization_list = ['org-slug-1', 'org-slug-2', 'org-slug-3']
date_to_add_holiday_for = '2020-02-26'
holiday_name = 'Last Sunday Holiday'
User = get_user_model()

User.__str__ = lambda self: str(self.id).rjust(6, '0') + str(self.full_name)


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


with transaction.atomic():
    for organization_to_add_holiday_for in organization_list:

        # < -- Create Last Sunday Holiday
        organization = Organization.objects.get(slug=organization_to_add_holiday_for)

        validated_data = {
            'organization': organization,
            'name': holiday_name,
            'date': date_to_add_holiday_for
        }

        created_object = Holiday.objects.create(**validated_data)

        rule_data = {
            'gender': 'All'
        }
        HolidayRule.objects.create(**rule_data, holiday=created_object)

        # Create Last Sunday Holiday -->

        ALL_LOGS = dict()

        queryset = TimeSheet.objects.filter(
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

        empty_timesheets(queryset)

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

with transaction.atomic():
    print('Begin Generate Overtime')
    generate_daily_overtime(date_to_add_holiday_for)
    print('Begin Leave Generation')
    add_compensatory_leaves(
        *(date_to_add_holiday_for,) * 4
    )
    print('End Leave Generation')
