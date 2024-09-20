from datetime import timedelta, date
from config import settings
from irhrs.attendance.constants import HOLIDAY, WORKDAY
from irhrs.attendance.utils.get_lost_hours_as_per_shift import get_lost_hours_for_date_range
from irhrs.attendance.utils.payroll import _parse_date, get_work_days_count_from_virtual_timesheets
from irhrs.attendance.utils.timesheet import simulate_timesheets
from irhrs.organization.models import Organization
from irhrs.payroll.models import Heading
from irhrs.payroll.utils.user_voluntary_rebate import get_remaining_fiscal_months_in_payroll
from irhrs.users.models import User


def has_heading_rule(heading: Heading, rule: str) -> bool:
    return heading.rules.rfind(rule) != -1


def get_holiday_count_for_user_with_date_range_according_to_timesheet(employee: User,
                                                                      start_date: date,
                                                                      end_date: date) -> int:
    return employee.timesheets.filter(
        timesheet_for__gte=start_date,
        timesheet_for__lte=end_date,
        coefficient=HOLIDAY
    ).count()


def get_simulated_working_days_count(employee, work_shift, start_date, end_date,
                                     include_holiday_offday=False) -> int:
    if not work_shift:
        return 0
    virtual_timesheet = simulate_timesheets(
        employee,
        work_shift,
        start_date,
        end_date
    )
    return get_work_days_count_from_virtual_timesheets(virtual_timesheet, include_holiday_offday)


def get_working_days_count_for_date_range(
    employee: User, start: date, end: date, include_holiday_offday: bool = False
):
    """
    Return total number of working days for given user for given date range.
    """
    timesheet_qs = employee.timesheets.filter(
        timesheet_for__gte=start,
        timesheet_for__lte=end,
        work_shift__isnull=False
    ).order_by('timesheet_for')

    start_date = _parse_date(start)
    end_date = _parse_date(end)

    if timesheet_qs:
        work_shift = timesheet_qs.first().work_shift
    else:
        first_time_sheet = employee.timesheets.filter(
            timesheet_for__gte=start,
            work_shift__isnull=False
        ).order_by('timesheet_for').first()

        last_time_sheet = employee.timesheets.filter(
            timesheet_for__lte=end,
            work_shift__isnull=False
        ).order_by('-timesheet_for').first()

        work_shift = first_time_sheet.work_shift if first_time_sheet else last_time_sheet.work_shift if last_time_sheet else None

    return get_simulated_working_days_count(
        employee, work_shift, start_date,
        end_date, include_holiday_offday
    )


class YearlyPayslipReportForRemainingMonths:
    def __init__(self, employee: User, organization: Organization, remaining_months,
                 include_holiday_off_day: bool = False):
        self.employee = employee
        self.organization = organization
        self.remaining_months = remaining_months
        self.include_holiday_off_day = include_holiday_off_day

    def get_monthly_lost_hours(self) -> list:
        result = []
        for month in self.remaining_months:
            total_lost_time = get_lost_hours_for_date_range(
                self.employee.id, self.organization, month['start_at'],
                month['end_at'],
                calculate_unpaid_breaks=settings.CALCULATE_UNPAID_BREAKS_IN_INTERNAL_PLUGIN,
                ignore_seconds=settings.IGNORE_SECOND_IN_TOTAL_LOST_HOURS
            )
            total_lost_in_hours = round(total_lost_time / 3600, 2)
            result.append(
                {
                    'from_date': month['start_at'],
                    'to_date': month['end_at'],
                    'amount': total_lost_in_hours,
                    'display_name': month['display_name']
                })
        return result

    def get_monthly_holiday_count(self) -> list:
        return [
            {
                'from_date': month['start_at'],
                'to_date': month['end_at'],
                'amount': get_holiday_count_for_user_with_date_range_according_to_timesheet(
                    self.employee,
                    month['start_at'],
                    month['end_at']
                ),
                'display_name': month['display_name']
            }
            for month in self.remaining_months
        ]

    def get_monthly_working_days(self) -> list:
        return [
            {
                'from_date': month['start_at'],
                'to_date': month['end_at'],
                'amount': get_working_days_count_for_date_range(
                    self.employee,
                    month['start_at'],
                    month['end_at'],
                    self.include_holiday_off_day
                ),
                'display_name': month['display_name']
            } for month in self.remaining_months
        ]

    def get_monthly_rebate_amounts(self, payroll_row):
        remaining_rebate_months = get_remaining_fiscal_months_in_payroll(
            payroll_row, self.remaining_months[0]['start_at'],
            self.remaining_months[0]['end_at'], include_current_month=False
        )
        return [
            {
                'from_date': month['start_at'],
                'to_date': month['end_at'],
                'amount': float(remaining_rebate_months[month[
                    'display_name']]) if remaining_rebate_months else 0,
                'display_name': month['display_name']
            }
            for month in self.remaining_months
        ]
