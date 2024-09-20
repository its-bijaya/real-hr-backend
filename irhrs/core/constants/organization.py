GOVERNMENT, PRIVATE, PUBLIC, NONPROFIT = "Government", "Private", "Public", "Non-profit"
ORGANIZATION_OWNERSHIP = (
    (GOVERNMENT, 'Government'),
    (PRIVATE, 'Private'),
    (PUBLIC, 'Public'),
    (NONPROFIT, 'Non-profit')
)

ORGANIZATION_SIZE = [
    ('1 - 10 employees', '1 - 10 employees'),
    ('10 - 50 employees', '10 - 50 employees'),
    ('50 - 100 employees', '50 - 100 employees'),
    ('100 - 200 employees', '100 - 200 employees'),
    ('200 - 500 employees', '200 - 500 employees'),
    ('500 - 1000 employees', '500 - 1000 employees'),
    ('1000+ employees', '1000+ employees'),
    ('Confidential', 'Confidential')
]

IDLE = 'Idle'
USED = 'Used'
DAMAGED = 'Damaged'

ASSET_STATUS = (
    (IDLE, IDLE),
    (USED, USED),
    (DAMAGED, DAMAGED)
)

PER_DAMAGED = 'Permanent Damage'
RELEASED = 'Released'
TRANSFER = 'Transfer'
OTHERS = 'Others'

RELEASE_REMARK = (
    (PER_DAMAGED, PER_DAMAGED),
    (RELEASED, RELEASED),
    (TRANSFER, TRANSFER),
    (OTHERS, OTHERS)
)

DO, DONT, RULES, REGULATION = "Do", "Dont", "Rules", "Regulation"
MORAL_CHOICES = (
    (DO, "Do"),
    (DONT, "Don't"),
    (RULES, "Rules"),
    (REGULATION, "Regulation")
)

ORGANIZATION, DIVISION, INDIVIDUAL = "Organization", "Division", "Individual"
MESSAGE_LABEL_CHOICES = (
    (ORGANIZATION, "Organization"),
    (DIVISION, "Division"),
    (INDIVIDUAL, "Individual")
)

WORKLOG, PAYROLL, ASSESSMENT, TRAINING, RECRUITMENT, REIMBURSEMENT = ( 
    'worklog', 'payroll', 'assessment', 'training', 'recruitment', 'reimbursement'
)

APPLICATION_CHOICES = (
    (WORKLOG, WORKLOG),
    (PAYROLL, PAYROLL),
    (ASSESSMENT, ASSESSMENT),
    (TRAINING, TRAINING),
    (RECRUITMENT, RECRUITMENT),
    (REIMBURSEMENT, REIMBURSEMENT),
)
USER = 'User'
DIVISION_BRANCH = 'Division / Branch'
MEETING_ROOM = 'Meeting Room'
ASSIGNED_TO_CHOICES = (
    (USER, USER),
    (DIVISION_BRANCH, DIVISION_BRANCH),
    (MEETING_ROOM, MEETING_ROOM)
)

GLOBAL = 'global'
LEAVE = 'leave'

FISCAL_YEAR_CATEGORY = (
    (GLOBAL, 'Global'),
    (LEAVE, 'Leave')
)


# Email Settings
(
    BIRTHDAY_EMAIL,
    ANNIVERSARY_EMAIL,
    HOLIDAY_EMAIL,

    INVITED_TO_EVENT_EMAIL,
    EVENT_UPDATED_EMAIL,
    EVENT_CANCELED_DELETED_EMAIL,

    ASSIGNED_TO_TASK_EMAIL,
    ASSIGNED_AS_OBSERVER_TO_TASK_EMAIL,
    OBSERVED_TASK_UPDATED_EMAIL,
    ASSIGNED_TASK_UPDATED_EMAIL,

    SELF_LATE_IN_EMAIL,
    SUBORDINATE_LATE_IN_EMAIL,
    EMPLOYEE_LATE_IN_EMAIL_AS_ADMIN,
    SELF_EARLY_OUT_EMAIL,
    SUBORDINATE_EARLY_OUT_EMAIL,
    EMPLOYEE_EARLY_OUT_EMAIL_AS_ADMIN,
    SHIFT_ASSIGNED_EMAIL,
    OVERTIME_GENERATED_EMAIL,
    SUBORDINATE_APPLIED_OVERTIME_EMAIL,
    ACTION_ON_OVERTIME_EMAIL,
    SUBORDINATE_SENT_ADJUSTMENT_EMAIL,
    EMPLOYEE_SENT_ADJUSTMENT_EMAIL_AS_ADMIN,
    ACTION_ON_ADJUSTMENT_EMAIL,
    TRAVEL_REQUEST_APPROVAL_REQUESTED_EMAIL,
    TRAVEL_REQUEST_APPROVAL_REQUESTED_EMAIL_AS_ADMIN,
    ACTION_ON_TRAVEL_REQUEST_EMAIL,
    CREDIT_HOUR_APPROVAL_REQUESTED_FORWARDED_EMAIL,
    ACTION_ON_CREDIT_HOUR_EMAIL,

    LEAVE_REQUEST_ACTION_NEEDED_EMAIL,
    ACTION_ON_LEAVE_REQUEST_EMAIL,
    LEAVE_CANCEL_REQUEST_ACTION_NEEDED_EMAIL,
    LEAVE_CANCEL_REQUEST_ACTION_NEEDED_EMAIL_AS_ADMIN,
    ACTION_ON_LEAVE_CANCEL_REQUEST_EMAIL,
    LEAVE_BALANCE_UPDATED_EMAIL,

    PAYROLL_APPROVAL_NEEDED_EMAIL,
    ACTION_ON_PAYROLL_APPROVAL_EMAIL_AS_ADMIN,
    PAYROLL_DISBURSED_EMAIL,
    PAYSLIP_ACKNOWLEDGE_EMAIL_AS_ADMIN,
    ADVANCE_SALARY_REQUEST_APPROVAL_NEEDED_EMAIL,

    ASSESSMENT_ASSIGNED_UNASSIGNED_TO_USER_EMAIL,
    ASSESSMENT_COMPLETED_BY_USER_EMAIL,

    CONTRACT_EXPIRY_ALERT_EMAIL,

    TRAINING_ASSIGNED_UNASSIGNED_EMAIL,
    TRAINING_CANCELLED_EMAIL,
    TRAINING_REQUESTED_EMAIL,
    TRAINING_UPDATED_EMAIL,
    TRAINING_REQUESTED_ACTION_EMAIL,

    RESIGNATION_REQUEST_EMAIL,
    RESIGNATION_REQUEST_ACTION_EMAIL,
    RESIGNATION_REMINDER_EMAIL,
    
    ADVANCE_EXPENSE_REQUEST_EMAIL,
    ADVANCE_EXPENSES_SETTLEMENT_EMAIL,
    ADVANCE_EXPENSE_SETTING_APPROVE_OR_DENY,
    ADVANCE_EXPENSES_SETTLEMENT_APPROVE_OR_DENY,
    ADVANCE_EXPENSES_SETTLEMENT_BY_HR,
    ADVANCE_EXPENSES_REQUEST_CANCELLED_BY_HR,

    OVERTIME_RECALIBRATE_EMAIL,
    OVERTIME_CLAIM_REQUEST,
    OVERTIME_CLAIM_APPROVED_DENIED_CONFIRMED,
    OVERTIME_UNCLAIMED_EXPIRED,

    ATTENDANCE_ADJUSTMENT_REQUEST_EMAIL,
    ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_BY_SUPERVISOR_EMAIL,
    ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_DELETED_BY_HR_EMAIL,

    TRAVEL_ATTENDANCE_REQUEST_EMAIL,
    TRAVEL_ATTENDANCE_IS_APPROVED_DECLINED,


    CREDIT_HOUR_DELETE_REQUEST_IS_REQUESTED_FORWARDED_EMAIL,
    CREDIT_HOUR_DELETE_REQUEST_IS_APPROVED_DECLINED_EMAIL,
    CREDIT_HOUR_REQUEST_ON_BEHALF,

    ACTION_ON_PAYROLL_APPROVAL_BY_APPROVAL_LEVELS,
    PAYROLL_CONFIRMATION_BY_HR,
    PAYROLL_ACKNOWLEDGED_BY_USER,

    REBATE_IS_REQUESTED_BY_USER,
    REBATE_IS_APPROVED_DECLINED,
    REBATE_IS_REQUESTED_ON_BEHALF_USER_BY_HR,

    ADVANCE_SALARY_IS_REQUESTED_BY_USER,
    ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL,
    GENERATE_ADVANCE_SALARY_BY_HR,

    LEAVE_DEDUCTION_ON_PENALTY

) = (
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
    26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 
    49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81,
    82, 83, 84, 85, 86, 87, 88
)

EMAIL_TYPE_CHOICES = (
    (BIRTHDAY_EMAIL, "Birthday Email"),
    (ANNIVERSARY_EMAIL, "Anniversary Email"),
    (HOLIDAY_EMAIL, "Holiday Email"),

    (INVITED_TO_EVENT_EMAIL, "When you are invited to an event or meeting"),
    (EVENT_UPDATED_EMAIL, "When an event or meeting, you are involved, is updated"),
    (EVENT_CANCELED_DELETED_EMAIL, "When an event or meeting, you are involved, is cancelled"),

    (
        ASSESSMENT_ASSIGNED_UNASSIGNED_TO_USER_EMAIL,
        "When an assessment is assigned or unassigned to a user."
    ),
    (
        ASSESSMENT_COMPLETED_BY_USER_EMAIL,
        "When an user completes an assigned assessment(For HR Only)"
    ),

    (
        CREDIT_HOUR_APPROVAL_REQUESTED_FORWARDED_EMAIL,
        "When a credit hour approval is requested/forwarded"
    ),
    (
        ACTION_ON_CREDIT_HOUR_EMAIL, 
        "When credit hour request is approved/declined"
    ),
    (
        CONTRACT_EXPIRY_ALERT_EMAIL, 
        "When an employee's expiry date is in critical date range(For HR only)."
    ),

    (TRAINING_ASSIGNED_UNASSIGNED_EMAIL, "When a training is assigned or unassigned."),
    (TRAINING_CANCELLED_EMAIL, "When a training is deleted or cancelled."),
    (TRAINING_REQUESTED_EMAIL, "When a training is requested by user(For HR only)."),
    (TRAINING_REQUESTED_ACTION_EMAIL, "When a training request is acted upon."),
    (TRAINING_UPDATED_EMAIL, "When a training is updated."),

    (RESIGNATION_REQUEST_EMAIL, "When a user sends a resignation request."),
    (RESIGNATION_REQUEST_ACTION_EMAIL, "When HR takes an action on resignation request."),
    (
        RESIGNATION_REMINDER_EMAIL,
        "When HR does not take action on resignation request for a certain interval(For HR only)."
    ),

    (ADVANCE_EXPENSE_REQUEST_EMAIL, "When user requests for Advance expenses"),
    (ADVANCE_EXPENSES_SETTLEMENT_EMAIL, "When user requests for settlement"),

    (
        OVERTIME_GENERATED_EMAIL,
        "When overtime is generated"
    ),
    (
        OVERTIME_RECALIBRATE_EMAIL,
        "When overtime is re-calibrated"
    ),
    (
        OVERTIME_CLAIM_REQUEST,
        "When overtime claim request is sent"
    ),
    (
        OVERTIME_CLAIM_APPROVED_DENIED_CONFIRMED,
        "When overtime claim request is approved/declined/confirmed"
    ),
    (
        OVERTIME_UNCLAIMED_EXPIRED,
        "When unclaimed overtime is expired"
    ),
    
    (
        ADVANCE_EXPENSE_SETTING_APPROVE_OR_DENY, 
        "When requests is Approved and Denied for request of Advance expenses"
    ),
    (
        ADVANCE_EXPENSES_SETTLEMENT_APPROVE_OR_DENY,
        "When requests for settlement Approved or Denied"
    ),
    (
        ADVANCE_EXPENSES_SETTLEMENT_BY_HR, 
        "When HR has to settle the settlement request approved by approval levels"
    ),
    (   
        ADVANCE_EXPENSES_REQUEST_CANCELLED_BY_HR, 
        "When HR cancels the approved advance expense request"
    ),

    (
        ATTENDANCE_ADJUSTMENT_REQUEST_EMAIL, 
        "When attendance adjustment is requested by user"
    ),
    (
        ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_BY_SUPERVISOR_EMAIL,
        "When attendance adjustment is approved or declined by supervisor"
    ),
    (
        ATTENDANCE_ADJUSTMENT_IS_APPROVED_DECLINED_DELETED_BY_HR_EMAIL,
        "When attendance adjustment is approved, declined or deleted by hr"
    ),
    (
        TRAVEL_ATTENDANCE_REQUEST_EMAIL,
        "When travel attendance request is sent by user"
    ),
    (
        TRAVEL_ATTENDANCE_IS_APPROVED_DECLINED,
        "When travel attendance request is approved or declined"
    ),
    (
        CREDIT_HOUR_DELETE_REQUEST_IS_REQUESTED_FORWARDED_EMAIL,
        "When credit hour delete request is requested/forwarded"
    ),
    (
        CREDIT_HOUR_DELETE_REQUEST_IS_APPROVED_DECLINED_EMAIL,
        "When credit hour delete request is approved/declined"
    ),
    (
        CREDIT_HOUR_REQUEST_ON_BEHALF,
        "When credit hour is requested on behalf"
    ),
    (
        PAYROLL_APPROVAL_NEEDED_EMAIL,
        "When HR forward Payroll to approval levels for approval"
    ),
    (
        ACTION_ON_PAYROLL_APPROVAL_BY_APPROVAL_LEVELS,
        "When approval level approve or denies the payroll"
    ),
    (
        PAYROLL_CONFIRMATION_BY_HR,
        "When payroll is confirmed by HR after approval from appoval levels"
    ),
    (
        PAYROLL_ACKNOWLEDGED_BY_USER,
        "When Payroll is acknowledged by user"
    ),
    (
        REBATE_IS_REQUESTED_BY_USER,
        "When rebate is requested by user"
    ),
    (
        REBATE_IS_APPROVED_DECLINED,
        "When rebate is approved/decline by hr"
    ),
    (
        REBATE_IS_REQUESTED_ON_BEHALF_USER_BY_HR,
        "When Rebate is requested by hr on behalf of user"
    ),
    (
        ADVANCE_SALARY_IS_REQUESTED_BY_USER,
        "When advance salary is requested by user"
    ),
    (
        ADVANCE_SALARY_IS_APPROVED_DECLINED_BY_LEVEL_OF_APPROVAL,
        "When level of approval decline/approved the advance salary"
    ),
    (
        GENERATE_ADVANCE_SALARY_BY_HR,
        "When hr generates the approved advance salary"
    ),
    (
        LEAVE_DEDUCTION_ON_PENALTY,
        "When leave is deducted by the penalty"

    )
)
