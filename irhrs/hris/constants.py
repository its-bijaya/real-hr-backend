from irhrs.core.constants.user import PARTING_REASON_CHOICES
from irhrs.permission.constants.permissions import (
    HRIS_PERMISSION,
    HRIS_OFF_BOARDING_PERMISSION,
    HRIS_SEPARATION_TYPE_PERMISSION,
    RESIGNATION_PERMISSION,
    EXIT_INTERVIEW_PERMISSION,
)

ONBOARDING, OFFBOARDING, CHANGE_TYPE, OFFER_LETTER, CUSTOM = (
    'on', 'off', 'change', 'offer', 'custom'
)

CHANGE_TYPE_CHOICES = (
    (ONBOARDING, 'On Boarding',),
    (OFFBOARDING, 'Off Boarding',),
    (CHANGE_TYPE, 'Change Type'),
)

LETTER_TEMPLATE_TYPE_CHOICES = (
    (OFFER_LETTER, 'Offer Letter'),
    (CUSTOM, 'Custom')
) + CHANGE_TYPE_CHOICES

OFFER_LETTER_LETTER_PARAMS = {
    '{{full_name}}': 'Full Name of the on boarding employee.',
    '{{date_of_join_AD}}': 'Date of Join for on boarding employee on A.D. format.',
    '{{date_of_join_BS}}': 'Date of Join for on boarding employee on B.S. format.',
    '{{employment_level}}': 'Employment Level of the on boarding employee.',
    '{{employment_status}}': 'Employment Status of the on boarding employee.',
    '{{job_title}}': 'Job title of the on boarding employee.',
    '{{step}}': 'Employment Step of the on boarding employee.',
    '{{division}}': 'Division of the on boarding employee.',
    '{{payroll}}': 'Payroll of the on boarding employee.',
    '{{company_name}}': 'Organization of the on boarding employee.',
    '{{company_address}}': 'Organization address of the on boarding employee.',
    '{{branch}}': 'Branch of the on boarding employee.',
    '{{deadline}}': 'Deadline to accept the job offer.',
    '{{address}}': 'Address of the on boarding employee.',
    '{{gender}}': 'Gender of the on boarding employee.',
    '{{email}}': 'Email to send the job offer to.',
    '{{contract_period}}': 'Contract end date for the on boarding employee. '
                           '(if applicable)',
    '{{url}}': 'The url user shall click to accept/decline the job offer.'
}
CHANGE_TYPE_LETTER_PARAMS = {
    '{{name}}': 'Name of employee whose employment is being changed.',
    '{{nationality}}': 'Nationality of employee whose employment is being '
                       'changed.',
    '{{change_type}}': 'Name of the employment change type.',
    '{{effective_from}}': 'Effective date of employment being changed.',
    '{{job_title}}': 'Job title of the new employment.',
    '{{division}}': 'Division the employee will be transferred to.',
    '{{company_address}}': 'Division the employee will be transferred to.',
    '{{company_name}}': 'Division the employee will be transferred to.',
    '{{employment_level}}': 'Name of Employment Level to which the employee '
                            'will be changed to.',
    '{{employment_status}}': 'Name of employment status the employee will be '
                             'changed to.',
    '{{pan_number}}': 'PAN Number of employee whose employment is being '
                      'changed.',
    '{{cit_number}}': 'CIT Number of employee whose employment is being '
                      'changed.',
    '{{pf_number}}': 'PF Number of employee whose employment is being changed.',
    '{{citizenship_number}}': 'Citizenship number of the employee whose '
                              'employment is being changed.',
    '{{passport_number}}': 'Passport Number of employee whose employment is '
                           'being changed.',
    '{{branch}}': 'Branch the employee will be transferred to.',
    '{{step}}': 'Step of the new employment of the user.',
    '{{payroll}}': 'New payroll assigned to the employee.',
    '{{dob}}': 'Date of Birth of employee whose employment is being changed.',
    '{{date_of_join_AD}}': 'Date of Join of employee whose employment is being '
                        'changed on A.D. format.',
    '{{date_of_join_BS}}': 'Date of Join of employee whose employment is being '
                        'changed on B.S. format.',
}

ONBOARDING_LETTER_PARAMS = {
    '{{name}}': 'Full Name of the on boarding employee.',
    '{{nationality}}': 'Nationality of the on boarding employee.',
    '{{dob}}': 'Date of Birth of the on boarding employee.',
    '{{effective_from}}': 'Effective Date of the user\'s experience',
    '{{job_title}}': 'Job Title of the on boarding employee',
    '{{division}}': 'Division the on boarding employee will be at.',
    '{{branch}}': 'Branch the on boarding employee will be at.',
    '{{employment_level}}': 'Employment level of the on boarding employee.',
    '{{employment_status}}': 'Employment Status of the on boarding employee.',
    '{{step}}': 'Current step of the on boarding employee.',
    '{{pan_number}}': 'PAN Number of the on boarding employee. (Must be set '
                      'in User\'s Legal Info)',
    '{{cit_number}}': 'CIT Number of the on boarding employee. (Must be set '
                      'in User\'s Legal Info)',
    '{{pf_number}}': 'PF Number of the on boarding employee. (Must be set '
                      'in User\'s Legal Info)',
    '{{citizenship_number}}': 'Citizenship number of the on boarding '
                              'employee. (Must be set  in User\'s Legal Info)',
    '{{passport_number}}': 'Passport Number of the on boarding employee.'
                           '(Must be set in User\'s Legal Info)',
    '{{payroll}}': 'Payroll the on boarding employee is assigned.',
    '{{date_of_join_AD}}': 'Date of Join for on-boarding employee on A.D. format.',
    '{{date_of_join_BS}}': 'Date of Join for on-boarding employee on B.S. format.',
    '{{company_name}}': 'Organization the on-boarding employee will be at.',
    '{{company_address}}': 'Address of organization the on-boarding employee will be at.',
}

OFFBOARDING_LETTER_PARAMS = {
    '{{name}}': 'Full name of the employee who is discontinuing with the '
                'company.',
    '{{nationality}}': 'Nationality of the employee who is discontinuing with '
                       'the company.',
    '{{change_type}}': 'The change type of user\'s current experience.',
    '{{effective_from}}': 'The effective date of user\'s current experience.',
    '{{job_title}}': 'Job title of the user\'s current experience.',
    '{{division}}': 'Division of the user\'s current experience.',
    '{{branch}}': 'Branch of the user\'s current experience',
    '{{company_name}}': 'Organization of the user\'s current experience',
    '{{company_address}}': 'Address of organization of the user\'s current experience',
    '{{employment_status}}': 'Employment status of the user\'s current '
                             'experience.',
    '{{employment_level}}': 'Employment Level of the user\'s current '
                            'experience.',
    '{{pan_number}}': 'PAN Number of the employee who is discontinuing with '
                      'the company.',
    '{{cit_number}}': 'CIT Number of the employee who is discontinuing with '
                      'the company.',
    '{{pf_number}}': 'PF Number of the employee who is discontinuing with the '
                     'company.',
    '{{citizenship_number}}': 'Citizenship Number of the employee who is '
                              'discontinuing with the company.',
    '{{passport_number}}': 'Passport Number of the employee who is '
                           'discontinuing with the company.',
    '{{separation_type}}': 'The separation type how the user parted the '
                           'company.',
    '{{resign_date}}': 'The date, employee informed the company about '
                           'leaving the company.',
    '{{last_working_date}}': 'The date, employee will be released from the company.',
    '{{approved_date}}': 'The date, HR accepted the resignation.',
    '{{dob}}': 'Date of birth of the employee who is discontinuing with the '
               'company.',
    '{{step}}': 'Step of the user\'s current experience.',
    '{{date_of_join_AD}}': 'Date, the employee joined the company on A.D. format.',
    '{{date_of_join_BS}}': 'Date, the employee joined the company on B.S. format.',
}

CUSTOM_LETTER_PARAMS = {
    '{{full_name}}': "Employee's full name.",
    '{{date_of_join_AD}}': "Employee's date of join (in A.D format).",
    '{{date_of_join_BS}}': "Employee's date of join (in B.S format).",
    '{{employment_level}}': "Employee's current employment level.",
    '{{employment_status}}': "Employee's current employment status.",
    '{{job_title}}': "Employee's current job title.",
    '{{step}}': "Employee's current experience step",
    '{{division}}': "Employee's current division name.",
    '{{company_name}}': "Employee's current company name.",
    '{{company_address}}': "Employee's current company address.",
    '{{branch}}': "Employee's current branch",
    '{{address}}': "Employee's current address",
    '{{gender}}': "Employee's gender",
    '{{nationality}}': "Employee's nationality",
    '{{change_type}}': "Employee's current experience change type.",
    '{{pan_number}}': "Employee's PAN number",
    '{{cit_number}}': "Employee's CIT number",
    '{{pf_number}}': "Employee's PF number",
    '{{citizenship_number}}': "Employee's citizenship number",
    '{{ssfid}}': "Employee's SSF ID.",
    '{{passport_number}}': "Employee's passport number",
    '{{dob}}': "Employee's date of birth.",
    '{{resign_date}}': 'The date, employee resigned from the company.',
    '{{last_working_date}}': 'The date, employee was released from the company.'
 }

SENT, NOT_SENT, FAILED, ACCEPTED, DECLINED, EXPIRED = (
    'sent',
    'not sent',
    'failed',
    'accepted',
    'declined',
    'expired'
)
SAVED, DOWNLOADED = 'saved', 'downloaded'
EMAIL_STATUS_CHOICES = (
    (SENT, 'Sent'),
    (NOT_SENT, 'Not Sent'),
    (FAILED, 'Failed'),
    (ACCEPTED, 'Accepted'),
    (DECLINED, 'Declined'),
    (EXPIRED, 'Expired'),
    (DOWNLOADED, 'Downloaded'),
    (SAVED, 'SAVED'),
)

ON_BOARDING_STARTED, ON_BOARDING_COMPLETED, LETTER_NOT_GENERATED = (
    'On Boarding Started',
    'On Boarding Completed',
    'Letter Not Generated'
)

(ACTIVE, HOLD, STOPPED, COMPLETED, PENDING, IN_PROGRESS) = (
    'active', 'hold', 'stopped', 'completed', 'pending', 'in-progress'
)
LETTERS_GENERATED = 'letters-generated'
PRE_TASK_ACTIVE, PRE_TASK_COMPLETED = 'pre-active', 'pre-completed'
POST_TASK_ACTIVE, POST_TASK_COMPLETED = 'post-active', 'post-completed'

BASE_STATUS = (
    (ACTIVE, 'Active'),
    (HOLD, 'Hold'),
    (STOPPED, 'Stopped'),
    (COMPLETED, 'Completed'),
    (LETTERS_GENERATED, 'Letters Generated'),
    (PRE_TASK_ACTIVE, 'Pre Task Active'),
    (PRE_TASK_COMPLETED, 'Pre Task Completed'),
    (POST_TASK_ACTIVE, 'Post Task Active'),
    (POST_TASK_COMPLETED, 'Post Task Completed'),
)

(EMPLOYEE_ADDED, SUPERVISOR_ADDED, EQUIPMENTS_ASSIGNED) = ('employee-added',
                                                           'supervisor-added',
                                                           'equipments-assigned'
                                                           )
ONBOARDING_STATUS = BASE_STATUS + (
    (EMPLOYEE_ADDED, 'Employee Added'),
    (SUPERVISOR_ADDED, 'Supervisor Added'),
    (EQUIPMENTS_ASSIGNED, 'Equipments Assigned'),
)

(
    LEAVE_REVIEWED, ATTENDANCE_REVIEWED, PENDING_TASKS_REVIEWED,
    PAYROLL_REVIEWED, EXIT_INTERVIEW_CREATED, EXIT_INTERVIEW_REVIEWED
) = (
    'leave-reviewed', 'attendance-reviewed', 'tasks-reviewed',
    'payroll-reviewed', 'exit-interview-created', 'exit-interview-reviewed'
)

OFFBOARDING_STATUS = BASE_STATUS + (
    (LEAVE_REVIEWED, 'Leave Reviewed'),
    (ATTENDANCE_REVIEWED, 'Attendance Reviewed'),
    (PENDING_TASKS_REVIEWED, 'Pending Tasks Reviewed'),
    (PAYROLL_REVIEWED, 'Payroll Reviewed'),
    (EXIT_INTERVIEW_CREATED, 'Exit Interview Created'),
    (EXIT_INTERVIEW_REVIEWED, 'Exit Interview Reviewed')
)

(
    EXPERIENCE_ADDED, PAYROLL_CHANGED, WORKSHIFT_CHANGED,
    LEAVE_UPDATED, CORE_TASKS_UPDATED
) = (
    'experience-added', 'payroll-changed', 'workshift-changed', 'leave-updated',
    'core-tasks-updated'
)

CHANGE_TYPE_STATUS = BASE_STATUS + (
    (EXPERIENCE_ADDED, 'Experience Added'),
    (PAYROLL_CHANGED, 'Payroll Changed'),
    (WORKSHIFT_CHANGED, 'Workshift Changed'),
    (LEAVE_UPDATED, 'Leave Updated'),
    (CORE_TASKS_UPDATED, 'Core Tasks Updated'),
)

# Onboarding sequence begins after offer letter is accepted.
# We will check offer letter status before proceeding here.
# Offer letter has statuses, SENT, EXPIRED, ACCEPTED, DECLINED, DOWNLOADED

ONBOARDING_SEQUENCE = (
    PRE_TASK_ACTIVE,
    PRE_TASK_COMPLETED,
    EMPLOYEE_ADDED,
    SUPERVISOR_ADDED,
    LETTERS_GENERATED,
    EQUIPMENTS_ASSIGNED,
    POST_TASK_ACTIVE,
    POST_TASK_COMPLETED
)

AWAITING_VERIFICATION = 'awaiting-verification'
CHANGE_TYPE_SEQUENCE = (
    ACTIVE, PRE_TASK_ACTIVE, PRE_TASK_COMPLETED,
    EXPERIENCE_ADDED, PAYROLL_CHANGED, WORKSHIFT_CHANGED, LEAVE_UPDATED,
    CORE_TASKS_UPDATED, LETTERS_GENERATED, POST_TASK_ACTIVE, POST_TASK_COMPLETED,
    AWAITING_VERIFICATION
)

OFFBOARDING_SEQUENCE = (
    PRE_TASK_ACTIVE, PRE_TASK_COMPLETED,
    LETTERS_GENERATED, LEAVE_REVIEWED, ATTENDANCE_REVIEWED,
    PENDING_TASKS_REVIEWED, PAYROLL_REVIEWED, EXIT_INTERVIEW_CREATED,
    EXIT_INTERVIEW_REVIEWED, POST_TASK_ACTIVE, POST_TASK_COMPLETED
)

NEITHER, BOTH, EMPLOYEE_DIRECTORY, EMPLOYEE_LIST = 'n', 'b', 'd', 'l'
BADGE_VISIBILITY_CHOICES = (
    (NEITHER, 'Hide from Directory and Employee List'),
    (BOTH, 'Show in Directory and Employee List'),
    (EMPLOYEE_DIRECTORY, 'Show in Directory Only'),
    (EMPLOYEE_LIST, 'Show in Employee List Only'),
)

OTHER = 'Other'
NEW = 'New'
UPCOMING = 'Upcoming'
SEPARATION_CATEGORY_CHOICES = PARTING_REASON_CHOICES + (
    (OTHER, 'Other'),
)

resignation_email_permissions = [
    HRIS_PERMISSION,
    HRIS_OFF_BOARDING_PERMISSION,
    HRIS_SEPARATION_TYPE_PERMISSION,
    RESIGNATION_PERMISSION,
    EXIT_INTERVIEW_PERMISSION,
]
