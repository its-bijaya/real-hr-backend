from datetime import timedelta, date as dateclass

from dateutil.rrule import rrule, DAILY
from django.utils import timezone

from irhrs.attendance.api.v1.tests.factory import WorkShiftFactory2
from irhrs.attendance.api.v1.tests.utils import punch_for_credit_hour
from irhrs.attendance.constants import P_MONTH as MONTH, FREQUENCY, P_DAYS as DAYS, DURATION
from irhrs.attendance.models import IndividualAttendanceSetting, IndividualUserShift, \
    BreakOutPenaltySetting, PenaltyRule, WorkDay
from irhrs.attendance.utils.breakout_penalty_report import BreakoutReport, make_key
from irhrs.common.api.tests.common import BaseTestCase
from irhrs.organization.api.v1.tests.factory import OrganizationFactory, FiscalYearFactory
from irhrs.users.api.v1.tests.factory import UserFactory


class TestTimeSheetPenalty(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.org = OrganizationFactory()
        self.user = UserFactory(_organization=self.org)
        self.fiscal_year = FiscalYearFactory(
            end_at=dateclass(2017, 12, 31)
        )
        self.fiscal_months = self.fiscal_year.fiscal_months.order_by('month_index')

    @staticmethod
    def assign_setting(user, **settings_data):
        setting, _ = IndividualAttendanceSetting.objects.update_or_create(
            user=user,
            defaults=settings_data
        )
        shift = WorkShiftFactory2(work_days=7, organization=user.detail.organization)
        applicable_from = dateclass(2017, 1, 1)
        IndividualUserShift.objects.create(
            individual_setting=setting,
            shift=shift,
            applicable_from=applicable_from
        )
        WorkDay.objects.filter(shift=shift).update(applicable_from=applicable_from)

    def test_group_dates_fiscal_month(self):
        s = BreakOutPenaltySetting.objects.create(
            organization=self.org,
            title='AxA',
        )
        r = PenaltyRule.objects.create(
            penalty_setting=s,
            penalty_duration_in_days=1,
            penalty_counter_value=1,
            penalty_counter_unit=MONTH,
            calculation_type=FREQUENCY,
            tolerated_duration_in_minutes=0,
            tolerated_occurrences=0,
            consider_late_in=True,
            consider_early_out=False,
            consider_in_between_breaks=False,
            penalty_accumulates=True
        )
        self.assign_setting(self.user, penalty_setting=s)

        from irhrs.attendance.utils.breakout_penalty_report import BreakoutReport
        for fy in self.fiscal_months.all():
            report = BreakoutReport(self.user, fy)
            self.assertEqual(
                report.group_dates(r),
                [(fy.start_at, fy.end_at)],
            )

    def test_group_dates_15_days(self):
        s = BreakOutPenaltySetting.objects.create(
            organization=self.org,
            title='AxB',
        )
        r = PenaltyRule.objects.create(
            penalty_setting=s,
            penalty_duration_in_days=1,
            penalty_counter_value=16,
            penalty_counter_unit=DAYS,
            calculation_type=FREQUENCY,
            tolerated_duration_in_minutes=0,
            tolerated_occurrences=0,
            consider_late_in=True,
            consider_early_out=False,
            consider_in_between_breaks=False,
            penalty_accumulates=True
        )
        self.assign_setting(self.user, penalty_setting=s)

        for fy in self.fiscal_months.all():
            report = BreakoutReport(self.user, fy)
            self.assertEqual(
                report.group_dates(r),
                [
                    (fy.start_at, fy.start_at + timedelta(15)),
                    (fy.start_at + timedelta(16), fy.end_at),
                ]
            )

    def test_frequency_penalty(self):
        s = BreakOutPenaltySetting.objects.create(
            organization=self.org,
            title='AxC',
        )
        r = PenaltyRule.objects.create(
            penalty_setting=s,
            penalty_duration_in_days=1,
            penalty_counter_value=1,
            penalty_counter_unit=MONTH,
            calculation_type=FREQUENCY,
            tolerated_duration_in_minutes=10,
            tolerated_occurrences=5,
            consider_late_in=True,
            consider_early_out=False,
            consider_in_between_breaks=False,
            penalty_accumulates=True
        )
        self.assign_setting(self.user, penalty_setting=s)

        fy = self.fiscal_months.last()
        for day in rrule(
            DAILY,
            dtstart=fy.start_at,
            until=fy.end_at
        ):
            punch_for_credit_hour(self.user, day.date(), early=11, late=0)
        report = BreakoutReport(self.user, fy)
        key = make_key(fy.start_at, fy.end_at, r.id)
        self.assertEqual(
            report.compute_lost_penalty().get(key).get('penalty_days'),
            1
        )

    def test_frequency_penalty_day_wise(self):
        s = BreakOutPenaltySetting.objects.create(
            organization=self.org,
            title='AxC',
        )
        r = PenaltyRule.objects.create(
            penalty_setting=s,
            penalty_duration_in_days=1,
            penalty_counter_value=10,
            penalty_counter_unit=DAYS,
            calculation_type=FREQUENCY,
            tolerated_duration_in_minutes=10,
            tolerated_occurrences=5,
            consider_late_in=True,
            consider_early_out=False,
            consider_in_between_breaks=False,
            penalty_accumulates=True
        )
        self.assign_setting(self.user, penalty_setting=s)

        fy = self.fiscal_months.last()
        for ind, day in enumerate(rrule(
            DAILY,
            dtstart=fy.start_at,
            until=fy.end_at
        )):
            if ind < 10:
                punch_for_credit_hour(self.user, day.date(), early=11, late=0)
            elif ind < 20:
                punch_for_credit_hour(self.user, day.date(), early=0, late=0)
            else:
                punch_for_credit_hour(self.user, day.date(), early=11, late=0)
        report = BreakoutReport(self.user, fy)
        key = make_key(fy.start_at, fy.start_at + timedelta(9), r.id)
        val = report.compute_lost_penalty().get(key)
        self.assertEqual(val['penalty_days'], 1)

        # Since the month is of 31 days and `penalty_counter_value` is set to 10, we need
        # to deduct 1 day to get desired_value
        key = make_key(
            fy.start_at + timedelta(20),
            min(fy.end_at, fy.start_at + timezone.timedelta(29)),
            r.id
        )

        val = report.compute_lost_penalty().get(key)
        self.assertEqual(val['penalty_days'], 1)

    def test_frequency_penalty_day_wise_occurrences_multiple_rules(self):
        s = BreakOutPenaltySetting.objects.create(
            organization=self.org,
            title='AxC',
        )
        r = PenaltyRule.objects.create(
            penalty_setting=s,
            penalty_duration_in_days=1,
            penalty_counter_value=10,
            penalty_counter_unit=DAYS,
            calculation_type=FREQUENCY,
            tolerated_duration_in_minutes=10,
            tolerated_occurrences=5,
            consider_late_in=True,
            consider_early_out=False,
            consider_in_between_breaks=False,
            penalty_accumulates=True
        )
        r2 = PenaltyRule.objects.create(
            penalty_setting=s,
            penalty_duration_in_days=1,
            penalty_counter_value=10,
            penalty_counter_unit=DAYS,
            calculation_type=FREQUENCY,
            tolerated_duration_in_minutes=25,
            tolerated_occurrences=0,
            consider_late_in=True,
            consider_early_out=False,
            consider_in_between_breaks=False,
            penalty_accumulates=True
        )
        self.assign_setting(self.user, penalty_setting=s)

        fy = self.fiscal_months.last()
        for ind, day in enumerate(rrule(
            DAILY,
            dtstart=fy.start_at,
            until=fy.end_at
        )):
            if ind < 10:
                punch_for_credit_hour(self.user, day.date(), early=11, late=0)
            elif ind < 20:
                punch_for_credit_hour(self.user, day.date(), early=30, late=0)
            else:
                punch_for_credit_hour(self.user, day.date(), early=50, late=0)
        report = BreakoutReport(self.user, fy)
        key = make_key(fy.start_at, fy.start_at + timedelta(9), r.id)
        val = report.compute_lost_penalty().get(key)
        self.assertEqual(val['penalty_days'], 1)
        # Since the month is of 31 days and `penalty_counter_value` is set to 10, we need
        # to deduct 1 day to get desired_value
        key = make_key(
            fy.start_at + timedelta(20),
            min(fy.end_at, fy.start_at + timezone.timedelta(29)),
            r.id
        )

        val = report.compute_lost_penalty().get(key)
        self.assertEqual(val['penalty_days'], 1)
        key = make_key(
            fy.start_at + timedelta(20),
            min(fy.end_at, fy.start_at + timezone.timedelta(29)),
            r2.id
        )

        val = report.compute_lost_penalty().get(key)
        self.assertEqual(val['penalty_days'], 1)

    def test_duration_penalty_month_wise(self):
        s = BreakOutPenaltySetting.objects.create(
            organization=self.org,
            title='AxE',
        )
        r = PenaltyRule.objects.create(
            penalty_setting=s,
            penalty_duration_in_days=1,
            penalty_counter_value=1,
            penalty_counter_unit=MONTH,
            calculation_type=DURATION,
            tolerated_duration_in_minutes=180,
            tolerated_occurrences=0,
            consider_late_in=True,
            consider_early_out=False,
            consider_in_between_breaks=False,
            penalty_accumulates=True
        )
        self.assign_setting(self.user, penalty_setting=s)

        fy = self.fiscal_months.last()
        for ind, day in enumerate(rrule(
            DAILY,
            dtstart=fy.start_at,
            until=fy.end_at
        )):
            if ind < 5:
                punch_for_credit_hour(self.user, day.date(), early=11, late=0)
            elif ind < 10:
                punch_for_credit_hour(self.user, day.date(), early=50, late=0)
            elif ind < 15:
                punch_for_credit_hour(self.user, day.date(), early=20, late=0)
            elif ind < 25:
                punch_for_credit_hour(self.user, day.date(), early=5, late=0)
            else:
                punch_for_credit_hour(self.user, day.date(), early=30, late=0)
        # approx 10 hours
        report = BreakoutReport(self.user, fy)
        key = make_key(fy.start_at, fy.end_at, r.id)
        val = report.compute_lost_penalty()
        self.assertEqual(val[key]['penalty_days'], 3)

    def test_duration_penalty_day_wise(self):
        s = BreakOutPenaltySetting.objects.create(
            organization=self.org,
            title='AxE',
        )
        r = PenaltyRule.objects.create(
            penalty_setting=s,
            penalty_duration_in_days=1,
            penalty_counter_value=10,
            penalty_counter_unit=DAYS,
            calculation_type=DURATION,
            tolerated_duration_in_minutes=180,
            tolerated_occurrences=5,
            consider_late_in=True,
            consider_early_out=False,
            consider_in_between_breaks=False,
            penalty_accumulates=True
        )
        self.assign_setting(self.user, penalty_setting=s)

        fy = self.fiscal_months.last()
        for ind, day in enumerate(rrule(
            DAILY,
            dtstart=fy.start_at,
            until=fy.end_at
        )):
            if ind < 10:
                punch_for_credit_hour(self.user, day.date(), early=20, late=0)
            elif ind < 20:
                punch_for_credit_hour(self.user, day.date(), early=40, late=0)
            else:
                punch_for_credit_hour(self.user, day.date(), early=80, late=0)

        expected_val = {
            make_key(
                fy.start_at + timezone.timedelta(0),
                fy.start_at + timezone.timedelta(9),
                r.id
            ): 1,
            make_key(
                fy.start_at + timezone.timedelta(10),
                fy.start_at + timezone.timedelta(19),
                r.id
            ): 2,
            make_key(
                fy.start_at + timezone.timedelta(20),
                # Since the month is of 31 days and `penalty_counter_value` is set to 10, we need
                # to deduct 1 day to get desired_value
                min(fy.end_at, fy.start_at + timezone.timedelta(29)),
                r.id
            ): 4,
        }

        report = BreakoutReport(self.user, fy)
        val = report.compute_lost_penalty()
        for key, penalty in expected_val.items():
            self.assertEqual(
                val[key]['penalty_days'],
                penalty,
                key
            )
