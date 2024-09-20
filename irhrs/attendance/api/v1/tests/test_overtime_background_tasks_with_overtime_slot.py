from datetime import time, timedelta
from irhrs.common.api.tests.common import BaseTestCase as TestCase
from unittest.mock import patch

from django.db import transaction
from django.db.models.signals import post_save

from irhrs.attendance.api.v1.tests.factory import OvertimeSettingFactory, WorkShiftFactory2 as WorkShiftFactory
from irhrs.attendance.constants import DEVICE, DAILY, FIRST_HALF as ATTENDANCE_FIRST_HALF, \
    FULL_LEAVE, NO_OVERTIME
from irhrs.leave.constants.model_constants import FIRST_HALF as LEAVE_FIRST_HALF, APPROVED, FULL_DAY
from irhrs.attendance.models import TimeSheet, IndividualUserShift, AttendanceAdjustment, WorkDay, \
    IndividualAttendanceSetting, OvertimeEntry
from irhrs.attendance.signals import recalibrate_over_background
from irhrs.attendance.tasks.overtime import generate_overtime
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import get_yesterday, combine_aware, humanize_interval
from irhrs.leave.api.v1.serializers.leave_request import LeaveRequestSerializer
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveAccountFactory, LeaveTypeFactory, \
    LeaveRuleFactory, CompensatoryLeaveRuleFactory
from irhrs.leave.models import LeaveRequestHistory, LeaveAccountHistory
from irhrs.leave.signals import create_leave_request_notification, manage_compensatory_account, \
    create_leave_balance_update_notification
from irhrs.organization.models import Organization
from irhrs.organization.signals import create_organization_settings
from irhrs.users.api.v1.tests.factory import UserMinimalFactory as UserFactory
from irhrs.users.models import UserSupervisor


@patch(
    'irhrs.notification.utils.add_notification',
    new=lambda *y, **ky: None
)
class TestOvertimeGenerationWithSlotTask(TestCase):
    """
    This test will test the generated overtime under the given scenarios:
    * overtime generation for normal scenarios
    * overtime generation for adjustment for missing scenarios
    * overtime recalibration for adjustment scenarios
    * overtime recalibration for pre generated scenario
    * overtime for half leaves applied before
    * overtime for half leaves applied after
    * overtime for full leaves applied before
    * overtime for full leaves applied after
    * overtime for multiple adjustments
    * overtime for off days under leave limit
    * overtime for off days above leave limit
    """
    def setUp(self) -> None:
        days_per_week = getattr(self, 'days_per_week', 7)
        post_save.disconnect(sender=Organization, receiver=create_organization_settings)
        post_save.disconnect(sender=LeaveRequestHistory, receiver=create_leave_request_notification)
        post_save.disconnect(sender=LeaveAccountHistory,
                             receiver=create_leave_balance_update_notification)
        post_save.disconnect(sender=LeaveRequestHistory, receiver=manage_compensatory_account)
        self.user = UserFactory()

        UserSupervisor.objects.create(
            user=self.user,
            supervisor=UserFactory(),
            authority_order=1,
            approve=True,
            deny=True
        )

        self.dummy_request_get = type(
            'Request',
            (object,),
            {
                'method': 'GET',
                'user': self.user,
            }
        )
        self.dummy_request_post = type(
            'Request',
            (object,),
            {
                'method': 'POST',
                'user': self.user,
            }
        )
        setting, _ = IndividualAttendanceSetting.objects.update_or_create(
            user=self.user,
            defaults=dict(
                overtime_setting=self.ot_setting(),
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
        CompensatoryLeaveRuleFactory(
            rule=leave_rule
        )
        self.leave_account = LeaveAccountFactory(
            rule=leave_rule,
            user=self.user
        )
        super().setUp()

    def ot_setting(self, behave='up', minutes=30):
        return OvertimeSettingFactory(
            calculate_overtime_in_slots=True,
            slot_duration_in_minutes=minutes,
            slot_behavior_for_remainder=behave
        )

    def _create_timesheets(self):
        TimeSheet.objects.all().delete()
        time_sheets, *_ = TimeSheet.objects._create_or_update_timesheet_for_profile(
            self.user,
            get_yesterday()
        )
        leave_start = min([x.timesheet_for for x in time_sheets]) if time_sheets else None
        leave_end = max([x.timesheet_for for x in time_sheets]) if time_sheets else None

        return time_sheets

    @staticmethod
    def _clean_db():
        return None
        # Schedule.objects.all().delete()
        # for model in filter(lambda m: m.__module__.startswith('irhrs'), apps.get_models()):
        #     model.objects.all().delete()

    @staticmethod
    def _clock_timesheet(timesheet, timestamp):
        TimeSheet.objects.clock(
            user=timesheet.timesheet_user,
            date_time=timestamp,
            entry_method=DEVICE,
            timesheet=timesheet
        )

    def test_a_overtime_generation_for_normal_scenarios(self):
        entries = [

            # Timely In, Timely Out
            (
                time(9, 0),
                time(18, 0),
                False,
                None,
                None,
                'up'
            ),

            # Early In, Timely Out
            (
                time(7, 0),
                time(18, 0),
                True,
                timedelta(minutes=120),
                timedelta(seconds=0),
                'up'
            ),

            # Early In, Timely Out
            (
                time(7, 25),
                time(18, 0),
                True,
                timedelta(minutes=120),
                timedelta(seconds=0),
                'up'
            ),


            # Early In, Early Out
            (
                time(7, 0),
                time(16, 0),
                True,
                timedelta(minutes=120),
                timedelta(seconds=0),
                'up'
            ),

            # Early In, Late Out
            (
                time(7, 0),
                time(20, 0),
                True,
                timedelta(minutes=120),
                timedelta(minutes=120),
                'up'
            ),

        ]
        for ti, to, ot_created, early_ot, out_ot, behave in entries:
            time_sheets = self._create_timesheets()
            for timesheet in time_sheets:
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
                generate_overtime(
                    timesheet.timesheet_for,
                    timesheet.timesheet_for,
                    DAILY
                )
                self.assertEqual(
                    early_ot,
                    OvertimeEntry.objects.filter(
                        timesheet=timesheet
                    ).values_list(
                        'overtime_detail__punch_in_overtime', flat=True
                    ).first()
                )

                self.assertEqual(
                    out_ot,
                    OvertimeEntry.objects.filter(
                        timesheet=timesheet
                    ).values_list(
                        'overtime_detail__punch_out_overtime', flat=True
                    ).first()
                )

                self.assertEqual(
                    ot_created,
                    OvertimeEntry.objects.filter(
                        timesheet=timesheet
                    ).exists()
                )

    def test_b_overtime_generation_for_adjustment_for_missing_scenarios(self):
        entries = [
            {
                'punch_in': None,
                'punch_out': time(18, 32),
                'ot_creates': False,
                'expected_punch_in_overtime': timedelta(minutes=120),
                'expected_punch_out_overtime': timedelta(minutes=60),
                'punch_in_adjustment': time(7, 10),
                'punch_out_adjustment': None,
                'overtime_slot': 30,
                'slot_behave': 'up',
            },
            {
                'punch_in': time(9, 10),
                'punch_out': None,
                'ot_creates': False,
                'expected_punch_in_overtime': timedelta(0),
                'expected_punch_out_overtime': timedelta(minutes=90),
                'punch_in_adjustment': None,
                'punch_out_adjustment': time(19, 14),
                'overtime_slot': 30,
                'slot_behave': 'up',
            },
            {
                'punch_in': time(9, 30),
                'punch_out': None,
                'ot_creates': False,
                'expected_punch_in_overtime': timedelta(0),
                'expected_punch_out_overtime': timedelta(minutes=120),
                'punch_in_adjustment': None,
                'punch_out_adjustment': time(19, 54),
                'overtime_slot': 30,
                'slot_behave': 'up',
            },
            {
                'punch_in': time(9, 0),
                'punch_out': None,
                'ot_creates': False,
                'expected_punch_in_overtime': timedelta(0),
                'expected_punch_out_overtime': timedelta(minutes=90),
                'punch_in_adjustment': None,
                'punch_out_adjustment': time(19, 54),
                'overtime_slot': 30,
                'slot_behave': 'down',
            },
            {
                'punch_in': time(9, 0),
                'punch_out': None,
                'ot_creates': False,
                'expected_punch_in_overtime': timedelta(0),
                'expected_punch_out_overtime': timedelta(minutes=90),
                'punch_in_adjustment': None,
                'punch_out_adjustment': time(19, 54),
                'overtime_slot': 30,
                'slot_behave': 'down',
            },
            {
                'punch_in': time(9, 0),
                'punch_out': time(19, 54),
                'ot_creates': False,
                'expected_punch_in_overtime': timedelta(0),
                'expected_punch_out_overtime': timedelta(minutes=90),
                'punch_in_adjustment': None,
                'punch_out_adjustment': None,
                'overtime_slot': 30,
                'slot_behave': 'down',
            },
            {
                'punch_in': time(8, 27),
                'punch_out': time(21, 17),
                'ot_creates': False,
                'expected_punch_in_overtime': timedelta(minutes=30),
                'expected_punch_out_overtime': timedelta(hours=3, minutes=15),
                'punch_in_adjustment': None,
                'punch_out_adjustment': None,
                'overtime_slot': 15,
                'slot_behave': 'down',
            },
            {
                'punch_in': time(8, 10),
                'punch_out': time(17, 17),
                'ot_creates': False,
                'expected_punch_in_overtime': timedelta(minutes=45),
                'expected_punch_out_overtime': timedelta(minutes=0),
                'punch_in_adjustment': None,
                'punch_out_adjustment': None,
                'overtime_slot': 15,
                'slot_behave': 'down',
            },
            {
                'punch_in': time(10, 10),
                'punch_out': time(17, 17),
                'ot_creates': False,
                'expected_punch_in_overtime': None,
                'expected_punch_out_overtime': None,
                'punch_in_adjustment': None,
                'punch_out_adjustment': None,
                'overtime_slot': 15,
                'slot_behave': 'down',
            },
        ]
        for entry in entries:
            user = UserFactory()
            setting, _ = IndividualAttendanceSetting.objects.update_or_create(
                user=user,
                defaults=dict(
                    overtime_setting=self.ot_setting(
                        behave=entry['slot_behave'],
                        minutes=entry['overtime_slot']
                    ),
                    enable_overtime=True
                )
            )

            ius = IndividualUserShift.objects.create(
                individual_setting=setting,
                shift=WorkShiftFactory(work_days=7),
                applicable_from=get_yesterday()
            )
            WorkDay.objects.filter(shift=ius.shift).update(applicable_from=ius.applicable_from)
            timesheets, *_ = TimeSheet.objects._create_or_update_timesheet_for_profile(
                user,
                get_yesterday()
            )
            for timesheet in timesheets:
                ti, to, ot_created, early_ot, out_ot, pi_adj, po_adj = map(
                    lambda key: entry[key],
                    [
                        'punch_in', 'punch_out', 'ot_creates', 'expected_punch_in_overtime',
                        'expected_punch_out_overtime', 'punch_in_adjustment',
                        'punch_out_adjustment',
                    ]
                )
                for x in (ti, to):
                    if x:
                        self._clock_timesheet(
                            timesheet,
                            combine_aware(timesheet.timesheet_for, x)
                        )
                for t_stamp in (pi_adj, po_adj):
                    if not t_stamp:
                        continue
                    adjustment = AttendanceAdjustment.objects.create(
                        timesheet=timesheet,
                        timestamp=combine_aware(
                            timesheet.timesheet_for, t_stamp
                        ),
                        description='None',
                        sender=UserFactory(),
                        receiver=UserFactory()
                    )
                    adjustment.approve(
                        approved_by=UserFactory(),
                        remark='Test'
                    )
                generate_overtime(
                    timesheet.timesheet_for,
                    timesheet.timesheet_for,
                    DAILY
                )
                early_ot_db, late_ot_db = OvertimeEntry.objects.filter(
                    timesheet=timesheet
                ).values_list(
                    'overtime_detail__punch_in_overtime',
                    'overtime_detail__punch_out_overtime',
                ).first() or (None, None)
                self.assertEqual(
                    early_ot,
                    early_ot_db,
                    f"{early_ot} vs {early_ot_db} Early Overtime Mismatch"
                )
                self.assertEqual(
                    out_ot,
                    late_ot_db,
                    "Late Overtime Mismatch"
                )

    def tearDown(self) -> None:
        super().tearDown()
        post_save.connect(sender=Organization, receiver=create_organization_settings)
        post_save.connect(sender=LeaveRequestHistory,
                          receiver=create_leave_request_notification)
        post_save.connect(sender=LeaveAccountHistory,
                          receiver=create_leave_balance_update_notification)
        post_save.connect(sender=LeaveRequestHistory, receiver=manage_compensatory_account)
