from unittest.mock import patch

from irhrs.common.api.tests.common import BaseTestCase as TestCase
from django.utils import timezone

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, WorkShiftFactory
from irhrs.attendance.constants import WH_WEEKLY
from irhrs.attendance.models import IndividualAttendanceSetting, IndividualUserShift
from irhrs.core.utils.common import DummyObject, get_today


class TestWorkShiftGetterSetter(TestCase):

    def test_work_shift_getter_setter(self):
        setting = IndividualAttendanceSettingFactory()
        work_shift_1 = WorkShiftFactory()
        work_shift_2 = WorkShiftFactory()

        # first set a work_shift
        setting.work_shift = work_shift_1

        self.assertEqual(setting.work_shift, work_shift_1)
        self.assertTrue(
            IndividualUserShift.objects.filter(
                individual_setting=setting,
                shift=work_shift_1, applicable_to__isnull=True
            ).exists()
        )

        # update the shift: should be applicable from next day
        setting.work_shift = work_shift_2
        self.assertEqual(setting.work_shift, work_shift_1)
        self.assertTrue(
            IndividualUserShift.objects.filter(
                individual_setting=setting,
                shift=work_shift_1, applicable_to=get_today()
            ).exists()
        )
        self.assertTrue(
            IndividualUserShift.objects.filter(
                individual_setting=setting,
                shift=work_shift_2, applicable_to__isnull=True
            ).exists()
        )

        # check what happens tomorrow
        with patch('django.utils.timezone.now', return_value=timezone.now() + timezone.timedelta(days=1)):
            setting = IndividualAttendanceSetting.objects.get(id=setting.id)
            self.assertNotEqual(setting.work_shift, work_shift_1)
            self.assertEqual(setting.work_shift, work_shift_2)

    def test_work_shift_delete(self):
        setting = IndividualAttendanceSettingFactory()
        work_shift = WorkShiftFactory()

        # first set a work_shift
        setting.work_shift = work_shift

        self.assertEqual(setting.work_shift, work_shift)
        self.assertTrue(
            IndividualUserShift.objects.filter(
                individual_setting=setting,
                shift=work_shift, applicable_to__isnull=True
            ).exists()
        )

        setting.work_shift = None
        self.assertEqual(setting.work_shift, work_shift)
        self.assertTrue(
            IndividualUserShift.objects.filter(
                individual_setting=setting,
                shift=work_shift, applicable_to=get_today()
            ).exists()
        )

        # check what happens tomorrow
        with patch('django.utils.timezone.now', return_value=timezone.now() + timezone.timedelta(days=1)):
            setting = IndividualAttendanceSetting.objects.get(id=setting.id)
            self.assertIsNone(setting.work_shift)


class TestWorkingHourGetterSetter(TestCase):

    def test_working_hours_getter_setter(self):
        setting = IndividualAttendanceSettingFactory()

        # test initial insertion
        working_hour_object = DummyObject(working_hours=10, working_hours_duration=WH_WEEKLY)

        setting.working_hour = working_hour_object

        from_obj = setting.working_hour

        self.assertIsNotNone(from_obj)
        self.assertIsNone(from_obj.applicable_to)
        self.assertEqual(working_hour_object.working_hours, setting.working_hours)
        self.assertEqual(working_hour_object.working_hours_duration, setting.working_hours_duration)

        # test update case
        new_working_hour = DummyObject(working_hours=20, working_hours_duration=WH_WEEKLY)
        setting.working_hour = new_working_hour

        # recreate setting instance due to cached property
        setting = IndividualAttendanceSetting.objects.get(id=setting.id)

        # previous setting should exist with effective till today
        from_obj_2 = setting.working_hour
        self.assertEqual(from_obj_2.applicable_to, get_today())
        self.assertEqual(working_hour_object.working_hours, setting.working_hours)
        self.assertEqual(working_hour_object.working_hours_duration, setting.working_hours_duration)

        # there must be new work hour with new settings and applicable_from tomorrow
        self.assertTrue(setting.individual_setting_working_hours.filter(
            applicable_from=get_today() + timezone.timedelta(days=1),
            applicable_to__isnull=True,
            working_hours=new_working_hour.working_hours,
            working_hours_duration=new_working_hour.working_hours_duration
        ).exists())

        # check what happens tomorrow
        with patch('django.utils.timezone.now', return_value=timezone.now() + timezone.timedelta(days=1)):
            setting = IndividualAttendanceSetting.objects.get(id=setting.id)
            self.assertEqual(new_working_hour.working_hours, setting.working_hours)
            self.assertEqual(new_working_hour.working_hours_duration, setting.working_hours_duration)

    def test_working_hour_delete(self):
        setting = IndividualAttendanceSettingFactory()

        # test initial insertion
        working_hour_object = DummyObject(working_hours=10, working_hours_duration=WH_WEEKLY)

        setting.working_hour = working_hour_object

        from_obj = setting.working_hour

        self.assertIsNotNone(from_obj)
        self.assertIsNone(from_obj.applicable_to)

        # test delete
        # recreate setting instance due to cached property
        setting = IndividualAttendanceSetting.objects.get(id=setting.id)
        setting.working_hour = None
        from_obj_3 = setting.working_hour

        # since tomorrow isn't here, values should be of first one
        self.assertEqual(from_obj_3.applicable_to, get_today())
        self.assertEqual(working_hour_object.working_hours, setting.working_hours)
        self.assertEqual(working_hour_object.working_hours_duration, setting.working_hours_duration)

        # check what happens tomorrow
        with patch('django.utils.timezone.now', return_value=timezone.now() + timezone.timedelta(days=1)):
            updated_setting_instance = IndividualAttendanceSetting.objects.get(id=setting.id)
            self.assertIsNone(updated_setting_instance.working_hour)
            self.assertIsNone(updated_setting_instance.working_hours)
            self.assertIsNone(updated_setting_instance.working_hours_duration)


class TestWorkShiftWithWorkingHours(TestCase):

    def test_working_hours_getter_setter_with_work_shift(self):
        setting = IndividualAttendanceSettingFactory()
        work_shift = WorkShiftFactory()

        # first set a shift
        setting.work_shift = work_shift
        self.assertTrue(
            IndividualUserShift.objects.filter(
                individual_setting=setting, shift=work_shift, applicable_to__isnull=True
            ).exists()
        )

        # now set work hour
        work_hour = DummyObject(working_hours=10, working_hours_duration=WH_WEEKLY)
        setting.working_hour = work_hour

        # work shift should be set and no work hour
        self.assertEqual(setting.work_shift, work_shift)

        self.assertTrue(
            IndividualUserShift.objects.filter(
                individual_setting=setting, shift=work_shift,  applicable_to=get_today()
            ).exists()
        )

        self.assertIsNone(setting.working_hour)

        # next day shift should be none and work day should be set
        with patch('django.utils.timezone.now', return_value=timezone.now() + timezone.timedelta(days=1)):
            setting_2 = IndividualAttendanceSetting.objects.get(id=setting.id)
            self.assertIsNone(setting_2.work_shift)
            self.assertIsNotNone(setting_2.working_hour)
            self.assertEqual(work_hour.working_hours, setting.working_hours)
            self.assertEqual(work_hour.working_hours_duration, setting.working_hours_duration)

    def test_work_shift_getter_setter_with_work_days(self):
        setting = IndividualAttendanceSettingFactory()
        work_shift = WorkShiftFactory()
        work_hour = DummyObject(working_hours=10, working_hours_duration=WH_WEEKLY)

        setting.working_hour = work_hour

        self.assertTrue(
            setting.individual_setting_working_hours.filter(
                working_hours=10, working_hours_duration=WH_WEEKLY,
                applicable_to__isnull=True
            ).exists()
        )

        setting.work_shift = work_shift

        # work day with applicable_to None should not exist
        self.assertFalse(
            setting.individual_setting_working_hours.filter(
                working_hours=10, working_hours_duration=WH_WEEKLY,
                applicable_to__isnull=True
            ).exists()
        )

        # next day shift should be none and work day should be set
        with patch('django.utils.timezone.now', return_value=timezone.now() + timezone.timedelta(days=1)):
            setting_2 = IndividualAttendanceSetting.objects.get(id=setting.id)
            self.assertEqual(setting_2.work_shift, work_shift)
            self.assertIsNone(setting_2.working_hour)
            self.assertIsNone(setting.working_hours)
            self.assertIsNone(setting.working_hours_duration)
