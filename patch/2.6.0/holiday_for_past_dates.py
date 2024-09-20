import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from irhrs.attendance.tasks.overtime import generate_daily_overtime
from irhrs.attendance.models import TimeSheetEntry, TimeSheet
from irhrs.common.models import HolidayCategory
from irhrs.leave.tasks import add_compensatory_leaves
from irhrs.organization.models import Organization, HolidayRule, Holiday, OrganizationBranch

organization_list = ['mca-nepal']
# organization_list = ['alpl']
CONST = 'Bereavement'

HOLIDAY_DATE_RANGE_MAP = {
    CONST: ['2020-11-24'],
}

HOLIDAY_CATEGORY_MAP = {
    CONST: 'Bereavement'
}
ALL = 'All'
MALE = 'Male'
FEMALE = 'Female'
OTHER = 'Other'

GENDER_MAP = {
    CONST: ALL,
}

BRANCH_MAP = {
    CONST: []
}


User = get_user_model()

User.__str__ = lambda self: str(self.id).rjust(6, '0') + str(self.full_name)


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


with transaction.atomic():
    for organization_to_add_holiday_for in organization_list:
        for holiday_name, dates in HOLIDAY_DATE_RANGE_MAP.items():
            for date_to_add_holiday_for in dates:

                # < -- Create Holiday
                organization = Organization.objects.get(slug=organization_to_add_holiday_for)

                validated_data = {
                    'organization': organization,
                    'name': holiday_name,
                    'date': date_to_add_holiday_for
                }

                created_object = Holiday.objects.create(**validated_data)
                o, c = HolidayCategory.objects.get_or_create(
                    name=HOLIDAY_CATEGORY_MAP.get(holiday_name),
                    defaults={
                        'description': HOLIDAY_CATEGORY_MAP.get(holiday_name)
                    }
                )
                created_object.category = o
                created_object.save()

                rule_data = {
                    'gender': GENDER_MAP.get(holiday_name),
                    'lower_age': 16,
                    'upper_age': 99
                }
                rule = HolidayRule.objects.create(**rule_data, holiday=created_object)
                for branch in BRANCH_MAP.get(holiday_name):
                    branch_obj = OrganizationBranch.objects.get(slug=branch)
                    rule.branch.add(branch_obj)

                # Create Holiday -->

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
