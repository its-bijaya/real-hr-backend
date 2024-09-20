"""
Test for Normal User's Attendance Calendar
    # Scenarios Tested:
        * Absent Timesheet for a date [Missing Punch In Scenario]
        * Missing Punch Out Scenario
        * Valid Punch In/Out
        * First Half Leave
        * Second Half Leave
        * Full Leave

    # Actions Tested:
        * Attendance Adjustment [Ignored to be tested from Attendance Adjustment Test Case]
        * Leave Request [Ignored to be tested from Leave Request Test Case]
        # Note: Both of these actions use the same API
"""
from datetime import time
from irhrs.common.api.tests.common import BaseTestCase as TestCase

import factory
from factory.django import DjangoModelFactory
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from faker import Faker
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    WorkShiftFactory
from irhrs.attendance.constants import DEVICE, WORKDAY, HOLIDAY, OFFDAY, TIMESHEET_COEFFICIENTS, \
    FIRST_HALF, LEAVE_COEFFICIENTS, SECOND_HALF, FULL_LEAVE
from irhrs.attendance.models import TimeSheet, IndividualUserShift, WorkDay
from irhrs.common.models import HolidayCategory
from irhrs.core.utils import nested_get
from irhrs.core.utils.common import combine_aware
from irhrs.organization.models import Holiday, HolidayRule
from irhrs.users.api.v1.tests.factory import UserFactory

timedelta = timezone.timedelta


class TestNormalUserCalendar(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(
            self.user
        )
        ius = IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user,
            ),
            shift=WorkShiftFactory(work_days=7),
            applicable_from=timezone.now().date() - timezone.timedelta(days=50)
        )
        WorkDay.objects.filter(shift=ius.shift).update(applicable_from=ius.applicable_from)

    @property
    def attendance_url(self):
        return reverse(
            'api_v1:attendance:attendance-calendar-list',
        )

    def _create_timesheet(self, date_=timezone.now().date()):
        TimeSheet.objects._create_or_update_timesheet_for_profile(
            self.user,
            date_
        )
        return self.user.timesheets.filter(timesheet_for=date_).first()

    @staticmethod
    def find_corresponding_timesheet(response, date_):
        """
        Returns specific timesheet for a date from attendance calendar results.
        """
        return next(
            filter(
                lambda x: x.get('timesheet_for') == date_.strftime('%Y-%m-%d'),
                response.json().get('results'),
            ),
            {}
        )

    def test_absent_timesheet(self):
        """
        When No attendance Entry is detected,
        the entry for this date should be shown as `Absent`.
        """
        date_to_be_tested = timezone.now().date()-timedelta(days=1)
        if date_to_be_tested.strftime('%w') in ['0', '6']:
            date_to_be_tested = date_to_be_tested - timedelta(days=3)
        self._create_timesheet(date_to_be_tested)
        response = self.client.get(
            self.attendance_url,
            data={
                'organization_slug': self.user.detail.organization.slug,
                'start': date_to_be_tested-timedelta(1),
                'end': date_to_be_tested+timedelta(1),
            }
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        category = {
            '0': 'Offday',
            '1': 'Absent',
            '2': 'Absent',
            '3': 'Absent',
            '4': 'Absent',
            '5': 'Absent',
            '6': 'Offday',
        }.get(date_to_be_tested.strftime('%w'))
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('title'),
            category
        )

    def test_missing_punch_out(self):
        """
        When No Punch Out entry is detected,
        the entry for this date should be shown as `{PunchTime-Missing}`.
        """
        date_to_be_tested = timezone.now().date() - timezone.timedelta(days=2)
        timesheet = self._create_timesheet(date_to_be_tested)
        punch_time = time(10, 0)
        with transaction.atomic():
            TimeSheet.objects.clock(
                timesheet.timesheet_user,
                combine_aware(
                    timesheet.timesheet_for,
                    punch_time
                ),
                DEVICE
            )
        response = self.get_attendance_response(date_to_be_tested)
        response_object = self.find_corresponding_timesheet(
            response,
            date_to_be_tested
        )
        self.assertEqual(
            response_object.get('title'),
            f'{punch_time} - Missing'
        )
        self.assertEqual(
            response_object.get('coefficient'),
            self.get_timesheet_coefficient(date_to_be_tested)
        )

    def test_valid_timesheet(self):
        """
            When Valid Punch In and Punch Out is available,
            the title should read `{PunchIn} - {PunchOut}`
        """
        date_to_be_tested = timezone.now().date() - timezone.timedelta(days=3)
        timesheet = self._create_timesheet(date_to_be_tested)
        punch_in = time(9, 0)
        punch_out = time(18, 0)
        with transaction.atomic():
            TimeSheet.objects.clock(
                timesheet.timesheet_user,
                combine_aware(
                    timesheet.timesheet_for,
                    punch_in
                ),
                DEVICE
            )
            TimeSheet.objects.clock(
                timesheet.timesheet_user,
                combine_aware(
                    timesheet.timesheet_for,
                    punch_out
                ),
                DEVICE
            )
        response = self.get_attendance_response(date_to_be_tested)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('title'),
            f'{punch_in} - {punch_out}'
        )
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('coefficient'),
            self.get_timesheet_coefficient(date_to_be_tested)
        )

    def test_first_half_leave(self):
        """
            When First Half Leave is Applied,
            the title should read `[FH] {Leave Type}`
            If Leave is not available, it will be `First Half Leave`
        """
        date_to_be_tested = timezone.now().date() - timezone.timedelta(days=4)
        timesheet = self._create_timesheet(date_to_be_tested)
        timesheet.leave_coefficient = FIRST_HALF
        timesheet.save()
        response = self.get_attendance_response(date_to_be_tested)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('title'),
            f'First Half Leave'
            # This is result due to absence of a valid Leave Request.
            # When exists, it will result in something like: `[FH] Casual Leave`
        )
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('coefficient'),
            self.get_timesheet_coefficient(date_to_be_tested)
        )
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('leave_coefficient'),
            dict(LEAVE_COEFFICIENTS).get(FIRST_HALF)
        )

    def test_second_half_leave(self):
        """
            When Second Half Leave is Applied,
            the title should read `[SH] {Leave Type}`
            If Leave is not available, it will be `Second Half Leave`
        """
        date_to_be_tested = timezone.now().date() - timezone.timedelta(days=5)
        timesheet = self._create_timesheet(date_to_be_tested)
        timesheet.leave_coefficient = SECOND_HALF
        timesheet.save()
        response = self.get_attendance_response(date_to_be_tested)
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('title'),
            f'Second Half Leave'
            # This is result due to absence of a valid Leave Request.
            # When exists, it will result in something like: `[SH] Casual Leave`
        )
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('coefficient'),
            self.get_timesheet_coefficient(date_to_be_tested)
        )
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('leave_coefficient'),
            dict(LEAVE_COEFFICIENTS).get(SECOND_HALF)
        )

    def test_full_leave(self):
        """
            When Second Half Leave is Applied,
            the title should read `[FL] {Leave Type}`
            If Leave is not available, it will be `Full Leave`
        """
        date_to_be_tested = timezone.now().date() - timezone.timedelta(days=6)
        timesheet = self._create_timesheet(date_to_be_tested)
        timesheet.leave_coefficient = FULL_LEAVE
        timesheet.save()
        response = self.get_attendance_response(date_to_be_tested)
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('title'),
            f'Full Leave'
            # This is result due to absence of a valid Leave Request.
            # When exists, it will result in something like: `[SH] Casual Leave`
        )
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('coefficient'),
            self.get_timesheet_coefficient(date_to_be_tested)
        )
        self.assertEqual(
            self.find_corresponding_timesheet(
                response,
                date_to_be_tested
            ).get('leave_coefficient'),
            dict(LEAVE_COEFFICIENTS).get(FULL_LEAVE)
        )

    def test_zz_off_day(self):
        # ZZ will ensure, this will run at last
        self.user = UserFactory()
        self.client.force_login(self.user)
        IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user,
            ),
            shift=WorkShiftFactory(work_days=0),
            applicable_from=timezone.now().date() - timezone.timedelta(days=50)
        )
        self._create_timesheet(timezone.now().date())
        response = self.get_attendance_response(timezone.now().date())
        resp = self.find_corresponding_timesheet(response, timezone.now().date())
        self.assertEqual(
            resp.get('title'),
            dict(TIMESHEET_COEFFICIENTS).get(OFFDAY)
        )

    def test_zz_holiday(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user,
            ),
            shift=WorkShiftFactory(work_days=7),
            applicable_from=timezone.now().date() - timezone.timedelta(days=50)
        )
        self.user.detail.date_of_birth = timezone.now().date() - relativedelta(years=30)
        self.user.detail.save()
        # Holiday
        cat = HolidayCategory.objects.create(name=Faker().first_name())
        holiday_name = Faker().first_name()
        holiday = Holiday.objects.create(
            category=cat,
            organization=self.user.detail.organization,
            name=holiday_name,
            date=timezone.now().date()
        )
        HolidayRule.objects.create(
            lower_age=15,
            upper_age=90,
            gender='All',
            holiday=holiday
        )

        # /Holiday
        self._create_timesheet(timezone.now().date())
        response = self.get_attendance_response(timezone.now().date())
        resp = self.find_corresponding_timesheet(response, timezone.now().date())
        self.assertEqual(
            resp.get('title'),
            holiday_name.upper()
        )

    # def test_attendance_adjustment(self):
    #     # To Be Tested in Attendance Adjustment Test Case
    #     pass
    #
    # def test_leave_request(self):
    #     # To Be tested in Leave Request Test Case
    #     pass

    def get_attendance_response(self, date_to_be_tested):
        response = self.client.get(
            self.attendance_url,
            data={
                'organization_slug': self.user.detail.organization.slug,
                'start': date_to_be_tested - timedelta(1),
                'end': date_to_be_tested + timedelta(1),
            }
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        return response

    def get_timesheet_coefficient(self, date_to_be_tested):
        coefficient_displays = dict(TIMESHEET_COEFFICIENTS)
        if self.user.is_holiday(date_to_be_tested):
            return coefficient_displays.get(HOLIDAY)
        elif self.user.is_offday(date_to_be_tested):
            return coefficient_displays.get(OFFDAY)
        else:
            return coefficient_displays.get(WORKDAY)
