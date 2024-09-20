from datetime import time, timedelta

from irhrs.attendance.api.v1.tests.factory import OvertimeSettingFactory, WorkShiftFactory
from irhrs.attendance.constants import DEVICE, DAILY
from irhrs.attendance.models import IndividualAttendanceSetting, IndividualUserShift, WorkDay, \
    TimeSheet, AttendanceAdjustment
from irhrs.attendance.tasks.overtime import generate_overtime, generate_daily_overtime
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_yesterday, combine_aware
from irhrs.notification.models import Notification
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, LeaveAccountFactory
from irhrs.users.api.v1.tests.factory import UserFactory


class TestOvertimeGenerationTask(RHRSAPITestCase):
    users = [
        ('admin@email.com', 'password', 'Male'),
    ]
    organization_name = "Google"

    def setUp(self) -> None:
        super().setUp()
        days_per_week = getattr(self, 'days_per_week', 7)
        self.user = self.created_users[0]

        setting, _ = IndividualAttendanceSetting.objects.update_or_create(
            user=self.user,
            defaults=dict(
                overtime_setting=OvertimeSettingFactory(),
                enable_overtime=True
            )
        )

        ius = IndividualUserShift.objects.create(
            individual_setting=setting,
            shift=WorkShiftFactory(work_days=days_per_week),
            applicable_from=get_yesterday()
        )
        WorkDay.objects.filter(shift=ius.shift).update(applicable_from=ius.applicable_from)
        master_setting = MasterSettingFactory()
        leave_type = LeaveTypeFactory(master_setting=master_setting)
        leave_rule = LeaveRuleFactory(
            leave_type=leave_type
        )
        self.leave_account = LeaveAccountFactory(
            rule=leave_rule,
            user=self.user
        )

    def _create_timesheets(self):
        TimeSheet.objects.all().delete()
        time_sheets, *_ = TimeSheet.objects._create_or_update_timesheet_for_profile(
            self.user,
            get_yesterday()
        )
        leave_start = min([x.timesheet_for for x in time_sheets]) if time_sheets else None
        leave_end = max([x.timesheet_for for x in time_sheets]) if time_sheets else None

        if not (leave_end and leave_start):
            print(
                "No time sheets were created. Rethink the scenarios."
            )
            return

        return time_sheets

    @staticmethod
    def _clock_timesheet(timesheet, timestamp):
        TimeSheet.objects.clock(
            user=timesheet.timesheet_user,
            date_time=timestamp,
            entry_method=DEVICE,
            timesheet=timesheet
        )

    def test_overtime_notification(self):
        entry = (
            time(7, 0),
            time(20, 0),
            True,
            timedelta(minutes=120),
            timedelta(minutes=120),
        )

        timesheet = self._create_timesheets()[0]
        ti, to, ot_created, early_ot, out_ot = entry
        ts1, ts2 = map(
            lambda x: combine_aware(timesheet.timesheet_for, x),
            (ti, to)
        )
        self._clock_timesheet(
            timesheet,
            ts1
        )
        self._clock_timesheet(
            timesheet,
            ts2
        )

        overtime = generate_overtime(
            timesheet.timesheet_for,
            timesheet.timesheet_for,
            DAILY
        )
        self.assertEqual(
            overtime.get('created_count'),
            1
        )
        self.assertTrue(
            Notification.objects.filter(
                text=f"Your overtime for {get_yesterday()} has been generated."
            ).exists()
        )

        adjustment = AttendanceAdjustment.objects.create(
            timesheet=timesheet,
            timestamp=combine_aware(
                timesheet.timesheet_for,
                time(6, 0)
            ),
            description='None',
            sender=self.created_users[0],
            receiver=UserFactory()
        )
        generate_daily_overtime(
            str(combine_aware(timesheet.timesheet_for, time(0, 0)))
        )
        user = UserFactory()

        adjustment.approve(
            approved_by=user,
            remark='Test'
        )
        self.assertTrue(
            Notification.objects.filter(
                text=(
                    f"{user} has approved your adjust attendance entry request "
                    f"for {get_yesterday()}."
                )
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                text=f"Your overtime claim has been re-calibrated for {get_yesterday()} after "
                     f"adjustment approval  by {user}"
            ).exists()
        )

        background_overtime2 = generate_daily_overtime(
            str(combine_aware(timesheet.timesheet_for, time(0, 0)))
        )
        #
        self.assertEqual(
            background_overtime2.get('re-calibrated'),
            []
        )
