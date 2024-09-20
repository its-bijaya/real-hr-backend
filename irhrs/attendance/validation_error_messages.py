from django.utils.translation import gettext_lazy as _

AT_LEAST_ONE_REQUIRED = _("This field must have at least one value")
AT_LEAST_ONE_DAY_REQUIRED = _("You must set at least one work day.")
START_TIME_MUST_BE_GREATER = _("Start time can not be greater than end time")
REPEATING_DAYS = _("Days are repeating. Please insure they are unique.")
CONFLICTING_WORK_DAYS = _("Work days are conflicting. Please check them.")

INVALID_CIDR = _("The passed value is not a valid IP address or a CIDR address.")
IP_FILTERS_REQUIRED = _("IP filters are required if web attendance is enabled.")
CONFLICTING_CIDR = _("Can not create more than one filter for a CIDR/IP")
OT_SETTING_REQUIRED = _("Overtime Setting is required if overtime is enabled")
HAS_TO_BE_OF_SAME_ORGANIZATION = _("Can not assign to work shift from "
                                   "different organization")
PUNCH_IN_MUST_BE_GREATER = _("Punch Out time must be greater than Punch In "
                             "time")
INVALID_DATE = _("Invalid date string")

SET_BOTH_HOURS_AND_DURATION = _("Set both working hours and duration "
                                "type.")
SET_LESS_THAN_24 = _("Set working hours less than 24 for daily.")
SET_LESS_THAN_768 = _("Set working hours less than 768 for monthly.")
SET_LESS_THAN_168 = _("Set working hours less than 168 for weekly.")
