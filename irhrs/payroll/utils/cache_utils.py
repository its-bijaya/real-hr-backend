from functools import lru_cache
from contextlib import ContextDecorator


from irhrs.payroll.utils.unit_of_work import get_unit_of_work_done as _get_unit_of_work_done
from irhrs.payroll.utils.helpers import get_days_to_be_paid as _gwd
from irhrs.attendance.utils.payroll import (
    get_working_days_from_organization_calendar as _gwdfoc,
    get_hours_of_work as _ghow,
    get_absent_days as _get_absent_days,
    get_work_days_count_from_simulated_timesheets as _get_work_days_count_from_simulated_timesheets,
    get_worked_days_for_daily_heading as _get_worked_days_for_daily_heading,
)
from irhrs.leave.utils.payroll import get_unpaid_leave_days as _get_unpaid_leave_days


get_unit_of_work_done = lru_cache(_get_unit_of_work_done)
gwd = lru_cache(_gwd)
gwdfoc = lru_cache(_gwdfoc)
ghow = lru_cache(_ghow)
get_absent_days = lru_cache(_get_absent_days)
get_work_days_count_from_simulated_timesheets = lru_cache(
    _get_work_days_count_from_simulated_timesheets
)
get_worked_days_for_daily_heading = lru_cache(
    _get_worked_days_for_daily_heading)
get_unpaid_leave_days = lru_cache(_get_unpaid_leave_days)


class CachedPayrollInput(ContextDecorator):
    def __enter__(self):
        pass

    def __exit__(self, *exec):
        get_unit_of_work_done.cache_clear()
        gwd.cache_clear()
        gwdfoc.cache_clear()
        ghow.cache_clear()
        get_absent_days.cache_clear()
        get_work_days_count_from_simulated_timesheets.cache_clear()
        get_worked_days_for_daily_heading.cache_clear()
        get_unpaid_leave_days.cache_clear()
