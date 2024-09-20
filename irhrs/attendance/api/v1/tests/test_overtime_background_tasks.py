import json
from datetime import time, timedelta
from irhrs.common.api.tests.common import BaseTestCase as TestCase, RHRSAPITestCase
from unittest.mock import patch

from django.db import transaction
from django.db.models.signals import post_save
from django.utils import timezone
from django_q.models import Schedule

from irhrs.attendance.api.v1.tests.factory import OvertimeSettingFactory, WorkShiftFactory2 as WorkShiftFactory
from irhrs.attendance.constants import DEVICE, DAILY, FIRST_HALF as ATTENDANCE_FIRST_HALF, \
    FULL_LEAVE, NO_OVERTIME
from irhrs.leave.constants.model_constants import FIRST_HALF as LEAVE_FIRST_HALF, APPROVED, FULL_DAY
from irhrs.attendance.models import TimeSheet, IndividualUserShift, AttendanceAdjustment, WorkDay, \
    IndividualAttendanceSetting
from irhrs.attendance.signals import recalibrate_over_background
from irhrs.attendance.tasks.overtime import generate_overtime
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import get_yesterday, combine_aware, humanize_interval, get_today
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
class TestOvertimeGenerationTask(RHRSAPITestCase):
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

    organization_name = 'organization'

    users = [
        ('user@email.com', 'password', 'male')
    ]
    def setUp(self) -> None:
        super().setUp()
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
        CompensatoryLeaveRuleFactory(
            rule=leave_rule
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
                None
            ),

            # Early In, Timely Out
            (
                time(7, 0),
                time(18, 0),
                True,
                timedelta(minutes=120),
                timedelta(seconds=0)
            ),

            # Early In, Early Out
            (
                time(7, 0),
                time(16, 0),
                True,
                timedelta(minutes=120),
                timedelta(seconds=0)
            ),

            # Early In, Late Out
            (
                time(7, 0),
                time(20, 0),
                True,
                timedelta(minutes=120),
                timedelta(minutes=120),
            ),

        ]

        for entry in entries:
            time_sheets = self._create_timesheets()
            for timesheet in time_sheets:
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

                generate_overtime(
                    timesheet.timesheet_for,
                    timesheet.timesheet_for,
                    DAILY
                )

                self.assertEqual(
                    early_ot,
                    nested_getattr(
                        timesheet,
                        'overtime.overtime_detail.punch_in_overtime'
                    )
                )

                self.assertEqual(
                    out_ot,
                    nested_getattr(
                        timesheet,
                        'overtime.overtime_detail.punch_out_overtime'
                    )
                )

                self.assertEqual(
                    ot_created,
                    bool(getattr(timesheet, 'overtime', False))
                )

    def test_b_overtime_generation_for_adjustment_for_missing_scenarios(self):
        entries = [
            # Missing PI
            (
                None,  # PI
                time(18, 0),  # PO
                False,  # OT Creates?
                timedelta(minutes=120),  # Punch In Overtime
                timedelta(0),  # Punch Out Overtime,
                time(7, 0),  # Punch In Adjustment
                None,  # Punch Out Adjustment
            ),
            (
                time(9, 0),
                None,
                False,
                timedelta(0),
                timedelta(minutes=60),
                None,
                time(19, 0)
            ),
        ]
        for entry in entries:
            user = UserFactory()
            setting, _ = IndividualAttendanceSetting.objects.update_or_create(
                user=user,
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
            timesheets, *_ = TimeSheet.objects._create_or_update_timesheet_for_profile(
                user,
                get_yesterday()
            )
            for timesheet in timesheets:
                ti, to, ot_created, early_ot, out_ot, pi_adj, po_adj = entry
                for x in (ti, to):
                    if x:
                        self._clock_timesheet(
                            timesheet,
                            combine_aware(timesheet.timesheet_for, x)
                        )
                generate_overtime(
                    timesheet.timesheet_for,
                    timesheet.timesheet_for,
                    DAILY
                )

                self.assertEqual(
                    ot_created,
                    bool(getattr(timesheet, 'overtime', False))
                )

                if ot_created:
                    self.assertEqual(
                        out_ot,
                        nested_getattr(
                            timesheet,
                            'overtime.overtime_detail.punch_out_overtime'
                        )
                    )
                    self.assertEqual(
                        early_ot,
                        nested_getattr(
                            timesheet,
                            'overtime.overtime_detail.punch_in_overtime'
                        )
                    )
                punch_in = combine_aware(timesheet.timesheet_for, pi_adj) if pi_adj else None
                punch_out = combine_aware(timesheet.timesheet_for, po_adj) if po_adj else None
                for timestamp in (punch_in, punch_out):
                    if not timestamp:
                        continue
                    adjustment = AttendanceAdjustment.objects.create(
                        timesheet=timesheet,
                        timestamp=timestamp,
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

                timesheet.refresh_from_db()

                ot_detail = nested_getattr(
                    timesheet,
                    'overtime.overtime_detail'
                )
                self.assertEqual(
                    early_ot,
                    ot_detail.punch_in_overtime,
                    "Early Overtime Mismatch"
                )
                self.assertEqual(
                    out_ot,
                    ot_detail.punch_out_overtime,
                    "Late Overtime Mismatch"
                )

    def test_c_overtime_recalibration_for_adjustment_scenarios(self):
        entries = [
            (
                time(12, 0),  # PI
                time(16, 0),  # PO
                timedelta(minutes=120),  # Punch In Overtime
                timedelta(minutes=0),  # Punch Out Overtime,
                time(7, 0),  # Punch In Adjustment
                None,  # Punch Out Adjustment
            ),
            (

                time(9, 0),  # PI
                time(15, 0),  # PO
                timedelta(hours=2),  # Punch In Overtime
                timedelta(hours=1),  # Punch Out Overtime,
                time(7, 0),  # Punch In Adjustment
                time(19, 0),  # Punch Out Adjustment
            ),
        ]

        for entry in entries:
            user = UserFactory()
            setting, _ = IndividualAttendanceSetting.objects.update_or_create(
                user=user,
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
            timesheets, *_ = TimeSheet.objects._create_or_update_timesheet_for_profile(
                user,
                get_yesterday()
            )
            for timesheet in timesheets:
                ti, to, early_ot, out_ot, pi_adj, po_adj = entry
                for x in (ti, to):
                    if x:
                        self._clock_timesheet(
                            timesheet,
                            combine_aware(timesheet.timesheet_for, x)
                        )
                generate_overtime(
                    timesheet.timesheet_for,
                    timesheet.timesheet_for,
                    DAILY
                )

                self.assertEqual(
                    None,  # Should not be created
                    nested_getattr(
                        timesheet,
                        'overtime.overtime_detail.punch_in_overtime'
                        "Overtime should not have been generated"
                    )
                )
                self.assertEqual(
                    None,  # Should not be created
                    nested_getattr(
                        timesheet,
                        'overtime.overtime_detail.punch_out_overtime'
                    ),
                    "Overtime should not have been generated"
                )
                punch_in = combine_aware(timesheet.timesheet_for, pi_adj) if pi_adj else None
                punch_out = combine_aware(timesheet.timesheet_for, po_adj) if po_adj else None
                for timestamp in (punch_in, punch_out):
                    if not timestamp:
                        continue
                    adjustment = AttendanceAdjustment.objects.create(
                        timesheet=timesheet,
                        timestamp=timestamp,
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
                timesheet.refresh_from_db()
                ot_detail = nested_getattr(
                    timesheet,
                    'overtime.overtime_detail'
                )
                self.assertEqual(
                    early_ot,
                    ot_detail.punch_in_overtime,
                    "Early Overtime Mismatch"
                )
                self.assertEqual(
                    out_ot,
                    ot_detail.punch_out_overtime,
                    "Late Overtime Mismatch"
                )

    def test_d_overtime_recalibration_for_pre_generated_scenario(self):
        user = UserFactory()
        setting, _ = IndividualAttendanceSetting.objects.update_or_create(
                user=user,
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

        timesheets, *_ = TimeSheet.objects._create_or_update_timesheet_for_profile(
            user,
            get_yesterday()
        )
        for ts in timesheets:
            timestamp = combine_aware(
                ts.timesheet_for,
                time(7, 0)
            )
            self._clock_timesheet(
                ts,
                timestamp
            )
            timestamp = combine_aware(
                ts.timesheet_for,
                time(19, 0)
            )
            self._clock_timesheet(
                ts,
                timestamp
            )
            generate_overtime(
                ts.timesheet_for,
                ts.timesheet_for,
                DAILY
            )
            ts.refresh_from_db()
            ot_detail = nested_getattr(
                ts,
                'overtime.overtime_detail'
            )
            self.assertEqual(
                ot_detail.punch_in_overtime,
                timedelta(hours=2),
                "Two hours Overtime should have been generated."
            )
            adjustment = AttendanceAdjustment.objects.create(
                timesheet=ts,
                timestamp=combine_aware(
                    ts.timesheet_for,
                    time(6, 0)
                ),
                description='None',
                sender=UserFactory(),
                receiver=UserFactory()
            )
            adjustment.approve(
                UserFactory(),
                'Remark'
            )
            ts.refresh_from_db()
            ot_detail = nested_getattr(
                ts,
                'overtime.overtime_detail'
            )
            self.assertEqual(
                ot_detail.punch_in_overtime,
                timedelta(hours=3),
                "Three hours Overtime should have been re-calibrated."
            )

    def test_e_overtime_for_half_leaves_applied_before(self):
        self._clean_db()
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

        # directly modify the timesheet as leave. Care for nothing else.
        for timesheet in time_sheets:
            timesheet.leave_coefficient = ATTENDANCE_FIRST_HALF
            timesheet.expected_punch_in = combine_aware(
                timesheet.timesheet_for,
                timesheet.work_time.start_time
            ) + timedelta(minutes=(timesheet.work_time.working_minutes//2))
            timesheet.save()
            with transaction.atomic():
                self._clock_timesheet(
                    timesheet,
                    combine_aware(
                        timesheet.timesheet_for,
                        time(12, 0)
                    )
                )
                self._clock_timesheet(
                    timesheet,
                    combine_aware(
                        timesheet.timesheet_for,
                        time(18, 0)
                    )
                )
            timesheet.refresh_from_db()
            generate_overtime(
                1, 1, 1,
                fix_ids=[timesheet.id],
                fix_missing=True
            )
            overtime_detail = timesheet.overtime.overtime_detail
            self.assertEqual(
                humanize_interval(overtime_detail.punch_in_overtime),
                humanize_interval(timedelta(hours=1, minutes=30)),
                "Overtime for 1st half leave should have been 1 hours and 30 minutes."
            )
            self.assertEqual(
                humanize_interval(overtime_detail.punch_out_overtime),
                humanize_interval(timedelta(minutes=0)),
                "Overtime for 2nd half leave should have been 0 hours."
            )

    def test_f_overtime_for_half_leaves_applied_after(self):
        time_sheets = self._create_timesheets()
        leave_start = min([x.timesheet_for for x in time_sheets]) if time_sheets else None
        leave_end = max([x.timesheet_for for x in time_sheets]) if time_sheets else None

        if not (leave_end and leave_start):
            print(
                "No time sheets were created. Rethink the scenarios."
            )
            return

        UserSupervisor.objects.create(
            user=self.user,
            supervisor=UserFactory(),
            authority_order=1,
            approve=True,
            deny=True
        )
        # directly modify the timesheet as leave. Care for nothing else.
        for timesheet in time_sheets:
            with transaction.atomic():
                self._clock_timesheet(
                    timesheet,
                    combine_aware(
                        timesheet.timesheet_for,
                        time(12, 0)
                    )
                )
                self._clock_timesheet(
                    timesheet,
                    combine_aware(
                        timesheet.timesheet_for,
                        time(18, 0)
                    )
                )
            timesheet.refresh_from_db()
            generate_overtime(
                1, 1, 1,
                fix_ids=[timesheet.id],
                fix_missing=True
            )
            overtime_detail = nested_getattr(
                timesheet, 'overtime.overtime_detail'
            )
            self.assertIsNone(
                overtime_detail,
                "Overtime Should not have been created"
            )
            next_week = get_today() + timedelta(days=7)
            last_week = get_today() - timedelta(days=7)
            ser = LeaveRequestSerializer(
                context={
                    'request': self.dummy_request_post,
                    'organization': self.organization
                },
                data=dict(
                    recipient=UserFactory(),
                    balance=0.5,
                    start=get_yesterday(),
                    end=get_yesterday(),
                    part_of_day=LEAVE_FIRST_HALF,
                    leave_account=LeaveAccountFactory(
                        user=self.user,
                        rule=LeaveRuleFactory(
                            employee_can_apply=True,
                            can_apply_half_shift=True,
                            leave_type=LeaveTypeFactory(
                                master_setting=MasterSettingFactory(
                                    half_shift_leave=True,
                                    effective_from=last_week,
                                    effective_till=next_week,
                                    organization=self.user.detail.organization
                                )
                            )
                        )
                    ).id,
                    details="testing for leave",
                )
            )
            ser.is_valid(raise_exception=True)
            with transaction.atomic():
                leave = ser.save()
            leave.refresh_from_db()
            # approve the leave here, that should recalibrate the overtime.
            ser.update(
                leave,
                {
                    "supervisor_remarks": "supervisor_remarks",
                    "status": APPROVED
                }
            )
            if recalibrate_over_background(
                timesheet.id,
                UserFactory().id,
                None
            ) == (False, "Overtime Does Not exist!"):
                generate_overtime(
                    1, 1, 1,
                    fix_missing=True,
                    fix_ids=[timesheet.id]
                )
            timesheet.refresh_from_db()
            overtime_detail = nested_getattr(
                timesheet, 'overtime.overtime_detail'
            )
            self.assertEqual(
                humanize_interval(overtime_detail.punch_in_overtime),
                humanize_interval(timedelta(hours=1, minutes=30)),
                "Overtime for 1st half leave should have been 1 hours and 30 minutes."
            )
            self.assertEqual(
                humanize_interval(overtime_detail.punch_out_overtime),
                humanize_interval(timedelta(minutes=0)),
                "Overtime for 2nd half leave should have been 0 hours."
            )

    def test_g_overtime_for_full_leaves_applied_before(self):
        time_sheets = self._create_timesheets()
        # directly modify the timesheet as leave. Care for nothing else.
        next_week = get_today() + timedelta(days=7)
        last_week = get_today() - timedelta(days=7)
        for timesheet in time_sheets:
            ser = LeaveRequestSerializer(
                context={
                    'request': self.dummy_request_post,
                    'organization': self.organization
                },
                data=dict(
                    recipient=UserFactory(),
                    start=get_yesterday(),
                    end=get_yesterday(),
                    part_of_day=FULL_DAY,
                    leave_account=LeaveAccountFactory(
                        user=self.user,
                        rule=LeaveRuleFactory(
                            employee_can_apply=True,
                            leave_type=LeaveTypeFactory(
                                master_setting=MasterSettingFactory(
                                    effective_from=last_week,
                                    effective_till=next_week,
                                    organization=self.user.detail.organization
                                )
                            )
                        )
                    ).id,
                    details="testing for leave",
                )
            )
            ser.is_valid(raise_exception=True)
            with transaction.atomic():
                leave = ser.save()
            leave.refresh_from_db()
            # approve the leave here, that should recalibrate the overtime.
            with transaction.atomic():
                ser.update(
                    leave,
                    {
                        "supervisor_remarks": "supervisor_remarks",
                        "status": APPROVED
                    }
                )
            timesheet.refresh_from_db()
            self.assertEqual(
                timesheet.leave_coefficient,
                FULL_LEAVE,
                "TimeSheet coefficient should have been full leave."
            )
            with transaction.atomic():
                self._clock_timesheet(
                    timesheet,
                    combine_aware(
                        timesheet.timesheet_for,
                        time(12, 0)
                    )
                )
                self._clock_timesheet(
                    timesheet,
                    combine_aware(
                        timesheet.timesheet_for,
                        time(18, 0)
                    )
                )
            timesheet.refresh_from_db()
            generate_overtime(
                1, 1, 1,
                fix_ids=[timesheet.id],
                fix_missing=True
            )
            timesheet.refresh_from_db()
            overtime_detail = nested_getattr(
                timesheet, 'overtime.overtime_detail'
            )
            self.assertEqual(
                humanize_interval(overtime_detail.punch_in_overtime),
                humanize_interval(timedelta(hours=6)),
                "Overtime for full day leave have been 6 hours."
            )
            self.assertEqual(
                humanize_interval(overtime_detail.punch_out_overtime),
                humanize_interval(timedelta(minutes=0)),
                "Overtime for full day leave should have been 0 hours."
            )

    def test_h_overtime_for_full_leaves_applied_after(self):
        time_sheets = self._create_timesheets()
        # directly modify the timesheet as leave. Care for nothing else.
        for timesheet in time_sheets:
            with transaction.atomic():
                self._clock_timesheet(
                    timesheet,
                    combine_aware(
                        timesheet.timesheet_for,
                        time(12, 0)
                    )
                )
                self._clock_timesheet(
                    timesheet,
                    combine_aware(
                        timesheet.timesheet_for,
                        time(18, 0)
                    )
                )
            timesheet.refresh_from_db()
            generate_overtime(
                1, 1, 1,
                fix_ids=[timesheet.id],
                fix_missing=True
            )
            overtime_detail = nested_getattr(
                timesheet, 'overtime.overtime_detail'
            )
            self.assertIsNone(
                overtime_detail,
                "Overtime should not have been generated."
            )
            next_week = get_today() + timedelta(days=7)
            last_week = get_today() - timedelta(days=7)
            ser = LeaveRequestSerializer(
                context={
                    'request': self.dummy_request_post,
                    'organization': self.organization
                },
                data=dict(
                    recipient=UserFactory(),
                    start=get_yesterday(),
                    end=get_yesterday(),
                    part_of_day=FULL_DAY,
                    leave_account=LeaveAccountFactory(
                        user=self.user,
                        rule=LeaveRuleFactory(
                            employee_can_apply=True,
                            leave_type=LeaveTypeFactory(
                                master_setting=MasterSettingFactory(
                                    effective_from=last_week,
                                    effective_till=next_week,
                                    organization=self.user.detail.organization
                                )
                            )
                        )
                    ).id,
                    details="testing for leave",
                )
            )
            ser.is_valid(raise_exception=True)
            with transaction.atomic():
                leave = ser.save()
            leave.refresh_from_db()
            # approve the leave here, that should recalibrate the overtime.
            with transaction.atomic():
                ser.update(
                    leave,
                    {
                        "supervisor_remarks": "supervisor_remarks",
                        "status": APPROVED
                    }
                )
            timesheet.refresh_from_db()
            self.assertEqual(
                timesheet.leave_coefficient,
                FULL_LEAVE,
                "TimeSheet coefficient should have been full leave."
            )
            generate_overtime(
                1, 1, 1,
                fix_ids=[timesheet.id],
                fix_missing=True
            )
            overtime_detail = nested_getattr(
                timesheet, 'overtime.overtime_detail'
            )
            self.assertEqual(
                humanize_interval(overtime_detail.punch_in_overtime),
                humanize_interval(timedelta(hours=6)),
                "Overtime for full day leave have been 6 hours."
            )
            self.assertEqual(
                humanize_interval(overtime_detail.punch_out_overtime),
                humanize_interval(timedelta(minutes=0)),
                "Overtime for full day leave should have been 0 hours."
            )

    def test_i_overtime_for_multiple_adjustments(self):
        time_sheets = self._create_timesheets()
        for ts in time_sheets:
            # The user came in at 11 AM and left at 4 PM.
            # Later, sent an adjustment managing the punch in time.
            # After that, sent an adjustment managing the punch out time.
            with transaction.atomic():
                self._clock_timesheet(
                    timesheet=ts,
                    timestamp=combine_aware(
                        ts.timesheet_for,
                        time(11, 0)
                    )
                )
                self._clock_timesheet(
                    timesheet=ts,
                    timestamp=combine_aware(
                        ts.timesheet_for,
                        time(16, 0)
                    )
                )
            adjustment = AttendanceAdjustment.objects.create(
                timesheet=ts,
                timestamp=combine_aware(
                    ts.timesheet_for,
                    time(8, 0)
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
                1, 1, 1,
                fix_missing=True,
                fix_ids=[ts.id]
            )
            ts.refresh_from_db()
            self.assertEqual(
                ts.overtime.overtime_detail.punch_in_overtime,
                timedelta(hours=1),
                "Overtime should have generated 1 hours after the adjustment "
                "approval."
            )

            adjustment = AttendanceAdjustment.objects.create(
                timesheet=ts,
                timestamp=combine_aware(
                    ts.timesheet_for,
                    time(19, 0)
                ),
                description='None',
                sender=UserFactory(),
                receiver=UserFactory()
            )
            adjustment.approve(
                approved_by=UserFactory(),
                remark='Test'
            )
            ts.refresh_from_db()
            self.assertEqual(
                ts.overtime.overtime_detail.punch_out_overtime,
                timedelta(hours=1),
                "Overtime should have re-calibrated after the overtime was "
                "generated, and adjustment was sent."
            )

    def test_j_overtime_for_off_days_under_leave_limit(self):
        WorkDay.objects.all().delete()
        self.days_per_week = 0
        time_sheets = self._create_timesheets()
        for timesheet in time_sheets:
            self._clock_timesheet(
                timesheet,
                combine_aware(
                    timesheet.timesheet_for,
                    time(12, 0)
                )
            )
            self._clock_timesheet(
                timesheet,
                combine_aware(
                    timesheet.timesheet_for,
                    time(14, 0)
                )
            )
        timesheet.refresh_from_db()
        generate_overtime(
            1,  1, 1,
            fix_missing=True,
            fix_ids=[timesheet.id]
        )
        self.assertEqual(
            timesheet.overtime.overtime_detail.punch_in_overtime,
            timedelta(hours=2),
            "Two hours offday overtime should have been generated."
        )

    def test_k_overtime_for_off_days_above_leave_limit(self):
        WorkDay.objects.all().delete()
        self.days_per_week = 0
        time_sheets = self._create_timesheets()
        for timesheet in time_sheets:
            self._clock_timesheet(
                timesheet,
                combine_aware(
                    timesheet.timesheet_for,
                    time(12, 0)
                )
            )
            self._clock_timesheet(
                timesheet,
                combine_aware(
                    timesheet.timesheet_for,
                    time(22, 0)
                )
            )
            timesheet.refresh_from_db()
            ot_setting = timesheet.timesheet_user.attendance_setting.overtime_setting
            ot_setting.overtime_after_offday = NO_OVERTIME
            ot_setting.save()
            generate_overtime(
                1, 1, 1,
                fix_missing=True,
                fix_ids=[timesheet.id]
            )
            self.assertIsNone(
                getattr(timesheet, 'overtime', None),
                "Off-day overtime should not have been generated."
            )

    def tearDown(self) -> None:
        super().tearDown()
        post_save.connect(sender=Organization, receiver=create_organization_settings)
        post_save.connect(sender=LeaveRequestHistory, receiver=create_leave_request_notification)
        post_save.connect(sender=LeaveAccountHistory,
                          receiver=create_leave_balance_update_notification)
        post_save.connect(sender=LeaveRequestHistory, receiver=manage_compensatory_account)
