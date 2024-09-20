from dateutil import rrule

from irhrs.attendance.api.v1.tests.factory import TimeSheetFactory
from irhrs.attendance.constants import OFFDAY, WORKDAY
from irhrs.attendance.utils.payroll import get_work_duration
from irhrs.common.api.tests.common import BaseTestCase
from irhrs.core.utils.common import combine_aware, humanize_interval
from irhrs.users.api.v1.tests.factory import UserFactory
from datetime import date, time, timedelta


def extract_date(timestamp):
    return timestamp.astimezone().date()


class TestWorkedDuration(BaseTestCase):

    def test_worked_hours_no_shift(self):
        start, until = date(2017, 1, 1), date(2017, 1, 31)
        dates = list(
            map(
                extract_date,
                rrule.rrule(rrule.DAILY, dtstart=start, until=until)
            )
        )
        for test_case in (
            # worked hours,      break hours,        punch in,    punch out,   expected result
            (timedelta(hours=9), timedelta(hours=0), time(9, 0), time(18, 0), timedelta(hours=9*31)),
            (timedelta(hours=8), timedelta(hours=0), time(9, 0), time(17, 0), timedelta(hours=8*31)),
            (timedelta(hours=8), timedelta(hours=2), time(9, 0), time(17, 0), timedelta(hours=6*31)),
        ):
            user = UserFactory()
            worked_hours, unpaid_break_hours, start_time, end_time, expected_result = test_case
            for day in dates:
                TimeSheetFactory(
                    timesheet_user=user,
                    timesheet_for=day,
                    punch_in=combine_aware(day, start_time),
                    punch_out=combine_aware(day, end_time),
                    worked_hours=(worked_hours-unpaid_break_hours),
                    unpaid_break_hours=unpaid_break_hours
                )
            actual_worked_hours = humanize_interval(
                get_work_duration(user=user, start=start, end=until)
            )
            with self.subTest():
                self.assertEqual(
                    actual_worked_hours,
                    humanize_interval(expected_result),
                    "Expected %s Got %s" % (humanize_interval(expected_result), actual_worked_hours)
                )

    def test_worked_hours_with_shift(self):
        start, until = date(2017, 1, 1), date(2017, 1, 31)
        dates = list(
            map(
                extract_date,
                rrule.rrule(rrule.DAILY, dtstart=start, until=until)
            )
        )

        def get_coefficient(day):
            # 2021-01-01 --> 2021-01-31 ==> {6, 12, 18, 24, 30}
            ret = OFFDAY if day % 6 == 0 else WORKDAY
            return ret

        for test_case in (
            # worked hours,      break hours,        punch in,    punch out,   expected result
            (timedelta(hours=9), timedelta(hours=0), time(9, 0), time(18, 0), timedelta(hours=9*26)),
            (timedelta(hours=8), timedelta(hours=0), time(9, 0), time(17, 0), timedelta(hours=8*26)),
            (timedelta(hours=8), timedelta(hours=2), time(9, 0), time(17, 0), timedelta(hours=6*26)),
        ):
            user = UserFactory()
            worked_hours, unpaid_break_hours, start_time, end_time, expected_result = test_case
            for day in dates:
                coefficient = get_coefficient(day.day)
                wkday = coefficient == WORKDAY
                TimeSheetFactory(
                    timesheet_user=user,
                    timesheet_for=day,
                    punch_in=combine_aware(day, start_time) if wkday else None,
                    punch_out=combine_aware(day, end_time) if wkday else None,
                    worked_hours=(worked_hours-unpaid_break_hours),
                    unpaid_break_hours=unpaid_break_hours,
                    coefficient=coefficient
                )
            actual_worked_hours = humanize_interval(
                get_work_duration(user=user, start=start, end=until)
            )
            with self.atomicSubTest():
                self.assertEqual(
                    actual_worked_hours,
                    humanize_interval(expected_result),
                    "Expected %s Got %s" % (humanize_interval(expected_result), actual_worked_hours)
                )
