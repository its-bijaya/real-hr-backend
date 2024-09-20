from irhrs.core.constants.user import GENDER_CHOICES, MARITAL_STATUS_CHOICES

YEARS, MONTHS, DAYS = "Years", "Months", "Days"
HOURS, MINUTES = "Hours", "Minutes"

LEAVE_LIMIT_DURATION_CHOICES = (
    (YEARS, "Years"),
    (MONTHS, "Months")
)

LEAVE_DURATION_CHOICES = (
    (YEARS, "Years"),
    (MONTHS, "Months"),
    (DAYS, "Days")
)

YEARLY, MONTHLY = "Yearly", "Monthly"
LEAVE_TAKEN_INTERVAL_CHOICES = (
    (YEARLY, "Yearly"),
    (MONTHLY, "Monthly")
)

PRIOR_APPROVAL_UNITS = (
    (DAYS, 'Days'),
    (HOURS, 'Hours'),
    (MINUTES, 'Minutes')
)

GENERAL, YEARS_OF_SERVICE, TIME_OFF, COMPENSATORY, CREDIT_HOUR = (
    "General", "Years of Service", "Time Off", "Compensatory", "Credit Hour"
)
LEAVE_TYPE_CATEGORIES = (
    (GENERAL, "General"),
    (YEARS_OF_SERVICE, "Years of Service"),
    (TIME_OFF, "Time Off"),
    (COMPENSATORY, "Compensatory"),
    (CREDIT_HOUR, "Credit Hour"),
)
# category to field in master setting
CATEGORY_FIELD_MAP = {
    YEARS_OF_SERVICE: "years_of_service",
    TIME_OFF: "time_off",
    COMPENSATORY: "compensatory",
    CREDIT_HOUR: 'credit_hour',
}

ASSIGNED, REMOVED, RENEWED, ADDED, DEDUCTED, UPDATED, ASSIGNED_WITH_BALANCE = (
    "Assigned", "Removed", "Renewed", "Added", "Deducted", "Updated", "Initialized"
)
LEAVE_ACCOUNT_ACTION_CHOICES = (
    (ASSIGNED, "Assigned"),
    (REMOVED, "Removed"),
    (RENEWED, "Renewed"),
    (ADDED, "Added"),
    (DEDUCTED, "Deducted"),
    (UPDATED, "Updated"),
    (ASSIGNED_WITH_BALANCE, "Assigned with balance")
)

REQUESTED, APPROVED, DENIED, FORWARDED = \
    'Requested', 'Approved', 'Denied', 'Forwarded'
LEAVE_REQUEST_STATUS = (
    (REQUESTED, 'Requested'),
    (APPROVED, 'Approved'),
    (DENIED, 'Denied'),
    (FORWARDED, 'Forwarded'),
)

LEAVE_REQUEST_DELETE_STATUS = (
    (REQUESTED, 'Requested'),
    (APPROVED, 'Approved'),
    (FORWARDED, 'Forwarded'),
    (DENIED, 'Denied'),
)


FIRST_HALF, SECOND_HALF, FULL_DAY = 'first', 'second', 'full'
HALF_LEAVE_CHOICES = (
    (FIRST_HALF, 'First Half'),
    (SECOND_HALF, 'Second Half'),
    (FULL_DAY, 'Full Day')
)

# master settings status choices (used in property)
IDLE, ACTIVE, EXPIRED = 'Idle', 'Active', 'Expired'

# Applicable for Gender choices
ALL = 'All'
APPLICABLE_GENDER_CHOICES = GENDER_CHOICES + (
    (ALL, 'All'),
)

# Applicable for Marital Status
APPLICABLE_MARITAL_STATUS_CHOICES = MARITAL_STATUS_CHOICES + (
    (ALL, 'All'),
)

PROCESSED, ENCASHED, GENERATED = 'Processed', 'Encashed', 'Generated'
ENCASHMENT_CHOICE_TYPES = (
    (GENERATED, 'Generated'),
    (APPROVED, 'Approved'),
    (ENCASHED, 'Encashed'),
    (DENIED, 'Denied')
)

SUPERVISOR = 'supervisor'
APPROVER = 'approver'

RECIPIENT_TYPE = (
    (SUPERVISOR, 'Supervisor'),
    (APPROVER, 'Approver')
)

HOURLY_LEAVE_CATEGORIES = [TIME_OFF, CREDIT_HOUR]

EXCLUDE_HOLIDAY_AND_OFF_DAY = 'Exclude Holiday And Off Day'
INCLUDE_HOLIDAY = 'Include Holiday'
INCLUDE_OFF_DAY = 'Include Off Day'
INCLUDE_HOLIDAY_AND_OFF_DAY = 'Include Holiday And Off Day'

HOLIDAY_INCLUSIVE_OPTION = (
    (EXCLUDE_HOLIDAY_AND_OFF_DAY, EXCLUDE_HOLIDAY_AND_OFF_DAY),
    (INCLUDE_HOLIDAY, INCLUDE_HOLIDAY),
    (INCLUDE_OFF_DAY, INCLUDE_OFF_DAY),
    (INCLUDE_HOLIDAY_AND_OFF_DAY, INCLUDE_HOLIDAY_AND_OFF_DAY)
)

ADJACENT_OFFDAY_HOLIDAY_INCLUSIVE_OPTION = (
    (INCLUDE_HOLIDAY, INCLUDE_HOLIDAY),
    (INCLUDE_OFF_DAY, INCLUDE_OFF_DAY),
    (INCLUDE_HOLIDAY_AND_OFF_DAY, INCLUDE_HOLIDAY_AND_OFF_DAY)
)
LEAVE_RENEW, EMPLOYEE_SEPARATION = "Leave Renew", "Employee Separation"
LEAVE_ENCASHMENT_SOURCE_CHOICES = (
    (LEAVE_RENEW, "Leave Renew"),
    (EMPLOYEE_SEPARATION, "Employee Separation")
)

INSUFFICIENT_BALANCE = 'insufficient_balance'
