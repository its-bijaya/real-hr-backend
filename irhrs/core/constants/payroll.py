DAY = 'Day'
MONTH = 'Month'

CHOICES = (
    (DAY, DAY),
    (MONTH, MONTH),
)

SUPERVISOR = 'Supervisor'
EMPLOYEE = 'Employee'

APPROVED_BY = (
    (SUPERVISOR, SUPERVISOR),
    (EMPLOYEE, EMPLOYEE),
)
ALL = 'All'
FIRST = 'First'
SECOND = 'Second'
THIRD = 'Third'

SUPERVISOR_LEVEL = (
    (FIRST, '1st Level'),
    (SECOND, '2nd Level'),
    (THIRD, '3rd Level'),
)
SUPERVISOR_LEVEL_FOR_RECRUITMENT = (
    (ALL, ALL),
    (FIRST, '1st Level'),
    (SECOND, '2nd Level'),
    (THIRD, '3rd Level'),
)

PENDING = 'Pending'
FORWARDED = 'Forwarded'
CONFIRMED = 'Confirmed'

REQUESTED, APPROVED, REPAYMENT, DENIED, COMPLETED, CANCELED, = (
    'Requested', 'Approved', 'Repayment', 'Denied', 'Completed', 'Canceled',
)
ADVANCE_SALARY_REQUEST_STATUS_CHOICES = (
    (REQUESTED, 'Requested'),
    (APPROVED, 'Approved'),
    (REPAYMENT, 'Repayment'),
    (DENIED, 'Denied'),
    (COMPLETED, 'Completed'),
    (CANCELED, 'Canceled')
)

ADVANCE_EXPENSE_REQUEST_STATUS_CHOICES = (
    (REQUESTED, 'Requested'),
    (APPROVED, 'Approved'),
    # (FORWARDED, 'Forwarded'),
    (DENIED, 'Denied'),
    (CANCELED, 'Canceled')
)

APPROVAL_STATUS_CHOICES = (
    (PENDING, 'Pending'),
    (APPROVED, 'Approved'),
    (DENIED, 'Denied')
)

SURPLUS_REQUEST_STATUS_CHOICES = (
    (REQUESTED, 'Requested'),
    (APPROVED, 'Approved'),
    (DENIED, 'Denied'),
)

SALARY_DEDUCTION = "Salary Deduction"
CASH = "Cash"
CHEQUE = "Cheque"

REPAYMENT_TYPES = (
    (SALARY_DEDUCTION, "Salary Deduction"),
    (CASH, "Cash"),
    (CHEQUE, "Cheque")
)

UNIT_OF_WORK_REQUEST_STATUS_CHOICES = (
    (REQUESTED, 'Requested'),
    (FORWARDED, 'Forwarded'),
    (APPROVED, 'Approved'),
    (DENIED, 'Denied'),
    (CANCELED, 'Canceled'),
    (CONFIRMED, 'Confirmed')
)

ADVANCE_EXPENSE_REQUEST_CANCEL_STATUS_CHOICES = (
    (REQUESTED, 'Requested'),
    (APPROVED, 'Approved'),
    (DENIED, 'Denied')
)
