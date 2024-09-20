import datetime
from datetime import time, timedelta
from django.urls import reverse
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import OvertimeSettingFactory, WorkShiftFactory
from irhrs.attendance.constants import DAILY, WEB_APP, CONFIRMED, HOLIDAY
from irhrs.attendance.models import IndividualAttendanceSetting, IndividualUserShift, WorkDay, \
    TimeSheet, TimeSheetEntry, OvertimeClaim
from irhrs.attendance.tasks.overtime import generate_overtime
from irhrs.attendance.utils.overtime_utils import get_early_late_overtime
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_yesterday, combine_aware
from irhrs.notification.models import Notification
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, LeaveAccountFactory


class TestDeleteTimesheetEntryWhenOTGenerated(RHRSAPITestCase):
    users = [
        ('admin@email.com', 'password', 'Male'),
    ]
    organization_name = "Google"

    def setUp(self) -> None:
        super().setUp()
        days_per_week = getattr(self, 'days_per_week', 7)
        self.user = self.created_users[0]

        setting, _ = IndividualAttendanceSetting.objects.update_or_create(
            user=self.user,
            defaults=dict(
                overtime_setting=OvertimeSettingFactory(),
                enable_overtime=True
            )
        )

        ius = IndividualUserShift.objects.create(
            individual_setting=setting,
            shift=WorkShiftFactory(work_days=days_per_week),
            applicable_from=get_yesterday()
        )
        WorkDay.objects.filter(shift=ius.shift).update(applicable_from=ius.applicable_from)
        master_setting = MasterSettingFactory()
        leave_type = LeaveTypeFactory(master_setting=master_setting)
        leave_rule = LeaveRuleFactory(
            leave_type=leave_type
        )
        self.leave_account = LeaveAccountFactory(
            rule=leave_rule,
            user=self.user
        )

    @property
    def delete_timesheet_entry_url(self):
        return reverse(
            'api_v1:attendance:update-entries-list',
            kwargs={
                'adjustment_action': 'delete',
                'organization_slug': self.organization.slug
            }
        )

    @property
    def delete_timesheet_entry_payload(self):
        return {
            "timesheet": TimeSheet.objects.first().id,
            "timesheet_entry": TimeSheetEntry.objects.last().id,
            "description": "New description required"
        }

    def _create_timesheets(self):
        TimeSheet.objects.all().delete()
        time_sheets, *_ = TimeSheet.objects._create_or_update_timesheet_for_profile(
            self.user,
            get_yesterday()
        )
        leave_start = min([x.timesheet_for for x in time_sheets]) if time_sheets else None
        leave_end = max([x.timesheet_for for x in time_sheets]) if time_sheets else None

        if not (leave_end and leave_start):
            print(
                "No time sheets were created. Rethink the scenarios."
            )
            return

        return time_sheets

    @staticmethod
    def _clock_timesheet(timesheet, timestamp):
        TimeSheet.objects.clock(
            user=timesheet.timesheet_user,
            date_time=timestamp,
            entry_method=WEB_APP,
            timesheet=timesheet
        )

    def test_delete_timesheet_entry_when_OT_is_generated(self):
        entry = (
                time(7, 0),
                time(20, 0),
                True,
                timedelta(minutes=120),
                timedelta(minutes=120),
            )

        timesheet = self._create_timesheets()[0]
        ti, to, ot_created, early_ot, out_ot = entry
        ts1, ts2 = map(
            lambda x: combine_aware(timesheet.timesheet_for, x),
            (ti, to)
        )
        self._clock_timesheet(
            timesheet,
            ts1
        )
        self._clock_timesheet(
            timesheet,
            ts2
        )

        overtime = generate_overtime(
            timesheet.timesheet_for,
            timesheet.timesheet_for,
            DAILY
        )
        self.assertEqual(
            overtime.get('created_count'),
            1
        )
        self.assertTrue(
            Notification.objects.filter(
                text=f"Your overtime for {get_yesterday()} has been generated."
            ).exists()
        )
        # Changed overtime status to CONFIRMED so that validation stops deletion of timesheet entry
        overtime_status = OvertimeClaim.objects.first()
        overtime_status.status = CONFIRMED
        overtime_status.save()
        self.client.force_login(self.admin)
        response = self.client.post(
            self.delete_timesheet_entry_url,
            self.delete_timesheet_entry_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json().get('non_field_errors'),
            [f'Cannot remove entries with overtime in {CONFIRMED} status']
        )

        delete_timesheet_entry_url = reverse(
                'api_v1:attendance:timesheet-entry-delete',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'pk': timesheet.id,
                    "timesheet_entry_id": timesheet.timesheet_entries.last().id
                }
            )

        response = self.client.post(
            self.delete_timesheet_entry_url,
            self.delete_timesheet_entry_payload,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json().get('non_field_errors'),
            [f'Cannot remove entries with overtime in {CONFIRMED} status']
        )

        # Checking for NoneType issue by sending punch_in and punch_out as None
        timesheet.punch_in = None
        timesheet.punch_out = None
        timesheet.coefficient = HOLIDAY
        timesheet.save()
        ot = get_early_late_overtime(timesheet, OvertimeSettingFactory())
        self.assertEqual(
            ot,
            (datetime.timedelta(0), datetime.timedelta(0))
        )
