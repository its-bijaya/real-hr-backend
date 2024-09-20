import datetime
from datetime import timedelta

from django.conf import settings
from pytz import timezone

from irhrs.attendance.api.v1.tests.factory import TimeSheetFactory, OvertimeSettingFactory, \
    WorkShiftFactory, PreApprovalOvertimeFactory
from irhrs.attendance.constants import WORKDAY
from irhrs.attendance.models import IndividualAttendanceSetting, IndividualUserShift, WorkDay
from irhrs.attendance.tasks.pre_approval import get_hours_for_pre_approved_overtime
from irhrs.common.api.tests.common import BaseTestCase
from irhrs.core.utils.common import get_yesterday
from irhrs.users.api.v1.tests.factory import UserFactory


class TestActualOvertimeGrantedForPreApprovedOvertime(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        setting, _ = IndividualAttendanceSetting.objects.update_or_create(
            user=self.user,
            defaults=dict(
                overtime_setting=OvertimeSettingFactory(),
                enable_overtime=True
            )
        )

        ius = IndividualUserShift.objects.create(
            individual_setting=setting,
            shift=WorkShiftFactory(work_days=7),
            applicable_from=get_yesterday()
        )
        WorkDay.objects.filter(shift=ius.shift).update(applicable_from=ius.applicable_from)

    def test(self):
        tz_info = timezone(settings.TIME_ZONE)
        punch_in = datetime.datetime(
            2017, 1, 1, 9, 0, tzinfo=tz_info
        )
        punch_out = datetime.datetime(
            2017, 1, 1, 19, 0, tzinfo=tz_info
        )
        test_cases = (
            # in_delta, out_delta, requested, expected, reduce, increase
            (0, 120, 120, 120, False, False, "# req: 2, worked: 2, got: 2 (=)"),
            (0, 120, 120, 120, True, True, "# req: 2, worked: 2, got: 2 (=)"),
            (60, 120, 120, 120, True, False, "# req: 2, worked: 3, got: 2 (no increase)"),
            (60, 0, 120, 60, True, False, "# req: 2, worked: 1, got: 1 (no increase)"),
            (60, 0, 120, 120, False, False, "# req: 2, worked: 1, got: 2 (no reduce)"),
            (120, 120, 120, 240, True, True, "# req: 2, worked: 4, got: 4 (increase)"),
        )
        for in_delta, out_delta, requested, expected, reduce, increase, msg in test_cases:
            with self.atomicSubTest():
                time_sheet = TimeSheetFactory(
                    coefficient=WORKDAY,
                    timesheet_user=self.user,
                    expected_punch_in=punch_in,
                    punch_in=punch_in - timedelta(minutes=in_delta),
                    expected_punch_out=punch_out,
                    punch_out=punch_out + timedelta(minutes=out_delta),
                )
                pre_approval_setting = OvertimeSettingFactory(
                    reduce_ot_if_actual_ot_lt_approved_ot=reduce,
                    actual_ot_if_actual_gt_approved_ot=increase,
                )
                pre_approval = PreApprovalOvertimeFactory(
                    sender=self.user,
                    overtime_duration=timedelta(minutes=requested)
                )
                will_be_granted = get_hours_for_pre_approved_overtime(
                    pre_approval=pre_approval,
                    pre_approval_setting=pre_approval_setting,
                    time_sheet=time_sheet
                )
                self.assertEqual(will_be_granted, timedelta(minutes=expected), msg)
