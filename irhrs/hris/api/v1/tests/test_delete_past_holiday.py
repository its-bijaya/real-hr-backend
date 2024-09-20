import datetime

from django.urls import reverse
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    WorkShiftFactory, IndividualUserShiftFactory, WorkDayFactory, WorkTimingFactory
from irhrs.attendance.constants import WORKDAY, HOLIDAY
from irhrs.attendance.models import TimeSheet
from irhrs.attendance.tasks.timesheets import populate_timesheet_for_user, populate_timesheets
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.organization.api.v1.tests.factory import HolidayFactory


class TestDeletePastHoliday(RHRSAPITestCase):
    users = (
        ('admin@email.com', 'password', 'Male'),
        ('normal@email.com', 'password', 'Male'),
    )
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.date = datetime.date(2022, 2, 7)
        self.holiday = HolidayFactory(
            organization=self.organization,
            date=self.date
        )
        self.normal_user = self.created_users[1]

        self.w_shift = WorkShiftFactory(organization=self.organization)
        for day in range(1, 8):
            work_day = WorkDayFactory(
                shift=self.w_shift, day=day, applicable_from=datetime.date(2022, 2, 1)
            )
            work_day.timings.all().delete()
            WorkTimingFactory(work_day=work_day)

        self.attendance_setting = IndividualAttendanceSettingFactory(
            user=self.normal_user
        )
        self.individual_user_shift = IndividualUserShiftFactory(
            shift=self.w_shift,
            individual_setting=self.attendance_setting,
            applicable_from=datetime.date(2022, 2, 1)
        )

    def test_delete_past_holiday(self):
        is_holiday = self.normal_user.is_holiday(self.date)
        self.assertTrue(is_holiday)
        populate_timesheet_for_user(
            self.normal_user, datetime.date(2022, 2, 5), datetime.date(2022, 2, 10),
            notify='false', authority=1
        )
        self.assertEqual(
            TimeSheet.objects.get(timesheet_for=self.date).coefficient,
            HOLIDAY
        )

        url = reverse(
            'api_v1:organization:organization-holiday-detail',
            kwargs={
                "slug": self.holiday.slug,
                "organization_slug": self.organization.slug
            }
        )
        response = self.client.delete(
            url
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )
        self.assertEqual(
            TimeSheet.objects.get(timesheet_for=self.date).coefficient,
            WORKDAY
        )

