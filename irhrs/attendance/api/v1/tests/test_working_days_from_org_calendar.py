from irhrs.common.api.tests.common import BaseTestCase as TestCase

from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY
from django.utils import timezone

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    WorkShiftFactory
from irhrs.attendance.constants import WORKDAY
from irhrs.attendance.models import TimeSheet, IndividualUserShift, WorkDay
from irhrs.attendance.utils.payroll import get_working_days_from_organization_calendar, \
    get_worked_days
from irhrs.core.utils.common import get_yesterday
from irhrs.users.api.v1.tests.factory import UserFactory


class TestWorkingDaysFromOrganizationCalendar(TestCase):

    def test_working_days_for_normal_user(self):
        """
        The user was joined before the payroll generation range,
        * the user is regular
        * 5 days per work
        * No Holiday (Sad life)
        :return:
        """
        user = UserFactory()
        user.detail.joined_date = timezone.now().date()-relativedelta(months=2)
        user.detail.save()
        ius = IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=user,
            ),
            shift=WorkShiftFactory(work_days=5),
            applicable_from=user.detail.joined_date
        )
        WorkDay.objects.filter(shift=ius.shift).update(applicable_from=ius.applicable_from)
        month_start = timezone.now().date().replace(day=1)
        month_end = month_start + relativedelta(months=1) - timezone.timedelta(days=1)
        for dt in rrule(
            freq=DAILY,
            dtstart=month_start,
            until=month_end
        ):
            TimeSheet.objects._create_or_update_timesheet_for_profile(
                user,
                dt
            )
        self.assertEqual(
            (month_end-month_start).days + 1,  # both inclusive
            user.timesheets.filter(
                timesheet_for__range=(month_start, month_end)
            ).count(),
            "Timesheets should have been created for all days for the month"
        )
        user_workday_count = user.timesheets.filter(
                timesheet_for__range=(month_start, month_end),
                coefficient=WORKDAY
            ).count()
        self.assertEqual(
            get_working_days_from_organization_calendar(
                user=user,
                start=month_start,
                end=month_end
            ),
            user_workday_count,
        )
        include_holiday_offday = get_working_days_from_organization_calendar(
                user=user,
                start=month_start,
                end=month_end,
                include_holiday_offday=True
            )
        self.assertEqual(
            include_holiday_offday,
            (month_end - month_start + timezone.timedelta(days=1)).days
        )

        self.assertEqual(
            get_worked_days(
                user=user,
                start=month_start,
                end=month_end,
                include_non_working_days=False
            ),
            0
        )
        self.assertEqual(
            get_worked_days(
                user=user,
                start=month_start,
                end=month_end,
                count_offday_holiday_as_worked=True
            ),
            include_holiday_offday - user_workday_count
        )
        self.assertEqual(
            get_worked_days(
                user=user,
                start=month_start,
                end=month_end,
                include_non_working_days=True
            ),
            0
        )

    def test_working_days_for_mid_join_employee(self):
        """
            The user was joined after the payroll generation range,
            * the user is regular
            * 5 days per work
        """
        # Two users will be tested. One is regular and one is irregular,
        # If the simulation engine is correct, the no. of working days
        # produced for both these users should be equal.
        user = UserFactory()
        user2 = UserFactory()
        today = timezone.now().date().replace(day=15)
        user.detail.joined_date = today
        user.detail.save()
        ius = IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=user,
            ),
            shift=WorkShiftFactory(work_days=5),
            applicable_from=today
        )
        WorkDay.objects.filter(shift=ius.shift).update(applicable_from=ius.applicable_from)

        ius = IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=user2,
            ),
            shift=WorkShiftFactory(work_days=5),
            applicable_from=today-relativedelta(months=2)
        )
        WorkDay.objects.filter(shift=ius.shift).update(applicable_from=ius.applicable_from)
        month_start = timezone.now().date().replace(day=1)
        month_end = month_start + relativedelta(months=1) - timezone.timedelta(days=1)
        for dt in rrule(
                freq=DAILY,
                dtstart=month_start,
                until=month_end
        ):
            TimeSheet.objects._create_or_update_timesheet_for_profile(
                user,
                dt
            )
            TimeSheet.objects._create_or_update_timesheet_for_profile(
                user2,
                dt
            )
        self.assertEqual(
            (month_end - today).days + 1,  # both inclusive
            user.timesheets.filter(
                timesheet_for__range=(month_start, month_end)
            ).count(),
            "Timesheets should have been created for partial days for the month"
        )
        self.assertEqual(
            get_working_days_from_organization_calendar(
                user=user,
                start=month_start,
                end=month_end
            ),
            user2.timesheets.filter(
                timesheet_for__range=(month_start, month_end),
                coefficient=WORKDAY
            ).count(),
            "The simulated working days for user should be equal to regular user's"
        )

    def test_working_days_for_hourly_employee(self):
        """
            The user was joined before the payroll generation range,
            * the user is paid on hourly basis
        """
        user = UserFactory()
        today = timezone.now().date() - relativedelta(months=2)
        user.detail.joined_date = today
        user.detail.save()
        IndividualAttendanceSettingFactory(
            user=user,
        )
        month_start = timezone.now().date().replace(day=1)
        month_end = month_start + relativedelta(months=1) - timezone.timedelta(days=1)
        for dt in rrule(
                freq=DAILY,
                dtstart=month_start,
                until=month_end
        ):
            TimeSheet.objects._create_or_update_timesheet_for_profile(
                user,
                dt
            )
        self.assertEqual(
            0,
            user.timesheets.filter(
                timesheet_for__range=(month_start, month_end)
            ).count(),
            "Timesheets should not have been created for the days of the month"
        )

        self.assertEqual(
            0,
            get_working_days_from_organization_calendar(
                user,
                month_start,
                month_end
            ),
            "Total Working days for hourly employee should be zero."
        )

    def test_working_days_for_hourly_mid_join_employee(self):
        """
            The user was joined after the payroll generation range,
            * the user is paid on hourly basis
        """
        user = UserFactory()
        today = timezone.now().date().replace(day=15)
        user.detail.joined_date = today
        user.detail.save()
        IndividualAttendanceSettingFactory(
            user=user,
        )
        month_start = timezone.now().date().replace(day=1)
        month_end = month_start + relativedelta(months=1) - timezone.timedelta(days=1)
        for dt in rrule(
                freq=DAILY,
                dtstart=month_start,
                until=month_end
        ):
            TimeSheet.objects._create_or_update_timesheet_for_profile(
                user,
                dt
            )
        self.assertEqual(
            0,
            user.timesheets.filter(
                timesheet_for__range=(month_start, month_end)
            ).count(),
            "Timesheets should not have been created for hourly employee"
        )

        self.assertEqual(
            0,
            get_working_days_from_organization_calendar(
                user,
                month_start,
                month_end
            ),
            "Total Working days for hourly employee should be zero."
        )
