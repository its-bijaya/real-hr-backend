from irhrs.leave.constants.model_constants import (
    REQUESTED as L_REQUESTED, FORWARDED as L_FORWARDED, APPROVED as L_APPROVED,
    DENIED as L_DENIED
)

HRIS, NOTICEBOARD, ATTENDANCE, TASK = (
    "HRIS", "Noticeboard", "Attendance", "Task"
)
USER_ACTIVITY_CATEGORIES_CHOICES = (
    (TASK, "Task"),
    (HRIS, "HRIS"),
    (NOTICEBOARD, "Noticeboard"),
    (ATTENDANCE, "Attendance")
)

PUBLISHED, UNPUBLISHED = "Published", "Unpublished"
PUBLISH_UNPUBLISH_CHOICES = (
    (PUBLISHED, "Published"),
    (UNPUBLISHED, "Unpublished")
)

RELIGION, ETHNICITY = "Religion", "Ethnicity"
RELIGION_AND_ETHNICITY_CATEGORY = (
    ("Religion", "Religion"),
    ("Ethnicity", "Ethnicity")
)

# Assigning constants in Integer for ordering purposes
POOR, AVERAGE, GOOD, VERY_GOOD, EXCELLENT = 1, 2, 3, 4, 5
SCORE_CHOICES = (
    (POOR, "Poor"),
    (AVERAGE, "Average"),
    (GOOD, "Good"),
    (VERY_GOOD, "Very Good"),
    (EXCELLENT, "Excellent"),
)

WARNING, DANGER, INFO, SUCCESS = "Warning", "Danger", "Info", "Success"
NOTIFICATION_LABEL_CHOICES = (
    (WARNING, "Warning"),
    (DANGER, "Danger"),
    (INFO, "Info"),
    (SUCCESS, "Success")
)

(
    LEAVE_REQUEST_NOTIFICATION, LEAVE_CANCEL_REQUEST_NOTIFICATION, ADJUSTMENT_REQUEST_NOTIFICATION,
    OVERTIME_CLAIM_NOTIFICATION,
    TASK_APPROVAL_NOTIFICATION, TASK_ACKNOWLEDGE_NOTIFICATION, OVERTIME_PRE_APPROVAL,
    CREDIT_HOUR_PRE_APPROVAL, WEB_ATTENDANCE_APPROVAL, TIMESHEET_REPORT
) = (
    'leave_request', 'leave_cancel_request', 'adjustment_request', 'overtime_claim',
    'task_approval', 'task_acknowledge',
    'overtime_pre_approval', 'credit_hour_pre_approval', 'web_attendance', 'timesheet_report'
)
TRAVEL_ATTENDANCE_NOTIFICATION = 'travel_attendance'
TRAVEL_ATTENDANCE_DELETE_NOTIFICATION = 'travel_attendance_delete'
CREDIT_HOUR_PRE_APPROVAL_DELETE = 'credit_hour_pre_approval_delete'

INTERACTIVE_NOTIFICATION_CHOICES = (
    (LEAVE_REQUEST_NOTIFICATION, 'leave_request'),
    (LEAVE_CANCEL_REQUEST_NOTIFICATION, 'leave_cancel_request'),
    (ADJUSTMENT_REQUEST_NOTIFICATION, 'adjustment_request'),
    (OVERTIME_CLAIM_NOTIFICATION, 'overtime_claim'),
    (TASK_APPROVAL_NOTIFICATION, 'task_approval'),
    (TASK_ACKNOWLEDGE_NOTIFICATION, 'task_acknowledge'),
    (TRAVEL_ATTENDANCE_NOTIFICATION, 'travel_attendance'),
    (TRAVEL_ATTENDANCE_DELETE_NOTIFICATION, 'travel_attendance_delete'),
    (OVERTIME_PRE_APPROVAL, 'overtime_pre_approval'),
    (CREDIT_HOUR_PRE_APPROVAL, 'credit_hour_pre_approval'),
    (CREDIT_HOUR_PRE_APPROVAL_DELETE, 'credit_hour_pre_approval_delete'),
    (WEB_ATTENDANCE_APPROVAL, 'web_attendance'),
    (TIMESHEET_REPORT, 'timesheet_report')
)

EMPLOYEE, ORGANIZATION, BOTH, OTHER = "Employee", "Organization", "Both", "Other"
DOCUMENT_TYPE_ASSOCIATION_CHOICES = (
    (EMPLOYEE, "Employee"),
    (ORGANIZATION, "Organization"),
    (OTHER, "Other"),
    (BOTH, "Both")
)

FACEBOOK, GOOGLE, LINKEDIN, YAHOO, MICROSOFT, OTHER = "Facebook", "Google", \
                                                      "Linkedin", "Yahoo", \
                                                      "Microsoft", "Other"
LINK_OF = (
    (FACEBOOK, "Facebook"),
    (GOOGLE, "Google"),
    (YAHOO, "Yahoo"),
    (LINKEDIN, "Linkedin"),
    (MICROSOFT, "Microsoft"),  # Live, Hotmail, Outlook
    (OTHER, "Other")
)

NATIONALITY_CHOICES = (
    ("Afghan", "Afghan"),
    ("Albanian", "Albanian"),
    ("Algerian", "Algerian"),
    ("American", "American"),
    ("Andorran", "Andorran"),
    ("Angolan", "Angolan"),
    ("Antiguans", "Antiguans"),
    ("Argentinean", "Argentinean"),
    ("Armenian", "Armenian"),
    ("Australian", "Australian"),
    ("Austrian", "Austrian"),
    ("Azerbaijani", "Azerbaijani"),
    ("Bahamian", "Bahamian"),
    ("Bahraini", "Bahraini"),
    ("Bangladeshi", "Bangladeshi"),
    ("Barbadian", "Barbadian"),
    ("Barbudans", "Barbudans"),
    ("Batswana", "Batswana"),
    ("Belarusian", "Belarusian"),
    ("Belgian", "Belgian"),
    ("Belizean", "Belizean"),
    ("Beninese", "Beninese"),
    ("Bhutanese", "Bhutanese"),
    ("Bolivian", "Bolivian"),
    ("Bosnian", "Bosnian"),
    ("Brazilian", "Brazilian"),
    ("British", "British"),
    ("Bruneian", "Bruneian"),
    ("Bulgarian", "Bulgarian"),
    ("Burkinabe", "Burkinabe"),
    ("Burmese", "Burmese"),
    ("Burundian", "Burundian"),
    ("Cambodian", "Cambodian"),
    ("Cameroonian", "Cameroonian"),
    ("Canadian", "Canadian"),
    ("Cape Verdean", "Cape Verdean"),
    ("Central African", "Central African"),
    ("Chadian", "Chadian"),
    ("Chilean", "Chilean"),
    ("Chinese", "Chinese"),
    ("Colombian", "Colombian"),
    ("Comoran", "Comoran"),
    ("Congolese", "Congolese"),
    ("Costa Rican", "Costa Rican"),
    ("Croatian", "Croatian"),
    ("Cuban", "Cuban"),
    ("Cypriot", "Cypriot"),
    ("Czech", "Czech"),
    ("Danish", "Danish"),
    ("Djibouti", "Djibouti"),
    ("Dominican", "Dominican"),
    ("Dutch", "Dutch"),
    ("East Timorese", "East Timorese"),
    ("Ecuadorean", "Ecuadorean"),
    ("Egyptian", "Egyptian"),
    ("Emirian", "Emirian"),
    ("Equatorial Guinean", "Equatorial Guinean"),
    ("Eritrean", "Eritrean"),
    ("Estonian", "Estonian"),
    ("Ethiopian", "Ethiopian"),
    ("Fijian", "Fijian"),
    ("Filipino", "Filipino"),
    ("Finnish", "Finnish"),
    ("French", "French"),
    ("Gabonese", "Gabonese"),
    ("Gambian", "Gambian"),
    ("Georgian", "Georgian"),
    ("German", "German"),
    ("Ghanaian", "Ghanaian"),
    ("Greek", "Greek"),
    ("Grenadian", "Grenadian"),
    ("Guatemalan", "Guatemalan"),
    ("Guinea-Bissauan", "Guinea-Bissauan"),
    ("Guinean", "Guinean"),
    ("Guyanese", "Guyanese"),
    ("Haitian", "Haitian"),
    ("Herzegovinian", "Herzegovinian"),
    ("Honduran", "Honduran"),
    ("Hungarian", "Hungarian"),
    ("Icelander", "Icelander"),
    ("Indian", "Indian"),
    ("Indonesian", "Indonesian"),
    ("Iranian", "Iranian"),
    ("Iraqi", "Iraqi"),
    ("Irish", "Irish"),
    ("Israeli", "Israeli"),
    ("Italian", "Italian"),
    ("Ivorian", "Ivorian"),
    ("Jamaican", "Jamaican"),
    ("Japanese", "Japanese"),
    ("Jordanian", "Jordanian"),
    ("Kazakhstani", "Kazakhstani"),
    ("Kenyan", "Kenyan"),
    ("Kittian and Nevisian", "Kittian and Nevisian"),
    ("Kuwaiti", "Kuwaiti"),
    ("Kyrgyz", "Kyrgyz"),
    ("Laotian", "Laotian"),
    ("Latvian", "Latvian"),
    ("Lebanese", "Lebanese"),
    ("Liberian", "Liberian"),
    ("Libyan", "Libyan"),
    ("Liechtensteiner", "Liechtensteiner"),
    ("Lithuanian", "Lithuanian"),
    ("Luxembourger", "Luxembourger"),
    ("Macedonian", "Macedonian"),
    ("Malagasy", "Malagasy"),
    ("Malawian", "Malawian"),
    ("Malaysian", "Malaysian"),
    ("Maldivan", "Maldivan"),
    ("Malian", "Malian"),
    ("Maltese", "Maltese"),
    ("Marshallese", "Marshallese"),
    ("Mauritanian", "Mauritanian"),
    ("Mauritian", "Mauritian"),
    ("Mexican", "Mexican"),
    ("Micronesian", "Micronesian"),
    ("Moldovan", "Moldovan"),
    ("Monacan", "Monacan"),
    ("Mongolian", "Mongolian"),
    ("Moroccan", "Moroccan"),
    ("Mosotho", "Mosotho"),
    ("Motswana", "Motswana"),
    ("Mozambican", "Mozambican"),
    ("Namibian", "Namibian"),
    ("Nauruan", "Nauruan"),
    ("Nepali", "Nepali"),
    ("New Zealander", "New Zealander"),
    ("Ni-Vanuatu", "Ni-Vanuatu"),
    ("Nicaraguan", "Nicaraguan"),
    ("Nigerien", "Nigerien"),
    ("North Korean", "North Korean"),
    ("Northern Irish", "Northern Irish"),
    ("Norwegian", "Norwegian"),
    ("Omani", "Omani"),
    ("Pakistani", "Pakistani"),
    ("Palauan", "Palauan"),
    ("Panamanian", "Panamanian"),
    ("Papua New Guinean", "Papua New Guinean"),
    ("Paraguayan", "Paraguayan"),
    ("Peruvian", "Peruvian"),
    ("Polish", "Polish"),
    ("Portuguese", "Portuguese"),
    ("Qatari", "Qatari"),
    ("Romanian", "Romanian"),
    ("Russian", "Russian"),
    ("Rwandan", "Rwandan"),
    ("Saint Lucian", "Saint Lucian"),
    ("Salvadoran", "Salvadoran"),
    ("Samoan", "Samoan"),
    ("San Marinese", "San Marinese"),
    ("Sao Tomean", "Sao Tomean"),
    ("Saudi", "Saudi"),
    ("Scottish", "Scottish"),
    ("Senegalese", "Senegalese"),
    ("Serbian", "Serbian"),
    ("Seychellois", "Seychellois"),
    ("Sierra Leonean", "Sierra Leonean"),
    ("Singaporean", "Singaporean"),
    ("Slovakian", "Slovakian"),
    ("Slovenian", "Slovenian"),
    ("Solomon Islander", "Solomon Islander"),
    ("Somali", "Somali"),
    ("South African", "South African"),
    ("South Korean", "South Korean"),
    ("Spanish", "Spanish"),
    ("Sri Lankan", "Sri Lankan"),
    ("Sudanese", "Sudanese"),
    ("Surinamer", "Surinamer"),
    ("Swazi", "Swazi"),
    ("Swedish", "Swedish"),
    ("Swiss", "Swiss"),
    ("Syrian", "Syrian"),
    ("Taiwanese", "Taiwanese"),
    ("Tajik", "Tajik"),
    ("Tanzanian", "Tanzanian"),
    ("Thai", "Thai"),
    ("Togolese", "Togolese"),
    ("Tongan", "Tongan"),
    ("Trinidadian or Tobagonian", "Trinidadian or Tobagonian"),
    ("Tunisian", "Tunisian"),
    ("Turkish", "Turkish"),
    ("Tuvaluan", "Tuvaluan"),
    ("Ugandan", "Ugandan"),
    ("Ukrainian", "Ukrainian"),
    ("Uruguayan", "Uruguayan"),
    ("Uzbekistani", "Uzbekistani"),
    ("Venezuelan", "Venezuelan"),
    ("Vietnamese", "Vietnamese"),
    ("Welsh", "Welsh"),
    ("Yemenite", "Yemenite"),
    ("Zambian", "Zambian"),
    ("Zimbabwean", "Zimbabwean"),
)

MEDIA_DOCUMENT_AND_LINK_REQUIRED_MODELS = {
    'users': ['usermedicalinfo'],
    'common': [],
    'organization': ['organization', 'holiday'],
    'document': [],
    'notification': [],
    'noticeboard': [],
    'permission': [],
    'hrstatement': [],
}

# to separate permission categories from other names use P_ as prefix
(
    P_USER, P_ORGANIZATION, P_HRIS, P_NOTICEBOARD, P_ADMIN, P_ATTENDANCE,
    P_LEAVE, P_TASK, P_BUILDER, P_PAYROLL
) = (
    "User", "Organization", "HRIS", "Noticeboard", "Admin", "Attendance",
    "Leave", "Task", "Builder", 'Payroll'
)

P_ASSESSMENT = 'Assessment'  # 13
P_TRAINING = 'Training'  # 14
P_QUESTIONNAIRE = 'Questionnaire'  # 15
P_RECRUITMENT = 'Recruitment'  # 16
P_REIMBURSEMENT = 'Reimbursement'  # 17
P_EVENT = 'Event'  # 20
P_FORM = 'Form'  # 21
P_PERFORMANCE_APPRAISAL = 'Appraisal'  # 18

PERMISSION_CATEGORY_CHOICES = (
    (P_USER, "User"),
    (P_ORGANIZATION, "Organization"),
    (P_HRIS, "HRIS"),
    (P_NOTICEBOARD, "Noticeboard"),
    (P_ADMIN, "Admin"),
    (P_ATTENDANCE, "Attendance"),
    (P_LEAVE, "Leave"),
    (P_TASK, "Task"),
    (P_BUILDER, "Builder"),
    (P_PAYROLL, "Payroll"),
    (P_ASSESSMENT, 'Assessment'),
    (P_TRAINING, 'Training'),
    (P_QUESTIONNAIRE, 'Questionnaire'),
    (P_RECRUITMENT, 'Recruitment'),
    (P_REIMBURSEMENT, 'Reimbursement'),
    (P_EVENT, 'Event'),
    (P_PERFORMANCE_APPRAISAL, 'Performance Appraisal'),
    (P_FORM, 'Form')
)

MAX_CHRONIC_DISEASES = 5

MAX_LENGTH_SMS = 160

EMAIL = 'Email'
TEMPLATE_TYPE_CHOICES = (
    (EMAIL, 'Email'),
)

(
    LATE_IN_EMAIL, ABSENT_EMAIL, OVERTIME_EMAIL, LEAVE_EMAIL, WEEKLY_ATTENDANCE_REPORT_EMAIL
) = (
    'Late In Email', 'Absent Email', 'Overtime Email', 'Leave Email', 'Weekly Attendance Report Email'
)

NOTIFICATION_TYPE_CHOICES = (
    (LATE_IN_EMAIL, 'LateIn Email'),
    (ABSENT_EMAIL, 'Absent Email'),
    (OVERTIME_EMAIL, 'Overtime Email'),
    (LEAVE_EMAIL, 'Leave Email'),
    (WEEKLY_ATTENDANCE_REPORT_EMAIL, 'Weekly Attendance Report Email'),
)

DAYS, MONTHS, YEARS = ('d', 'm', 'y')
DURATION_CHOICES = (
    (DAYS, 'Days'),
    (MONTHS, 'Months'),
    (YEARS, 'Years')
)

LATE_IN_EMAIL_HINTS = {
    '{{user}}': 'Name of the employee',
    '{{date}}': 'Date the user came late',
    '{{expected_punch_in}}': 'Time, the user was expected to come.',
    '{{actual_punch_in}}': 'Time, the user came.',
    '{{late_duration}}': 'How many hours/minutes did the user loose?',
    '{{contact_info}}': 'Info email for the organization.',
}

ABSENT_EMAIL_HINTS = {
    '{{user}}': 'Name of the employee',
    '{{date}}': 'Date the user was marked absent.',
    '{{contact_info}}': 'Info email for the organization.',
}

WEEKLY_ATTENDANCE_REPORT_EMAIL_HINTS = {
    '{{user}}': 'Name of the employee.',
    '{{date}}': 'Date of sent mail.',
    '{{contact_info}}': 'Info email for the organization.',
    '{{average_in}}': 'Average in time of user.',
    '{{average_out}}': 'Average out time of user.',
    '{{punctuality}}': 'Punctuality of user.',
    '{{total_worked_hours}}': 'Total worked hours of user.',
    '{{total_working_hours}}': 'Total working hours of user.',
    '{{overtime}}':'Overtime done by user.',
    '{{detailed_weekly_attendance_table}}': 'Weekly table.'
}

OVERTIME_EMAIL_HINTS = {
    '{{user}}': 'Name of the employee',
    '{{date}}': 'Date of overtime generated.',
    '{{ot_hours}}': 'Hours of overtime calculated',
    '{{contact_info}}': 'Info email for the organization.',

}

LEAVE_EMAIL_HINTS = {
    '{{user}}': 'Name of the employee',
    '{{start_date}}': '2019-01-01 09:00 AM',
    '{{end_date}}': '2019-01-01 05:00 PM',
    '{{status}}': 'approved or declined',
    '{{contact_info}}': 'Info email for the organization.',
    '{{actor}}': 'Name of actor.',
    '{{recipient}}': 'Name of recipient.'
}

EMAIL_TEMPLATE_VALIDATION_MATCH = {
    LATE_IN_EMAIL: LATE_IN_EMAIL_HINTS,
    OVERTIME_EMAIL: OVERTIME_EMAIL_HINTS,
    LEAVE_EMAIL: LEAVE_EMAIL_HINTS,
    ABSENT_EMAIL: ABSENT_EMAIL_HINTS,
    WEEKLY_ATTENDANCE_REPORT_EMAIL: WEEKLY_ATTENDANCE_REPORT_EMAIL_HINTS,
}

DEFAULT = 'Default'

EMAIL_TYPE_STATUS = {
    LATE_IN_EMAIL: [DEFAULT],
    ABSENT_EMAIL: [DEFAULT],
    OVERTIME_EMAIL: [DEFAULT],
    LEAVE_EMAIL: [L_REQUESTED, L_FORWARDED, L_APPROVED, L_DENIED],
    WEEKLY_ATTENDANCE_REPORT_EMAIL: [DEFAULT],
}

SENT, FAILED = 'Sent', 'Failed'
NOTIFICATION_STATUS_CHOICES = (
    (SENT, 'Sent'),
    (FAILED, 'Failed')
)

FIXED = 'Fixed'
TANGIBLE = 'Tangible'
INTANGIBLE = 'Intangible'
CURRENT = 'Current'
FINANCIAL = 'Financial'

ORGANIZATION_ASSET_CHOICES = (
    (FIXED, FIXED),
    (TANGIBLE, TANGIBLE),
    (INTANGIBLE, INTANGIBLE),
    (CURRENT, CURRENT),
    (FINANCIAL, FINANCIAL)
)

KNOWLEDGE = 'knowledge'
SKILL = 'skill'
ABILITY = 'ability'
OTHER_ATTRIBUTES = 'other_attributes'
KSA_TYPE = (
    (KNOWLEDGE, 'Knowledge'),
    (SKILL, 'Skill'),
    (ABILITY, 'Ability'),
    (OTHER_ATTRIBUTES, 'Other Attributes')
)

TOP_MANAGEMENT = 'top_management'
MANAGEMENT = 'management'
OFFICER = 'officer'
ASSISTANT = 'assistant'
EMPLOYMENT_LEVEL_CHOICE = (
    (TOP_MANAGEMENT, 'Top Management'),
    (MANAGEMENT, 'Management'),
    (OFFICER, 'Officer'),
    (ASSISTANT, 'Assistant')
)
