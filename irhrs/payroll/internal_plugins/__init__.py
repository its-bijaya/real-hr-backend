import sys

from .duty_station import duty_station_plugin
# from .user_voluntary_rebate import employee_health_insurance_plugin, \
#     employee_life_insurance_plugin, employee_cit_plugin, employee_donation_plugin
from .user_voluntary_rebate import user_voluntary_rebate_fxn_plugin
from .expense_settlement import taxable_expense
from .leave_encashment import leave_encashment_from_renew, leave_encashment_from_off_boarding
from .timesheet_penalty import timesheet_penalty_reduction
from .adjacent_timesheet_offday_holiday_penalty import adjacent_timesheet_offday_holiday_penalty_reduction
from .shift_presence_count import shift_presence_count_fxn_plugin
from .annual import annual_amount_fxn_plugin
from .worklog import amount_from_worklog
from .additional_condition_variables import total_working_days, total_lost_hours, total_holiday_count

if 'test' in sys.argv:
    from .test_plugins import (
        example_plugin1,
        example_plugin2,
        example_fxn_plugin
    )
