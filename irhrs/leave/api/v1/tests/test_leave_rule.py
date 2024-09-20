from unittest import TestCase as UnitTestCase
from irhrs.leave.api.v1.serializers.rule import AccumulationRuleSerializer
from irhrs.leave.constants.model_constants import DAYS, MONTHS, YEARS


class LeaveAccumulationSerializerValidationTest(UnitTestCase):
    # Do not perform any database actions here, does not extends transaction test case

    def setUp(self) -> None:
        self.initial_data = {
            "duration": 10,
            "duration_type": DAYS,
            "balance_added": 1
        }

    def test_default_daily(self):
        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_default_monthly(self):
        self.initial_data["duration_type"] = MONTHS
        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_default_yearly(self):
        self.initial_data["duration_type"] = YEARS
        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_setting_daily_setting_without_setting_duration_to_daily(self):
        daily_setting_fields = [
            'exclude_absent_days',
            'exclude_off_days',
            'count_if_present_in_off_day',
            'exclude_holidays',
            'count_if_present_in_holiday',
            'exclude_unpaid_leave',
            'exclude_paid_leave',
            'exclude_half_leave'
        ]
        self.initial_data["duration_type"] = YEARS
        self.initial_data.update({field: True for field in daily_setting_fields})

        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertFalse(serializer.is_valid())
        for field in daily_setting_fields:
            self.assertEqual(serializer.errors.get(field),
                             ['This field can not be set when duration is not days.'],
                             field)

    def test_setting_all_settings_daily_true_with_duration_daily(self):
        daily_setting_fields = [
            'exclude_absent_days',
            'exclude_off_days',
            'count_if_present_in_off_day',
            'exclude_holidays',
            'count_if_present_in_holiday',
            'exclude_unpaid_leave',
            'exclude_paid_leave',
            'exclude_half_leave'
        ]
        self.initial_data.update({field: True for field in daily_setting_fields})

        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_exclude_off_day_false_count_if_present_in_off_day_true(self):
        self.initial_data["exclude_off_days"] = False
        self.initial_data["count_if_present_in_off_day"] = True

        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get('count_if_present_in_off_day'),
            ["This value can not be set when exclude off days is not set."]
        )

    def test_exclude_off_day_false_count_if_present_in_off_day_false(self):
        self.initial_data["exclude_off_days"] = False
        self.initial_data["count_if_present_in_off_day"] = False

        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_exclude_holiday_false_count_if_present_in_holiday_true(self):
        self.initial_data["exclude_holidays"] = False
        self.initial_data["count_if_present_in_holiday"] = True

        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors.get('count_if_present_in_holiday'),
            ["This value can not be set when exclude holidays is not set."]
        )

    def test_exclude_holiday_false_count_if_present_in_holiday_false(self):
        self.initial_data["exclude_holidays"] = False
        self.initial_data["count_if_present_in_holiday"] = False

        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_exclude_half_leave_true_with_both_leave_false(self):
        self.initial_data["exclude_half_leave"] = True
        self.initial_data["exclude_paid_leave"] = False
        self.initial_data["exclude_unpaid_leave"] = False

        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors.get('exclude_half_leave'),
                         ["To set this value at least one of 'exclude unpaid leave' "
                          "or 'exclude paid leave'"
                          "must be set."]
                         )

    def test_exclude_half_leave_true_with_one_of_leave_false(self):
        self.initial_data["exclude_half_leave"] = True
        self.initial_data["exclude_paid_leave"] = True
        self.initial_data["exclude_unpaid_leave"] = False

        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        self.initial_data["exclude_paid_leave"] = False
        self.initial_data["exclude_unpaid_leave"] = True
        serializer = AccumulationRuleSerializer(data=self.initial_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
