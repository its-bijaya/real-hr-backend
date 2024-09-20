import itertools

from irhrs.common.api.tests.common import BaseTestCase as TestCase
from django.utils import timezone

from irhrs.attendance.api.v1.tests.factory import WorkShiftFactory2
from irhrs.attendance.utils.timesheet import simulate_timesheets
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import HolidayFactory
from irhrs.organization.models import Holiday, HolidayRule
from irhrs.users.api.v1.tests.factory import UserFactory


class TestSimulateTimeSheets(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_count_work_days(self):
        work_days_count = 5
        no_of_weeks = 4

        work_shift = WorkShiftFactory2(work_days=work_days_count)
        # building for entire week, so that 2 off-days are confirmed
        end_date = get_today()

        # (7 * no_of_weeks) -1 because start date is inclusive
        start_date = end_date - timezone.timedelta(days=(7 * no_of_weeks) - 1)

        expected_work_days_count = work_days_count * no_of_weeks

        virtual_timesheets = simulate_timesheets(
            self.user,
            work_shift,
            start_date,
            end_date
        )
        counts = self.get_counts_for_values(values=virtual_timesheets)

        self.assertEqual(counts["Workday"], expected_work_days_count)

    def test_get_count_work_days_with_holidays(self):
        work_days_count = 5
        no_of_weeks = 4

        work_shift = WorkShiftFactory2(work_days=work_days_count)
        today = get_today()

        # monday (so that holidays are not in off days)
        end_date = today - timezone.timedelta(today.weekday())

        HolidayFactory(date=end_date - timezone.timedelta(days=2),
                       organization=self.user.detail.organization)
        HolidayFactory(date=end_date - timezone.timedelta(days=3),
                       organization=self.user.detail.organization)

        holiday_count = 2

        # (7 * no_of_weeks) -1 because start date is inclusive
        start_date = end_date - timezone.timedelta(days=(7 * no_of_weeks) - 1)

        virtual_timesheets = simulate_timesheets(
            self.user,
            work_shift,
            start_date,
            end_date
        )
        counts = self.get_counts_for_values(values=virtual_timesheets)

        self.assertEqual(counts["Holiday"], holiday_count)
        self.assertEqual(counts["Workday"], work_days_count * no_of_weeks - holiday_count)

        # test for ignore holidays
        virtual_timesheets = simulate_timesheets(
            self.user,
            work_shift,
            start_date,
            end_date,
            ignore_holidays=True
        )
        counts = self.get_counts_for_values(values=virtual_timesheets)

        # If holidays are ignored then the value must be 0 and not included in keys
        self.assertNotIn('Holiday', counts)
        self.assertEqual(counts["Workday"], work_days_count * no_of_weeks)

    @staticmethod
    def get_counts_for_values(values: dict) -> dict:
        sorted_values = sorted(values.items(), key=lambda ts: ts[1])
        groups = itertools.groupby(sorted_values, key=lambda ts: ts[1])

        return {key: len(list(val)) for key, val in groups}

    def tearDown(self) -> None:
        Holiday.objects.all().delete()
