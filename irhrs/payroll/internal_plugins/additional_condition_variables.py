from datetime import timedelta

from django.conf import settings

from irhrs.attendance.constants import HOLIDAY
from irhrs.attendance.utils.get_lost_hours_as_per_shift import get_lost_hours_for_date_range
from irhrs.attendance.models.attendance import TimeSheet
from irhrs.attendance.utils.payroll import get_work_days_count_from_virtual_timesheets
from irhrs.attendance.utils.timesheet import simulate_timesheets
from irhrs.core.utils import nested_getattr
from irhrs.payroll.internal_plugins.registry import register_plugin


@register_plugin('total-lost-hours')
def total_lost_hours(calculator, package_heading):

    employee = calculator.employee
    from_date = calculator.from_date
    to_date = calculator.to_date
    organization = calculator.get_organization()
    simulated_from = calculator.simulated_from
    if simulated_from:
        to_date = simulated_from
    _previous_simulated_from = nested_getattr(calculator, 'previous_payroll.payroll.simulated_from')
    if _previous_simulated_from:
        from_date = _previous_simulated_from

    total_time = get_lost_hours_for_date_range(
        employee.id, organization, from_date, to_date,
        calculate_unpaid_breaks=settings.CALCULATE_UNPAID_BREAKS_IN_INTERNAL_PLUGIN,
        ignore_seconds=settings.IGNORE_SECOND_IN_TOTAL_LOST_HOURS
    )
    return round(total_time/3600, 2), []


@register_plugin('total-working-days')
def total_working_days(calculator, package_heading):

    employee = calculator.employee
    from_date = calculator.from_date
    to_date = calculator.to_date
    simulated_from = calculator.simulated_from
    from irhrs.attendance.utils.payroll import get_working_days_from_organization_calendar
    include_holiday_offday = calculator.payroll_config.include_holiday_offday_in_calculation

    days = 0
    shift = nested_getattr(employee, 'attendance_setting.work_shift')
    if shift and simulated_from:
        days += get_work_days_count_from_virtual_timesheets(
            simulate_timesheets(
                employee, shift, simulated_from, to_date, include_holiday_offday
            ), include_holiday_offday)
        to_date = simulated_from - timedelta(days=1)

    days += get_working_days_from_organization_calendar(
        user=employee,
        start=from_date,
        end=to_date,
        include_holiday_offday=include_holiday_offday
    )

    return days, []


@register_plugin('total-holiday-count')
def total_holiday_count(calculator, package_heading):

    employee = calculator.employee
    from_date = calculator.from_date
    to_date = calculator.to_date
    return TimeSheet.objects.filter(
        timesheet_user=employee,
        timesheet_for__gte=from_date,
        timesheet_for__lte=to_date,
        coefficient=HOLIDAY
    ).count(), []
