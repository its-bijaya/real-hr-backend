from django.utils.translation import gettext_lazy as _

WORKDAY, OFFDAY, HOLIDAY, = 1, 2, 3

TIMESHEET_COEFFICIENTS = (
    (HOLIDAY, 'Holiday'),
    (OFFDAY, 'Offday'),
    (WORKDAY, 'Workday')
)

FIRST_HALF, SECOND_HALF, FULL_LEAVE, NO_LEAVE, TIME_OFF, CREDIT_HOUR, CREDIT_TIME_OFF = (
    'First Half', 'Second Half', 'Full Leave', 'No Leave', 'Time Off', 'Credit Hour', 'credit-time-off'
)

LEAVE_COEFFICIENTS = (
    (FIRST_HALF, 'First Half'),
    (SECOND_HALF, 'Second Half'),
    (FULL_LEAVE, 'Full Leave'),
    (NO_LEAVE, 'No Leave')
)
HOUR_OFF_COEFFICIENT = (
    (TIME_OFF, 'Time Off'),
    (CREDIT_HOUR, 'Credit Hour'),
    (CREDIT_TIME_OFF, 'Credit Hour & Time Off'),
)

DEVICE = 'Device'
WEB_APP = 'Web App'
MOBILE_APP = 'Mobile App'
RFID_CARD = 'RFID Card'
PASSWORD = 'Password'
ATT_ADJUSTMENT = 'Att Adjustment'
TRAVEL_ATTENDANCE = 'Travel Att'
TRAINING_ATTENDANCE = 'Training Att'
METHOD_OTHER = 'Other'
METHOD_IMPORT = 'Import'

TIMESHEET_ENTRY_METHODS = (
    (DEVICE, 'Device'),
    (WEB_APP, 'Web App'),
    (MOBILE_APP, 'Mobile App'),
    (RFID_CARD, 'RFID Card'),
    (PASSWORD, 'Password'),
    (ATT_ADJUSTMENT, 'Attendance Adjustment'),
    (METHOD_OTHER, 'Other'),
    (METHOD_IMPORT, 'Import'),
    (TRAVEL_ATTENDANCE, 'Travel Attendance'),
    (TRAINING_ATTENDANCE, 'Training Attendance')
)

PUNCH_IN = 'Punch In'
PUNCH_OUT = 'Punch Out'
BREAK_IN = 'Break In'
BREAK_OUT = 'Break Out'
TYPE_UNKNOWN = 'Unknown'

TIMESHEET_ENTRY_TYPES = (
    (PUNCH_IN, 'Punch In'),
    (PUNCH_OUT, 'Punch Out'),
    (BREAK_IN, 'Break In'),
    (BREAK_OUT, 'Break Out'),
    (TYPE_UNKNOWN, 'Unknown')
)

EARLY_IN = 'Early In'
TIMELY_IN = 'Timely In'
LATE_IN = 'Late In'
EARLY_OUT = 'Early Out'
TIMELY_OUT = 'Timely Out'
LATE_OUT = 'Late Out'
UNCATEGORIZED = 'Uncategorized'
MISSING = 'Missing'

TIMESHEET_ENTRY_CATEGORIES = (
    (UNCATEGORIZED, 'Uncategorized'),
    (EARLY_IN, 'Early In'),
    (TIMELY_IN, 'Timely In'),
    (LATE_IN, 'Late In'),
    (EARLY_OUT, 'Early Out'),
    (TIMELY_OUT, 'Timely Out'),
    (LATE_OUT, 'Late Out')
)

REQUESTED = 'Requested'
FORWARDED = 'Forwarded'
APPROVED = 'Approved'
DECLINED = 'Declined'
CONFIRMED = 'Confirmed'
UNCLAIMED = 'Unclaimed'
CANCELLED = 'Cancelled'
GENERATED = 'Generated'

NOT_ADDED = 'Not Added'
ADDED = 'Added'

# IF Updated here, also update in configurations.py
TEA_BREAK, CLIENT_VISIT, LUNCH_BREAK, MEETING, PERSONAL, OTHERS = (
    'Tea Break', 'Client Visit', 'Lunch Break', 'Meeting', 'Personal Break', 'Others'
)

TIMESHEET_ENTRY_REMARKS = (
    (TEA_BREAK, 'Tea Break'),
    (CLIENT_VISIT, 'Client Visit'),
    (LUNCH_BREAK, 'Lunch Break'),
    (MEETING, 'Meeting'),
    (PERSONAL, 'Personal Break'),
    (OTHERS, 'Others'),
    (PUNCH_IN, 'Punch In'),
    (PUNCH_OUT, 'Punch Out'),
)

TRAVEL_ATTENDANCE_STATUS_CHOICES = (
    (REQUESTED, REQUESTED),
    (FORWARDED, FORWARDED),
    (APPROVED, APPROVED),
    (DECLINED, DECLINED),
    (CANCELLED, CANCELLED),
)

STATUS_CHOICES = (
    (UNCLAIMED, 'Unclaimed'),
    (REQUESTED, 'Requested'),
    (FORWARDED, 'Forwarded'),
    (APPROVED, 'Approved'),
    (DECLINED, 'Declined'),
    (CONFIRMED, 'Confirmed')
)

PRE_APPROVAL_STATUS_CHOICES = (
    (REQUESTED, 'Requested'),
    (FORWARDED, 'Forwarded'),
    (APPROVED, 'Approved'),
    (DECLINED, 'Declined'),
    (CANCELLED, 'Cancelled'),
)

CREDIT_HOUR_STATUS_CHOICES = (
    (REQUESTED, 'Requested'),
    (FORWARDED, 'Forwarded'),
    (CANCELLED, 'Cancelled'),
    (APPROVED, 'Approved'),
    (DECLINED, 'Declined'),
)

TIMESHEET_APPROVAL_CHOICES = (
    (REQUESTED, 'Requested'),
    (FORWARDED, 'Forwarded'),
    (APPROVED, 'Approved'),
    (DECLINED, 'Declined'),
)

ADJUSTMENT_STATUS_CHOICES = (
    (REQUESTED, 'Requested'),
    (FORWARDED, 'Forwarded'),
    (APPROVED, 'Approved'),
    (DECLINED, 'Declined'),
    (CANCELLED, 'Cancelled')
)

ADD, UPDATE, DELETE = 'add', 'update', 'delete'
ADJUSTMENT_ACTION_CHOICES = (
    (ADD, 'Add'),
    (UPDATE, 'Update'),
    (DELETE, 'Delete'),
)

ATTENDANCE_APPROVAL_STATUS_CHOICES = (
    (REQUESTED, 'Requested'),
    (APPROVED, 'Approved'),
    (DECLINED, 'Declined'),
)

TIMESHEET_REPORT_REQUEST_CHOICES = (
    (GENERATED, "Generated"),
    (REQUESTED, "Requested"),
    (APPROVED, 'Approved'),
    (FORWARDED, 'Forwarded'),
    (CONFIRMED, 'Confirmed'),
    (DECLINED, 'Declined'),
)

SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY = 1, 2, 3, 4, 5, 6, 7

WEEK_DAYS_CHOICES = (
    (SUNDAY, 'Sunday'),
    (MONDAY, 'Monday'),
    (TUESDAY, 'Tuesday'),
    (WEDNESDAY, 'Wednesday'),
    (THURSDAY, 'Thursday'),
    (FRIDAY, 'Friday'),
    (SATURDAY, 'Saturday'),
)

DAILY, WEEKLY, MONTHLY = 1, 2, 3
OVERTIME_CALCULATION_CHOICES = (
    (DAILY, 'Daily'),
    (WEEKLY, 'Weekly'),
)

CREDIT_HOUR_CALCULATION_CHOICES = (
    (DAILY, 'Daily'),
    (WEEKLY, 'Weekly'),
    (MONTHLY, 'Monthly')
)


PUNCH_IN_ONLY, PUNCH_OUT_ONLY, BOTH, EITHER = (
    'punch_in', 'punch_out', 'both', 'either',
)

OVERTIME_APPLICATION_AFTER_CHOICES = (
    (BOTH, 'Both'),
    (EITHER, 'Either')
)

NEITHER = 'neither'
OVERTIME_REDUCTION_CHOICES = (
    (PUNCH_IN_ONLY, 'Punch In Only'),
    (PUNCH_OUT_ONLY, 'Punch Out Only'),
    (BOTH, 'Both'),
    (NEITHER, 'Neither')
)
CREDIT_HOUR_REDUCTION_CHOICES = OVERTIME_REDUCTION_CHOICES

DAYS, MONTHS, WEEKS, YEARS = ('d', 'm', 'w', 'y')
EXPIRATION_CHOICES = (
    (DAYS, 'Days'),
    (MONTHS, 'Months'),
    (YEARS, 'Years')
)
DURATION_UNIT_CHOICES = (
    (DAYS, 'Days'),
    (WEEKS, 'Weeks'),
    (MONTHS, 'Months'),
)

GENERATE_BOTH, GENERATE_AFTER_DEDUCTION, NO_OVERTIME = (
    'both', 'deduction', 'no'
)

OVERTIME_AFTER_COMPENSATORY = (
    (GENERATE_BOTH, 'Generate Both'),
    (GENERATE_AFTER_DEDUCTION, 'Generate After Deduction'),
    (NO_OVERTIME, 'No Overtime')
)

OT_HOLIDAY, OT_OFFDAY, OT_WORKDAY, OT_LEAVE = (
    'Holiday', 'Offday', 'Workday', 'Leave'
)
OVERTIME_RATE_CHOICES = (
    (OT_HOLIDAY, 'Holiday'),
    (OT_OFFDAY, 'Offday'),
    (OT_WORKDAY, 'Workday'),
    (OT_LEAVE, 'Leave')
)
# Constraints for Overtime
WORK_DAYS = 7
DAILY_OVERTIME_LIMIT_IN_HOURS = 24
WEEKLY_OVERTIME_LIMIT_IN_HOURS = 24 * 7
MONTHLY_OVERTIME_LIMIT_IN_HOURS = WEEKLY_OVERTIME_LIMIT_IN_HOURS * 4


OVERTIME_DELTA_MAX = 50  # in minutes
OVERTIME_DELTA_VALIDATION_MESSAGE_MAX = _(
)

OFF_DAY_OVERTIME_LIMIT = DAILY_OVERTIME_LIMIT_IN_HOURS * 60
OFF_DAY_OVERTIME_LIMIT_MESSAGE = _(
)

SYNC_FAILED, SYNC_PENDING, SYNC_SUCCESS = 1, 2, 3

ATTENDANCE_CACHE_REASONS = (
    (SYNC_PENDING, 'Pending sync'),
    (SYNC_FAILED, 'Sync Failed'),
    (SYNC_SUCCESS, 'Sync Success')
)

ADMS, DIRSYNC, DONT_SYNC, EXTERNAL_SERVER = 1, 2, 3, 4
SYNC_METHODS = [
    (ADMS, 'ADMS'),
    (DIRSYNC, 'Dirsync'),
    (EXTERNAL_SERVER, 'External Server'),
    (DONT_SYNC, 'Do not sync')
]

TOTAL_WEEK_DAYS = 5

SENT, FAILED = 'Sent', 'Failed'
NOTIFICATION_STATUS_CHOICES = (
    (SENT, 'Sent'),
    (FAILED, 'Failed')
)

SYNC_HANDLERS = {
    ADMS: 'irhrs.attendance.handlers.adms_from_mysql_database.AdmsHandler',
    DIRSYNC: 'irhrs.attendance.handlers.dirsync.DirsyncHandler'
}

WH_DAILY, WH_WEEKLY, WH_MONTHLY = "Daily", "Weekly", "Monthly"
WORKING_HOURS_DURATION_CHOICES = (
    (WH_DAILY, "Daily"),
    (WH_WEEKLY, "Weekly"),
    (WH_MONTHLY, "Monthly")
)


FULL_DAY = 'Full Day'
TRAVEL_ATTENDANCE_PART_CHOICES = (
    (FIRST_HALF, 'First Half'),
    (SECOND_HALF, 'Second Half'),
    (FULL_DAY, 'Full Day')
)

INVALID_MODE_ACTIONS = {
    FORWARDED: ['hr'],
    CANCELLED: ['hr', 'supervisor']
}


LEAVE, PAYROLL = 'leave', 'payroll'
P_DAYS, P_MONTH = 'days', 'month'
REDUCTION_TYPE_CHOICES = (
    (LEAVE, 'Leave'),
    (PAYROLL, 'Payroll')
)
PENALTY_COUNTER_UNIT_CHOICES = (
    (P_DAYS, 'Days'),
    (P_MONTH, 'Month'),
)

BREAK_OUT_STATUS_CHOICES = (
    (GENERATED, 'Generated'),
    (CONFIRMED, 'Confirmed'),
    (CANCELLED, 'Cancelled'),
)
FREQUENCY, DURATION = 'frequency', 'duration'
TIMESHEET_PENALTY_CALCULATION_CHOICES = (
    (FREQUENCY, 'Frequency'),
    (DURATION, 'Duration'),
)

CREDIT_STATUS = (
    (NOT_ADDED, 'Not Added' ),
    (ADDED, 'Added')
)

