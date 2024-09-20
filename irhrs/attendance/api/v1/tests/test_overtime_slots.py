from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from irhrs.attendance.models import OvertimeSetting
from irhrs.attendance.utils.overtime_utils import slot_trim_overtime
from irhrs.common.api.tests.common import BaseTestCase
from irhrs.permission.constants.permissions import ATTENDANCE_OVERTIME_PERMISSION
from irhrs.users.api.v1.tests.factory import UserFactory

OVERTIME_SETTING_PAYLOAD = {
    "name": "Test Setting",
    "minimum_request_duration": None,
    "daily_overtime_limit_applicable": False,
    "daily_overtime_limit": None,
    "weekly_overtime_limit_applicable": False,
    "weekly_overtime_limit": None,
    "monthly_overtime_limit": None,
    "monthly_overtime_limit_applicable": False,
    "off_day_overtime": False,
    "off_day_overtime_limit": None,
    "applicable_before": 0,
    "applicable_after": 0,
    "overtime_calculation": 1,
    "require_dedicated_work_time": True,
    "paid_holiday_affect_overtime": False,
    "flat_reject_value": 0,
    "holiday_overtime_limit": None,
    "leave_affect_overtime": False,
    "leave_overtime_limit": None,
    "rates": [],
    "overtime_after_offday": "both",
    "require_prior_approval": False,
    "require_post_approval_of_pre_approved_overtime": None,
    "grant_compensatory_time_off_for_exceeded_minutes": None,
    "reduce_ot_if_actual_ot_lt_approved_ot": None,
    "allow_edit_of_pre_approved_overtime": None,
}


class TestOvertimeSlots(BaseTestCase):
    # @API Test
    def test_can_create_overtime_setting_with_overtime_slots(self):
        admin = UserFactory()
        self.client.force_login(admin)
        with patch.object(
            get_user_model(),
            'get_hrs_permissions',
            return_value={ATTENDANCE_OVERTIME_PERMISSION['code']}
        ):
            post_response = self.client.post(
                self.overtime_setting_url(organization=admin.detail.organization),
                data={
                    **OVERTIME_SETTING_PAYLOAD,
                    'calculate_overtime_in_slots': True,
                    'slot_duration_in_minutes': 30,
                    'slot_behavior_for_remainder': 'up',
                },
                content_type='application/json'
            )
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            OvertimeSetting.objects.filter(
                organization=admin.detail.organization,
                name="Test Setting"
            ).values_list(
                'calculate_overtime_in_slots',
                'slot_duration_in_minutes',
                'slot_behavior_for_remainder',
            ).first(),
            (True, 30, 'up')
        )

    # @API Test
    def test_can_create_overtime_setting_with_out_overtime_slots(self):
        admin = UserFactory()
        self.client.force_login(admin)
        with patch.object(
            get_user_model(),
            'get_hrs_permissions',
            return_value={ATTENDANCE_OVERTIME_PERMISSION['code']}
        ):
            post_response = self.client.post(
                self.overtime_setting_url(organization=admin.detail.organization),
                data=OVERTIME_SETTING_PAYLOAD,
                content_type='application/json'
            )
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            OvertimeSetting.objects.filter(
                organization=admin.detail.organization,
                name="Test Setting"
            ).values_list(
                'calculate_overtime_in_slots',
                'slot_duration_in_minutes',
                'slot_behavior_for_remainder',
            ).first(),
            (None, None, '')
        )

    def test_slot_trim_overtime(self):
        """
        Solo Test for irhrs.attendance.utils.overtime_utils.slot_trim_overtime
        """
        input_output_map = [
            (True, 10, 'up', 32, 40),
            (True, 10, 'up', 39, 40),
            (True, 10, 'down', 39, 30),
            (True, 10, 'const', 35, 35),
            (True, 10, 'const', 5, 0),

            (True, 7, 'up', 33, 35),
            (True, 7, 'down', 33, 28),
            (True, 7, 'const', 6, 0),
            (True, 7, 'const', 48, 48),

            (True, 60, 'down', 55, 0),
            (True, 60, 'up', 65, 120),
            (True, 60, 'const', 35, 0),
            (True, 60, 'const', 65, 65),

            (False, None, '', 112, 112),
            (False, None, '', 0, 0),
        ]
        for calc, dur, bev, inp, res in input_output_map:
            rsp = slot_trim_overtime(
                    timedelta(minutes=inp),
                    type(
                        'OvertimeSetting',
                        (object,),
                        {
                            'calculate_overtime_in_slots': calc,
                            'slot_duration_in_minutes': dur,
                            'slot_behavior_for_remainder': bev
                        }
                    )
                )
            self.assertEqual(
                timedelta(minutes=res),
                rsp
            )

    @staticmethod
    def overtime_setting_url(organization):
        return reverse(
            'api_v1:attendance:overtime-settings-list',
            kwargs={
                'organization_slug': organization.slug
            }
        )
