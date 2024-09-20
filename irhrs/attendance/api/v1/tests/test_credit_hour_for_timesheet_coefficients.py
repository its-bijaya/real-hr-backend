

# def test_credit_hours_earned():
#
import random
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from irhrs.attendance.tasks.credit_hours import get_earned_credit
from irhrs.attendance.constants import WORKDAY, OFFDAY, HOLIDAY
from irhrs.core.utils.common import DummyObject


class TestCreditHoursUtil(TestCase):
    def test_credit_hours_earned_for_workday(self):
        """
        get_earned_credit(
            current_credit, adjacent_timesheet, credit_setting,
             reserved=ZERO_CREDIT
         )
        """
        # Begin Payload
        credit_setting = DummyObject(
            reduce_credit_if_actual_credit_lt_approved_credit=True
        )
        sample_scenarios = [
            # Punch in delta/Punch out Delta 0, approved 2, reserved 0, output 0
            (0, 0, 2, 0, 0),
            (1, 1, 2, 0, 2),
            (3, 0, 2, 0, 2),
            (0, 3, 4, 0, 3),
            (1.5, 2, 3, 1, 2.5),
            (1, 1, 2, 2, 0),
        ]
        for pid, pod, approved, reserved, output in sample_scenarios:
            adjacent_timesheet = DummyObject(
                punch_in_delta=timedelta(hours=-pid),
                punch_out_delta=timedelta(hours=pod),
                unpaid_break_hours=None,
                coefficient=WORKDAY
            )
            current_credit = timedelta(hours=approved)
            reserved = timedelta(hours=reserved)
            result = get_earned_credit(
                current_credit=current_credit,
                adjacent_timesheet=adjacent_timesheet,
                credit_setting=credit_setting,
                reserved=reserved
            )
            self.assertEqual(
                timedelta(hours=output),
                result,
                f"On {pid} pid, {pod} pod, {approved} approved,"
                f"{reserved} reserved, {output} should be returned. Got {result}"
            )

    def test_credit_hours_earned_for_off_day_holiday(self):
        """
        get_earned_credit(
            current_credit, adjacent_timesheet, credit_setting,
             reserved=ZERO_CREDIT
         )
        """
        # Begin Payload
        credit_setting = DummyObject(
            reduce_credit_if_actual_credit_lt_approved_credit=True
        )
        sample_scenarios = [
            # Punch in delta/Punch out Delta 0, approved 2, reserved 0, output 0
            (0, 0, 2, 0, 0),
            (1, 1, 2, 0, 2),
            (3, 0, 2, 0, 2),
            (0, 3, 4, 0, 3),
            (1.5, 2, 3, 1, 2.5),
            (1, 1, 2, 2, 0),
        ]
        pi = timezone.now().replace(hour=9)
        for pid, pod, approved, reserved, output in sample_scenarios:
            adjacent_timesheet = DummyObject(
                punch_in_delta=None,
                punch_out_delta=None,
                punch_in=pi + timedelta(hours=-pid),
                punch_out=pi + timedelta(hours=pod),
                unpaid_break_hours=None,
                coefficient=random.choice([OFFDAY, HOLIDAY])
            )
            current_credit = timedelta(hours=approved)
            reserved = timedelta(hours=reserved)
            result = get_earned_credit(
                current_credit=current_credit,
                adjacent_timesheet=adjacent_timesheet,
                credit_setting=credit_setting,
                reserved=reserved
            )
            self.assertEqual(
                timedelta(hours=output),
                result,
                f"On {pid} pid, {pod} pod, {approved} approved,"
                f"{reserved} reserved, {output} should be returned. Got {result}"
            )

    def test_credit_hours_earned_for_no_reduction(self):
        current_credit = timedelta(hours=8)
        credit_setting = DummyObject(
            reduce_credit_if_actual_credit_lt_approved_credit=False
        )
        self.assertEqual(
            current_credit,
            get_earned_credit(
                current_credit,
                adjacent_timesheet=None,
                credit_setting=credit_setting,
            ),
            "When No reduction is set, current credit should be equal to current credit"
        )

        reserved = timedelta(hours=2)
        self.assertEqual(
            current_credit-reserved,
            get_earned_credit(
                current_credit,
                adjacent_timesheet=None,
                credit_setting=credit_setting,
                reserved=reserved
            ),
            "No reduction and reserved is set, current credit should be equal to current-reserved"
        )
