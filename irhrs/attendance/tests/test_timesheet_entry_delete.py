from django.test import TestCase
from django.utils import timezone

from irhrs.attendance.api.v1.tests.factory import TimeSheetFactory, TimeSheetEntryFactory, \
    IndividualAttendanceSettingFactory
from irhrs.attendance.constants import WEB_APP
from irhrs.attendance.models import TimeSheet
from irhrs.core.utils.common import get_today


class TestTimeSheetEntryDelete(TestCase):
    def setUp(self) -> None:
        self.timesheet = TimeSheetFactory(is_present=True)
        self.attendance_settings = IndividualAttendanceSettingFactory(
            user=self.timesheet.timesheet_user)
        today = get_today(with_time=True)
        self.dt1 = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=9,
                                     minute=0, tzinfo=today.tzinfo)
        self.dt2 = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=10,
                                     minute=0, tzinfo=today.tzinfo)
        self.dt3 = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=11,
                                     minute=0, tzinfo=today.tzinfo)
        self.dt4 = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=12,
                                     minute=0, tzinfo=today.tzinfo)
        self.entry1 = TimeSheetEntryFactory(timesheet=self.timesheet, timestamp=self.dt1,)
        self.entry2 = TimeSheetEntryFactory(timesheet=self.timesheet, timestamp=self.dt2)
        self.entry3 = TimeSheetEntryFactory(timesheet=self.timesheet, timestamp=self.dt3)
        self.entry4 = TimeSheetEntryFactory(timesheet=self.timesheet, timestamp=self.dt4)
        self.timesheet.fix_entries()

        # setup check
        self.assertEqual(self.timesheet.punch_in, self.dt1)
        self.assertEqual(self.timesheet.punch_out, self.dt4)

    def test_timesheet_entry_delete(self):

        # delete punch in record
        self.entry1.soft_delete()
        self.assertEqual(self.timesheet.punch_in, self.dt2)
        self.assertEqual(self.timesheet.punch_out, self.dt4)
        self.assertTrue(self.timesheet.is_present)

        # delete punch out record
        self.entry4.soft_delete()
        self.assertEqual(self.timesheet.punch_in, self.dt2)
        self.assertEqual(self.timesheet.punch_out, self.dt3)
        self.assertTrue(self.timesheet.is_present)

    def test_revert_soft_delete(self):

        # delete punch in record
        self.entry1.soft_delete()
        self.assertEqual(self.timesheet.punch_in, self.dt2)
        self.assertEqual(self.timesheet.punch_out, self.dt4)

        # revert back
        self.entry1.revert_soft_delete()
        self.assertEqual(self.timesheet.punch_in, self.dt1)
        self.assertEqual(self.timesheet.punch_out, self.dt4)

    def test_timesheet_entry_delete_on_timesheet_with_only_two_entries(self):
        timesheet = TimeSheetFactory(
            timesheet_user=self.timesheet.timesheet_user,
            timesheet_for=(self.timesheet.timesheet_for + timezone.timedelta(days=1)),
            is_present=True
        )
        entry1 = TimeSheetEntryFactory(timesheet=timesheet, timestamp=self.dt1,)
        entry2 = TimeSheetEntryFactory(timesheet=timesheet, timestamp=self.dt2,)
        timesheet.fix_entries()

        timesheet.refresh_from_db()
        self.assertTrue(timesheet.is_present)

        entry1.soft_delete()
        entry2.soft_delete()

        timesheet.refresh_from_db()
        self.assertFalse(timesheet.is_present)
        self.assertIsNone(timesheet.punch_in)
        self.assertIsNone(timesheet.punch_out)

    def test_clocking_timesheet_with_timestamp_of_deleted_entry(self):
        self.entry1.soft_delete()
        self.assertEqual(self.timesheet.punch_in, self.dt2)
        self.assertEqual(self.timesheet.punch_out, self.dt4)
        self.assertTrue(self.timesheet.is_present)

        self.entry1.refresh_from_db()
        self.assertTrue(self.entry1.is_deleted)

        TimeSheet.objects.clock(
            user=self.timesheet.timesheet_user,
            date_time=self.dt1,
            entry_method=WEB_APP
        )

        self.timesheet.refresh_from_db()
        self.entry1.refresh_from_db()
        from datetime import timezone, timedelta
        punch_in_local = self.timesheet.punch_in.astimezone(
            timezone(timedelta(hours=5, minutes=45))).replace(hour=self.dt1.hour,
                                                              minute=self.dt1.minute)

        self.assertEqual(punch_in_local, self.dt1)
        self.assertFalse(self.entry1.is_deleted)
