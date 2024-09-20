import datetime

from django.utils import timezone

from irhrs.attendance.constants import DAYS, WORKDAY, OFFDAY, HOLIDAY, NO_LEAVE, FULL_LEAVE, \
    FIRST_HALF
from irhrs.attendance.models import TimeSheet
from irhrs.common.api.tests.common import BaseTestCase
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, LeaveAccountFactory, AccumulationRuleFactory, LeaveRequestFactory
from irhrs.leave.constants.model_constants import ASSIGNED, APPROVED
from irhrs.leave.models import LeaveAccountHistory, LeaveSheet
from irhrs.leave.tasks import get_next_accrue_date_for_duration_days
from irhrs.users.api.v1.tests.factory import UserFactory


class GetNextAccrueDateTestCase(BaseTestCase):

    config = [
        {
            'case': 'all_settings_turned_off',
            'accrual_rule': {},
            'timesheet_config': dict(
                absent_days_count=1,
                off_days_count=2,
                holidays_count=2,
                present_in_off_days_count=1,
                present_in_holiday_count=1,
                paid_full_leave_count=1,
                paid_half_leave_count=1,
                unpaid_full_leave_count=1,
                unpaid_half_leave_count=1
            ),
            'deduct_days': 0
        },
        {
            'case': 'all_settings_turned_on',
            'accrual_rule': dict(
                exclude_absent_days=True,
                exclude_off_days=True,
                count_if_present_in_off_day=True,
                exclude_holidays=True,
                count_if_present_in_holiday=True,
                exclude_unpaid_leave=True,
                exclude_paid_leave=True,
                exclude_half_leave=True
            ),
            'timesheet_config': dict(
                absent_days_count=1,
                off_days_count=2,
                holidays_count=2,
                present_in_off_days_count=1,
                present_in_holiday_count=1,
                paid_full_leave_count=1,
                paid_half_leave_count=1,
                unpaid_full_leave_count=1,
                unpaid_half_leave_count=1
            ),
            'deduct_days': 6
        },
        {
            'case': 'all_settings_half_off',
            'accrual_rule': dict(
                exclude_absent_days=True,
                exclude_off_days=True,
                count_if_present_in_off_day=True,
                exclude_holidays=True,
                count_if_present_in_holiday=True,
                exclude_unpaid_leave=True,
                exclude_paid_leave=True,
                exclude_half_leave=False
            ),
            'timesheet_config': dict(
                absent_days_count=1,
                off_days_count=2,
                holidays_count=2,
                present_in_off_days_count=1,
                present_in_holiday_count=1,
                paid_full_leave_count=1,
                paid_half_leave_count=1,
                unpaid_full_leave_count=1,
                unpaid_half_leave_count=1
            ),
            'deduct_days': 5
        }
    ]

    def setUp(self) -> None:
        self.assigned_time = timezone.datetime(2017, 1, 1, 0, 0, 0)
        self.master_setting = MasterSettingFactory(
            accumulation=True,
            effective_from=self.assigned_time.date()
        )
        self.organization = self.master_setting.organization
        self.user = UserFactory(_organization=self.organization)

        self.leave_type = LeaveTypeFactory(master_setting=self.master_setting)
        self.leave_rule = LeaveRuleFactory(leave_type=self.leave_type)
        self.leave_account = LeaveAccountFactory(
            user=self.user,
            rule=self.leave_rule
        )
        LeaveAccountHistory.objects.create(
            account=self.leave_account,
            user=self.user,
            actor=self.user,
            action=ASSIGNED,
            previous_balance=0,
            previous_usable_balance=0,
            new_balance=0,
            new_usable_balance=0,
            created_at=self.assigned_time
        )

        unpaid_leave_type = LeaveTypeFactory(master_setting=self.master_setting, name="Unpaid")
        unpaid_leave_rule = LeaveRuleFactory(leave_type=unpaid_leave_type, is_paid=False)
        self.unpaid_leave_account = LeaveAccountFactory(user=self.user, rule=unpaid_leave_rule)

        paid_leave_type = LeaveTypeFactory(master_setting=self.master_setting, name="Paid")
        paid_leave_rule = LeaveRuleFactory(leave_type=paid_leave_type, is_paid=True)
        self.paid_leave_account = LeaveAccountFactory(user=self.user, rule=paid_leave_rule)

    def setup_timesheet_data(
        self,
        absent_days_count=0,
        off_days_count=0,
        holidays_count=0,
        present_in_off_days_count=0,
        present_in_holiday_count=0,
        paid_full_leave_count=0,
        paid_half_leave_count=0,
        unpaid_full_leave_count=0,
        unpaid_half_leave_count=0
    ):
        absent_created = 0
        off_days_created = 0
        holidays_created = 0
        present_in_off_days_created = 0
        present_in_holiday_created = 0
        paid_full_leave_created = 0
        paid_half_leave_created = 0
        unpaid_full_leave_created = 0
        unpaid_half_leave_created = 0

        paid_leave_request = LeaveRequestFactory(
            user=self.user,
            leave_rule=self.paid_leave_account.rule,
            leave_account=self.paid_leave_account,
            status=APPROVED
        )
        unpaid_leave_request = LeaveRequestFactory(
            user=self.user,
            leave_rule=self.paid_leave_account.rule,
            leave_account=self.unpaid_leave_account,
            status=APPROVED
        )

        for day in range(1, 32):
            leave_coefficient = NO_LEAVE
            is_present = True
            coefficient = WORKDAY

            timesheet_for = datetime.date(2017, 1, day)

            if absent_created < absent_days_count:
                is_present = False
                coefficient = WORKDAY
                absent_created += 1

            elif off_days_created < off_days_count:
                coefficient = OFFDAY
                off_days_created += 1

                if present_in_off_days_created < present_in_off_days_count:
                    is_present = True
                    present_in_off_days_created += 1
                else:
                    is_present = False

            elif holidays_created < holidays_count:
                coefficient = HOLIDAY
                holidays_created += 1

                if present_in_holiday_created < present_in_holiday_count:
                    is_present = True
                    present_in_holiday_created += 1
                else:
                    is_present = False

            elif paid_full_leave_created < paid_full_leave_count:
                LeaveSheet.objects.create(
                    request=paid_leave_request,
                    leave_for=timesheet_for,
                    balance=1,
                    start=paid_leave_request.start,
                    end=paid_leave_request.end
                )
                leave_coefficient = FULL_LEAVE
                is_present = False
                paid_full_leave_created += 1
            elif paid_half_leave_created < paid_half_leave_count:

                LeaveSheet.objects.create(
                    request=paid_leave_request,
                    leave_for=timesheet_for,
                    balance=0.5,
                    start=paid_leave_request.start,
                    end=paid_leave_request.end
                )
                leave_coefficient = FIRST_HALF
                is_present = True
                paid_half_leave_created += 1

            elif unpaid_full_leave_created < unpaid_full_leave_count:
                LeaveSheet.objects.create(
                    request=unpaid_leave_request,
                    leave_for=timesheet_for,
                    balance=1,
                    start=unpaid_leave_request.start,
                    end=unpaid_leave_request.end
                )
                leave_coefficient = FULL_LEAVE
                is_present = False
                unpaid_full_leave_created += 1
            elif unpaid_half_leave_created < unpaid_half_leave_count:

                LeaveSheet.objects.create(
                    request=unpaid_leave_request,
                    leave_for=timesheet_for,
                    balance=0.5,
                    start=unpaid_leave_request.start,
                    end=unpaid_leave_request.end
                )
                leave_coefficient = FIRST_HALF
                is_present = True
                unpaid_half_leave_created += 1

            TimeSheet.objects.create(
                timesheet_user=self.user,
                timesheet_for=timesheet_for,
                coefficient=coefficient,
                is_present=is_present,
                leave_coefficient=leave_coefficient
            )

    def set_accrual_rule(self, balance_added=1, duration=30, duration_type=DAYS, **kwargs):
        return AccumulationRuleFactory(
            rule=self.leave_rule,
            balance_added=balance_added,
            duration=duration,
            duration_type=duration_type,
            **kwargs
        )

    def test_as_expected(self):
        for config in self.config:
            with self.atomicSubTest():
                self.set_accrual_rule(**config['accrual_rule'])
                self.setup_timesheet_data(**config['timesheet_config'])
                last_accrued = self.assigned_time.date()
                expected_next_accrue = last_accrued + timezone.timedelta(
                    days=30 + config['deduct_days'])
                next_accrue = get_next_accrue_date_for_duration_days(
                    self.leave_account, last_accrued)
                self.assertEqual(next_accrue, expected_next_accrue, config['case'])


