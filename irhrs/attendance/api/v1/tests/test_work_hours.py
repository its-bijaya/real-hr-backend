from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.models import Q
from django.test import override_settings
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import TimeSheetFactory, \
    IndividualAttendanceSettingFactory, TimeSheetEntryFactory, \
    IndividualUserShiftFactory
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience, \
    RHRSAPITestCase
from irhrs.attendance.constants import BREAK_OUT, BREAK_IN
from irhrs.attendance.constants import PERSONAL, PUNCH_IN, PUNCH_OUT, OTHERS
from irhrs.attendance.models import TimeSheet, TimeSheetEntry
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import OrganizationBranchFactory

User = get_user_model()

class TimeSheetWorkHoursTest(RHRSTestCaseWithExperience):
    organization_name = "Google Inc."
    users = [
        ("userone@example.com", "password", "Male", "hr")
    ]

    @override_settings(UNPAID_BREAK_TYPES=(PERSONAL,))
    def setUp(self):
        super().setUp()
        today = get_today(with_time=True)
        self.today_9am = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=9,
                                     minute=0, tzinfo=today.tzinfo)
        self.today_10am = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=10,
                                     minute=0, tzinfo=today.tzinfo)

        self.today_12pm = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=12,
                                     minute=0, tzinfo=today.tzinfo)
        self.today_6pm = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=18,
                                     minute=0, tzinfo=today.tzinfo)

    @override_settings(UNPAID_BREAK_TYPES=(PERSONAL,))
    def test_deduct_unpaid_breaks_from_work_hours(self):
        self.timesheet = TimeSheetFactory(
            is_present=True,
            timesheet_user=self.admin
        )
        self.attendance_settings = IndividualAttendanceSettingFactory(
            user=self.admin
        )
        self.entry1 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.today_9am,
            entry_method='Web App',
            remark_category=PUNCH_IN
        )
        self.entry2 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.today_10am,
            entry_method='Web App',
            remark_category=PERSONAL
        )
        self.entry3 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.today_12pm,
            entry_method='Web App',
            remark_category=PERSONAL
        )
        self.entry4 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.today_6pm,
            entry_method='Web App',
            remark_category=PUNCH_OUT
        )
        self.timesheet.fix_entries()

        # setup check
        self.assertEqual(self.timesheet.punch_in, self.today_9am)
        self.assertEqual(self.timesheet.punch_out, self.today_6pm)
        ts = TimeSheet.objects.first()
        self.assertEqual(ts.worked_hours, timedelta(seconds=25200))

    @override_settings(UNPAID_BREAK_TYPES=(PERSONAL,))
    def test_unpaid_break_hours_in_irregularity_report(self):
        self.timesheet_one_for_unpaid_breaks = TimeSheetFactory(
            is_present=True,
            timesheet_user=self.admin
        )
        self.attendance_settings = IndividualAttendanceSettingFactory(
            user=self.admin
        )
        # timesheet_one entries
        self.entry1 = TimeSheetEntryFactory(
            timesheet=self.timesheet_one_for_unpaid_breaks,
            timestamp=self.today_9am,
            entry_method='Web App',
            remark_category=PUNCH_IN,
            entry_type=PUNCH_IN
        )
        self.entry2 = TimeSheetEntryFactory(
            timesheet=self.timesheet_one_for_unpaid_breaks,
            timestamp=self.today_10am,
            entry_method='Web App',
            remark_category=PERSONAL,
            entry_type=BREAK_IN
        )
        self.entry3 = TimeSheetEntryFactory(
            timesheet=self.timesheet_one_for_unpaid_breaks,
            timestamp=self.today_12pm,
            entry_method='Web App',
            remark_category=PERSONAL,
            entry_type=BREAK_OUT,
        )
        self.entry4 = TimeSheetEntryFactory(
            timesheet=self.timesheet_one_for_unpaid_breaks,
            timestamp=self.today_6pm,
            entry_method='Web App',
            remark_category=PUNCH_OUT,
            entry_type=PUNCH_OUT,
        )
        self.timesheet_one_for_unpaid_breaks.fix_entries()
        self.client.force_login(user=self.admin)
        irregularity_report_url = reverse(
            'api_v1:attendance:irregularity-report-user-irregularity',
            kwargs = {
                'organization_slug': self.organization.slug,
                'pk': self.admin.id
            }
        ) + '?type=unpaid_breaks'
        response = self.client.get(irregularity_report_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['results'][0]['total_lost'], '02:00:00')
        self.assertEqual(self.timesheet_one_for_unpaid_breaks.worked_hours,
                         timedelta(seconds=25200))

    @override_settings(UNPAID_BREAK_TYPES=(PERSONAL,))
    def test_cancelled_break_does_not_show_up_in_report(self):
        self.timesheet_one = TimeSheetFactory(
            is_present=True,
            timesheet_user=self.admin
        )
        self.attendance_settings = IndividualAttendanceSettingFactory(
            user=self.admin
        )
        self.individual_user_shift = IndividualUserShiftFactory(
            individual_setting=self.attendance_settings
        )
        # timesheet_one entries
        self.entry1 = TimeSheetEntryFactory(
            timesheet=self.timesheet_one,
            timestamp=self.today_9am,
            entry_method='Web App',
            remark_category=PUNCH_IN,
            entry_type=PUNCH_IN
        )
        self.entry2 = TimeSheetEntryFactory(
            timesheet=self.timesheet_one,
            timestamp=self.today_10am,
            entry_method='Web App',
            remark_category=PERSONAL,
            is_deleted=True,
            entry_type=BREAK_OUT
        )
        self.entry3 = TimeSheetEntryFactory(
            timesheet=self.timesheet_one,
            timestamp=self.today_12pm,
            entry_method='Web App',
            remark_category=PERSONAL,
            is_deleted=True,
            entry_type=BREAK_IN
        )
        self.entry4 = TimeSheetEntryFactory(
            timesheet=self.timesheet_one,
            timestamp=self.today_6pm,
            entry_method='Web App',
            remark_category=PUNCH_OUT,
            entry_type=PUNCH_OUT
        )
        self.timesheet_one.fix_entries()
        self.client.force_login(user=self.admin)
        irregularity_report_url = reverse(
            'api_v1:attendance:irregularity-report-user-irregularity',
            kwargs = {
                'organization_slug': self.organization.slug,
                'pk': self.admin.id
            }
        ) + '?type=unpaid_breaks'
        response = self.client.get(irregularity_report_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)
        attendance_irrgeularity_user_list = reverse(
            'api_v1:attendance:irregularity-report-list',
            kwargs = {
                'organization_slug': self.organization.slug
            }
        )
        response = self.client.get(attendance_irrgeularity_user_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(
            response.json()['results'][0]['results']['unpaid_break_out_count'],
            0
        )


    @override_settings(UNPAID_BREAK_TYPES=(PERSONAL,))
    def test_missing_punch_out_shows_up_in_unpaid_breaks(self):
        self.timesheet_one = TimeSheetFactory(
            is_present=True,
            timesheet_user=self.admin
        )
        self.attendance_settings = IndividualAttendanceSettingFactory(
            user=self.admin
        )
        self.individual_user_shift = IndividualUserShiftFactory(
            individual_setting=self.attendance_settings
        )
        # timesheet_one entries
        self.entry1 = TimeSheetEntryFactory(
            timesheet=self.timesheet_one,
            timestamp=self.today_9am,
            entry_method='Web App',
            entry_type=PUNCH_IN
        )
        self.entry2 = TimeSheetEntryFactory(
            timesheet=self.timesheet_one,
            timestamp=self.today_10am,
            entry_method='Web App',
            remark_category=PERSONAL,
            entry_type=BREAK_OUT
        )
        self.entry3 = TimeSheetEntryFactory(
            timesheet=self.timesheet_one,
            timestamp=self.today_12pm,
            entry_method='Web App',
            remark_category=PERSONAL,
            entry_type=BREAK_IN
        )
        self.timesheet_one.fix_entries()
        self.client.force_login(user=self.admin)
        irregularity_report_url = reverse(
            'api_v1:attendance:irregularity-report-user-irregularity',
            kwargs = {
                'organization_slug': self.organization.slug,
                'pk': self.admin.id
            }
        ) + '?type=unpaid_breaks'
        response = self.client.get(irregularity_report_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

        user = self.created_users[0]
        branch = OrganizationBranchFactory(organization=self.organization)
        user_detail = user.detail
        user_detail.branch = branch
        user_detail.save()
        attendance_irrgeularity_user_list = reverse(
            'api_v1:attendance:irregularity-report-list',
            kwargs = {
                'organization_slug': self.organization.slug
            }
        )
        response = self.client.get(attendance_irrgeularity_user_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(
            response.json()['results'][0]['results']['unpaid_break_out_count'],
            1
        )
        expected_output = {
            'name': branch.name,
            'slug': branch.slug
        }
        self.assertEqual(
            response.json()['results'][0]['user']['branch'],
            expected_output
        )


class TimeSheetWorkHoursOverTimeTest(RHRSAPITestCase):
    organization_name = "Google Inc."
    users = [
        ("userone@example.com", "password", "Male")
    ]

    def setUp(self):
        super().setUp()

        self.timesheet = TimeSheetFactory(
            is_present=True,
            timesheet_user=self.admin
        )
        self.attendance_settings = IndividualAttendanceSettingFactory(
            user=self.admin
        )

        today = get_today(with_time=True)
        self.early_in = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=6,
                                     minute=0, tzinfo=today.tzinfo)
        self.today_9am = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=9,
                                     minute=0, tzinfo=today.tzinfo)
        self.today_10am = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=10,
                                     minute=0, tzinfo=today.tzinfo)
        self.today_12pm = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=12,

                                     minute=0, tzinfo=today.tzinfo)
        self.today_6pm = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=18,
                                     minute=0, tzinfo=today.tzinfo)
        self.late_out_time = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=21,
                                     minute=0, tzinfo=today.tzinfo)

    @override_settings(UNPAID_BREAK_TYPES=(PERSONAL,))
    def test_deduct_unpaid_breaks_from_work_hours_with_early_overtime(self):
        self.entry1 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.early_in,
            entry_method='Web App',
            remark_category=PUNCH_IN
        )
        self.entry2 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.today_10am,
            entry_method='Web App',
            remark_category=PERSONAL

)
        self.entry3 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.today_12pm,
            entry_method='Web App',
            remark_category=PERSONAL
        )
        self.entry4 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.today_6pm,
            entry_method='Web App',
            remark_category=PUNCH_OUT
        )
        self.timesheet.fix_entries()

        # setup check
        self.assertEqual(self.timesheet.punch_in, self.early_in)
        self.assertEqual(self.timesheet.punch_out, self.today_6pm)
        ts = TimeSheet.objects.first()
        self.assertEqual(ts.worked_hours, timedelta(seconds=36000))


    @override_settings(UNPAID_BREAK_TYPES=(PERSONAL,))
    def test_deduct_unpaid_breaks_from_work_hours_with_late_overtime(self):
        self.entry1 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.today_9am,
            entry_method='Web App',
            remark_category=PUNCH_IN
        )
        self.entry2 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.today_10am,
            entry_method='Web App',
            remark_category=PERSONAL

)
        self.entry3 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.today_12pm,
            entry_method='Web App',
            remark_category=PERSONAL
        )
        self.late_out = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.late_out_time,
            entry_method='Web App',
            remark_category=PUNCH_OUT
        )
        self.timesheet.fix_entries()

        # setup check
        self.assertEqual(self.timesheet.punch_in, self.today_9am)
        self.assertEqual(self.timesheet.punch_out, self.late_out_time)
        ts = TimeSheet.objects.first()
        self.assertEqual(ts.worked_hours, timedelta(seconds=36000))


