"""
HRS Permissions are kept here and they will be added to the
database during setup
"""
from .assessment_questionnaire_training import *
from .reimbursement import (
    EXPANSE_APPROVAL_SETTING_PERMISSION,
    ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION
)
from .common_permissions import (
    COMMON_BANK_PERMISSION,
    EMAIL_TEMPLATE_PERMISSION,
    EQUIPMENT_CATEGORY_PERMISSION,
    RELIGION_AND_ETHNICITY_PERMISSION,
    HOLIDAY_CATEGORY_PERMISSION,
    DOCUMENT_CATEGORY_PERMISSION,
    NOTICE_BOARD_SETTING_PERMISSION
)
from .task import (
    TASK_REPORT_PERMISSION,
    TASK_APPROVALS_PERMISSION,
    TASK_PROJECT_PERMISSION,
)
from irhrs.core.constants.common import (
    P_ADMIN, P_ORGANIZATION, P_USER, P_ATTENDANCE, P_HRIS, P_LEAVE,
    P_NOTICEBOARD, P_TASK, P_BUILDER, P_PAYROLL, P_FORM,
    P_RECRUITMENT, P_REIMBURSEMENT, P_EVENT)
from .attendance import *


AUTH_PERMISSION = {
    "name": "Can create/update/delete groups and permissions",
    "code": "1.00",
    "category": P_ADMIN,
    "organization_specific": False,
    "description": ""
}

ORGANIZATION_PERMISSION = {
    "name": "Has complete permission in Organization.",
    "code": "2.00",
    "category": P_ORGANIZATION,
    "organization_specific": True,
    "description": ""
}
ORGANIZATION_READ_ONLY_PERMISSION = {
    "name": "Has read-only permission in Organization.",
    "code": "2.99",
    "category": P_ORGANIZATION,
    "organization_specific": True,
    "description": ""
}

USER_PROFILE_PERMISSION = {
    "name": "Can create/update user profile",
    "code": "3.00",
    "category": P_USER,
    "organization_specific": True,
    "description": ""
}

USER_PROFILE_READ_ONLY_PERMISSION = {
    "name": "Has read-only permission in user profile",
    "code": "3.99",
    "category": P_USER,
    "organization_specific": True,
    "description": ""
}

HRIS_PERMISSION = {
    "name": "Has complete permission in HRIS.",
    "code": "4.00",
    "category": P_HRIS,
    "organization_specific": True,
    "description": ""
}

HRIS_READ_ONLY_PERMISSION = {
    "name": "Has read-only permission in HRIS.",
    "code": "4.99",
    "category": P_HRIS,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_PERMISSION = {
    "name": "Has permissions in attendance.",
    "code": "5.00",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_READ_ONLY_PERMISSION = {
    "name": "Has read-only in attendance.",
    "code": "5.99",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

LEAVE_PERMISSION = {
    "name": "Has permissions in leave",
    "code": "6.00",
    "organization_specific": True,
    "category": P_LEAVE
}

LEAVE_READ_ONLY_PERMISSION = {
    "name": "Has read-only permissions in leave",
    "code": "6.99",
    "organization_specific": True,
    "category": P_LEAVE
}

NOTICE_BOARD_PERMISSION = {
    "name": "Can update/delete any ones post comments",
    "code": "7.00",
    "organization_specific": False,
    "category": P_NOTICEBOARD
}

NOTICE_BOARD_READ_ONLY_PERMISSION = {
    "name": "Has read-only permission in Notice Board",
    "code": "7.99",
    "organization_specific": False,
    "category": P_NOTICEBOARD
}

TASK_PERMISSION = {
    "name": "Task related HR permissions",
    "code": "8.00",
    "organization_specific": False,
    "category": P_TASK
}

TASK_READ_ONLY_PERMISSION = {
    "name": "Task read-only HR permissions",
    "code": "8.99",
    "organization_specific": False,
    "category": P_TASK
}


REPORT_BUILDER_PERMISSION = {
    "name": "Report Build Permission",
    "code": "9.00",
    "organization_specific": False,
    "category": P_BUILDER
}


ALL_COMMON_SETTINGS_PERMISSION = {
    "name": "Has All Access to Common Organization Settings.",
    "code": "10.00",
    "organization_specific": False,
    "category": P_ORGANIZATION
}

COMMON_SETTINGS_READ_ONLY_PERMISSION = {
    "name": "Has read-only Access to Common Organization Settings.",
    "code": "10.99",
    "organization_specific": False,
    "category": P_ORGANIZATION
}

SYSTEM_EMAIL_LOG_PERMISSION = {
    "name": "Can view System Email Logs.",
    "code": "10.02",
    "organization_specific": False,
    "category": P_ORGANIZATION
}

COMMON_ID_CARD_PERMISSION = {
    "name": "Can Add/Edit/View ID Card Template and its settings.",
    "code": "10.03",
    "organization_specific": False,
    "category": P_HRIS
}

COMMON_CENTRAL_DASHBOARD_PERMISSION = {
    "name": "Has read-only permission in central dashboard.",
    "code": "10.12",
    "category": P_ORGANIZATION,
    "organization_specific": False,
}

COMMON_SMTP_PERMISSION = {
    "name": "Can Add/View/Reset SMTP server configuration.",
    "code": "10.11",
    "organization_specific": False,
    "category": P_ADMIN
}
# Payroll Permissions

ALL_PAYROLL_PERMISSIONS = {
    "name": "Has full access in Payroll.",
    "code": "11.00",
    "organization_specific": True,
    "category": P_PAYROLL
}

PAYROLL_READ_ONLY_PERMISSIONS = {
    "name": "Has read-only access in Payroll.",
    "code": "11.99",
    "organization_specific": True,
    "category": P_PAYROLL
}

PAYROLL_SETTINGS_PERMISSION = {
    "name": "Can Create/Update Payroll Settings.",
    "code": "11.01",
    "organization_specific": True,
    "category": P_PAYROLL
}

WRITE_PAYROLL_PACKAGE_HEADINGS_PERMISSION = {
    "name": "Can Add, Edit, Delete Payroll Packages",
    "code": "11.02",
    "organization_specific": True,
    "category": P_PAYROLL
}

WRITE_PAYROLL_HEADINGS_PERMISSION = {
    "name": "Can Add, Edit, Delete Payroll Headings",
    "code": "11.12",
    "organization_specific": True,
    "category": P_PAYROLL
}

ASSIGN_PAYROLL_PACKAGES_PERMISSION = {
    "name": "Can Assign Payroll Packages or Headings",
    "code": "11.03",
    "organization_specific": True,
    "category": P_PAYROLL
}

GENERATE_PAYROLL_PERMISSION = {
    "name": "Can Generate Payroll",
    "code": "11.04",
    "organization_specific": True,
    "category": P_PAYROLL
}

PAYROLL_REBATE_PERMISSION = {
    "name": "Can Assign Rebate in Payroll.",
    "code": "11.05",
    "organization_specific": True,
    "category": P_PAYROLL
}

PAYROLL_REPORT_PERMISSION = {
    "name": "Can View Payroll Reports.",
    "code": "11.06",
    "organization_specific": True,
    "category": P_PAYROLL
}

PAYROLL_HOLD_PERMISSION = {
    "name": "Can Hold Generated Payroll.",
    "code": "11.07",
    "organization_specific": True,
    "category": P_PAYROLL
}

ADVANCE_SALARY_SETTING_PERMISSION = {
    "name": "Can access all setting of advance salary.",
    "code": "11.08",
    "organization_specific": True,
    "category": P_PAYROLL
}

ADVANCE_SALARY_GENERATE_PERMISSION = {
    "name": "Can view/generate advance salary.",
    "code": "11.09",
    "organization_specific": True,
    "category": P_PAYROLL
}

UNIT_OF_WORK_SETTINGS_PERMISSION = {
    "name": "Can change unit of work settings (operation/rate)",
    "code": "11.10",
    "organization_specific": True,
    "category": P_PAYROLL
}

UNIT_OF_WORK_REQUEST_PERMISSION = {
    "name": "Can accept/deny/confirm unit of work requests",
    "code": "11.11",
    "organization_specific": True,
    "category": P_PAYROLL
}

CAN_CREATE_PAYSLIP_REPORT_SETTING_PERMISSION = {
    "name": "Can create/update payslip report setting permission",
    "code": "11.13",
    "organization_specific": True,
    "category": P_PAYROLL
}

DELETE_CONFIRMED_EMPLOYEE_PAYROLL_PERMISSION = {
    "name": "Can delete confirmed payroll of employee",
    "code": "11.14",
    "organization_specific": True,
    "category": P_PAYROLL
}

# END Payroll Permissions

HRIS_REPORTS_PERMISSION = {
    "name": "Can view HRIS Reports.",
    "code": "4.01",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_ID_CARD_PERMISSION = {
    "name": "Can Add/Edit/View ID Card and its settings.",
    "code": "4.02",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_CONTRACT_SETTINGS_PERMISSION = {
    "name": "Can Add/View/Edit HRIS Contract related settings.",
    "code": "4.03",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_TASK_TEMPLATES_PERMISSION = {
    "name": "Can Add/View/Edit Task Templates regarding "
            "On-Boarding/Off-Boarding/Employment Review.",
    "code": "4.04",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_LETTER_TEMPLATE_PERMISSION = {
    "name": "Can Add/View/Edit Letter Templates regarding "
            "On-Boarding/Off-Boarding/Employment Review.",
    "code": "4.05",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_SEPARATION_TYPE_PERMISSION = {
    "name": "Can Add/View/Edit Separation Type.",
    "code": "4.06",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_EMPLOYMENT_REVIEW_PERMISSION = {
    "name": "Can Add/View/Edit Employment Review.",
    "code": "4.07",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_CHANGE_REQUEST_PERMISSION = {
    "name": "Can Approve/Deny Change Requests.",
    "code": "4.08",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_IMPORT_EMPLOYEE_PERMISSION = {
    "name": "Can Import Employees.",
    "code": "4.09",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_ON_BOARDING_PERMISSION = {
    "name": "Can On Board Employee.",
    "code": "4.10",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_EMPLOYMENT_REVIEW_PROCESS_PERMISSION = {
    "name": "Can Create Employment Reviews (promotion/demotion)",
    "code": "4.11",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_OFF_BOARDING_PERMISSION = {
    "name": "Can Off board employees.",
    "code": "4.12",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_ASSIGN_SUPERVISOR_PERMISSION = {
    "name": "Can assign supervisor",
    "code": "4.13",
    "organization_specific": True,
    "category": P_HRIS
}

HRIS_ASSIGN_KSAO_PERMISSION = {
    "name": "Can assign KSAO.",
    "code": "4.14",
    "organization_specific": True,
    "category": P_HRIS
}

EXIT_INTERVIEW_PERMISSION = {
    "name": "Can perform all action for Exit Interview.",
    "code": "4.15",
    "organization_specific": True,
    "category": P_HRIS,
}

RESIGNATION_PERMISSION = {
    "name": "Can perform all action for Resignation.",
    "code": "4.16",
    "organization_specific": True,
    "category": P_HRIS
}

EMAIL_SETTING_PERMISSION = {
    "name": "Can add email setting for user in hris setting.",
    "code": "4.17",
    "organization_specific": True,
    "category": P_HRIS
}

ASSIGN_UNASSIGN_DUTY_STATION_PERMISSION = {
    "name": "Can Assign/Unassign duty stations.",
    "code": "4.18",
    "organization_specific": True,
    "category": P_HRIS
}

PROFILE_COMPLETENESS_REPORT_PERMISSION = {
    "name": "Can view profile completeness report.",
    "code": "4.19",
    "organization_specific": True,
    "category": P_HRIS
}

USER_EXPERIENCE_IMPORT_PERMISSION = {
    "name": "Can import user experiences in bulk.",
    "code": "4.20",
    "organization_specific": True,
    "category": P_HRIS
}
USER_CONTACT_DETAIL_IMPORT_PERMISSION = {
    "name": "Can import user contact detail in bulk.",
    "code": "4.21",
    "organization_specific": True,
    "category": P_HRIS
}

USER_BANK_INFORMATION_IMPORT_PERMISSION = {
    "name": "Can import user bank information in bulk.",
    "code": "4.23",
    "organization_specific": True,
    "category": P_HRIS
}

USER_LEGAL_INFO_IMPORT_PERMISSION = {
    "name": "Can import user legal information in bulk.",
    "code": "4.22",
    "organization_specific": True,
    "category": P_HRIS
}

# organization specific permissions
# permission starts here
ORGANIZATION_REPORT_PERMISSION = {

    "name": "Can view Organization Reports.",
    "code": "2.03",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

ORGANIZATION_SETTINGS_PERMISSION = {
    "name": "Can create/read/update Organization Settings.",
    "code": "2.01",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

ORGANIZATION_SETTINGS_VIEW_PERMISSION = {
    "name": "Can view Organization Settings.",
    "code": "2.02",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

ORGANIZATION_DOCUMENTS_PERMISSION = {
    "name": "Can add Organization Documents.",
    "code": "2.04",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

APPLICATION_SETTING_PERMISSION = {
    "name": "Can view/update application Settings.",
    "code": "2.05",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

MISSION_AND_VISION_PERMISSION = {
    "name": "Can update/create mission and vision for organization.",
    "code": "2.06",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

FISCAL_YEAR_PERMISSION = {
    "name": "Can create/update/view fiscal year for organization.",
    "code": "2.07",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

HOLIDAY_PERMISSION = {
    "name": "Can create/update holidays.",
    "code": "2.08",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

ORGANIZATION_ETHICS_PERMISSION = {
    "name": "Can create/update Organization ethics.",
    "code": "2.09",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

OFFICE_EQUIPMENTS_PERMISSION = {
    "name": "Can create/update/view/delete office equipments.",
    "code": "2.10",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

DIVISION_PERMISSION = {
    "name": "Can create/update/delete division.",
    "code": "2.11",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

EMPLOYMENT_TYPE_PERMISSION = {
    "name": "Can create/update/view/delete employment type.",
    "code": "2.12",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

JOB_TITLE_PERMISSION = {
    "name": "Can create/update/view/delete job title.",
    "code": "2.13",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

BRANCH_PERMISSION = {
    "name": "Can create/update/view/delete branch.",
    "code": "2.14",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

ORGANIZATION_BANK_PERMISSION = {
    "name": "Can create/update/view/delete bank detail for organization.",
    "code": "2.15",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

ORGANIZATION_TEMPLATE_PERMISSION = {
    "name": "Can set template for organization.",
    "code": "2.16",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

MEETING_ROOM_PERMISSION = {
    "name": "Can create/update/delete meeting room.",
    "code": "2.17",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

EMPLOYMENT_LEVEL_PERMISSION = {
    "name": "Can create/update/view/delete employment level.",
    "code": "2.18",
    "organization_specific": True,
    "category": P_ORGANIZATION
}

KNOWLEDGE_SKILL_ABILITY_PERMISSION = {
    "name": "Can create/update/view/delete Knowledge, Skill, Ability and Other Attributes.",
    "code": "2.19",
    "organization_specific": True,
    "category": P_ORGANIZATION}

DUTY_STATION_PERMISSION = {
    "name": "Can create/update/view/delete Duty station category.",
    "code": "2.20",
    "organization_specific": False,
    "category": P_HRIS
}

ORGANIZATION_EMAIL_SETTING_PERMISSION = {
    "name": "Can change email notification settings for organization.",
    "code": "2.21",
    "organization_specific": True,
    "category": P_ORGANIZATION
}
# permission ends here

LEAVE_REPORT_PERMISSION = {
    "name": "Can view Leave Reports.",
    "code": "6.01",
    "organization_specific": True,
    "category": P_LEAVE
}

MASTER_SETTINGS_PERMISSION = {
    "name": "Can add/edit/update Master Settings.",
    "code": "6.02",
    "organization_specific": True,
    "category": P_LEAVE
}

ASSIGN_LEAVE_PERMISSION = {
    "name": "Can assign leave to users.",
    "code": "6.03",
    "organization_specific": True,
    "category": P_LEAVE
}

OFFLINE_LEAVE_PERMISSION = {
    "name": "Can grant offline leave.",
    "code": "6.04",
    "organization_specific": True,
    "category": P_LEAVE
}

LEAVE_BALANCE_PERMISSION = {
    "name": "Can view/edit leave balance for users.",
    "code": "6.05",
    "organization_specific": True,
    "category": P_LEAVE
}

LEAVE_REQUEST_PERMISSION = {
    "name": "Can View/Approve/Deny Leave Requests.",
    "code": "6.06",
    "organization_specific": True,
    "category": P_LEAVE
}

CORE_TASK_RELATED_PERMISSIONS = {
    "name": "Can perform operations regarding result area and core task",
    "code": "12.00",
    "category": P_TASK,
    "organization_specific": True,
}

CORE_TASK_READ_ONLY_PERMISSIONS = {
    "name": "Can view result area and core task",
    "code": "12.99",
    "category": P_TASK,
    "organization_specific": True,
}


TASK_RESULT_AREA_AND_CORE_TASK_PERMISSION = {
    "name": "Can create/update/list/delete result area and core task",
    "code": "12.01",
    "category": P_TASK,
    "organization_specific": True,
}

ASSIGN_CORE_TASK_PERMISSION = {
    "name": "Can assign result area and core task",
    "code": "12.02",
    "category": P_TASK,
    "organization_specific": True,
}

# task setting of organization
TASK_SETTINGS_PERMISSION = {
    "name": "Can view modify task settings.",
    "code": "12.03",
    "category": P_TASK,
    "organization_specific": True
}


OVERALL_RECRUITMENT_PERMISSION = {
    "name": "Can perform overall recruitment permission",
    "code": "16.00",
    "category": P_RECRUITMENT,
    "organization_specific": True,
}

RECRUITMENT_READ_ONLY_PERMISSION = {
    "name": "Has read-only permission in Recruitment.",
    "code": "16.99",
    "category": P_RECRUITMENT,
    "organization_specific": True,
}

EXTERNAL_USER_PERMISSION = {
    "name": "Can perform recruitment action as verifier",
    "code": "19.00",
    "category": P_RECRUITMENT,
    "organization_specific": True,
}

# Reimbursement Permission

OVERALL_REIMBURSEMENT_PERMISSION = {
    "name": "Can perform overall reimbursement permission",
    "code": "17.00",
    "category": P_REIMBURSEMENT,
    "organization_specific": True,
}

REIMBURSEMENT_READ_ONLY_PERMISSION = {
    "name": "Has read-only permission in reimbursement.",
    "code": "17.99",
    "category": P_REIMBURSEMENT,
    "organization_specific": True,
}

EVENT_PERMISSION = {
    "name": "Can perform overall event permission.",
    "code": "20.00",
    "category": P_EVENT,
    "organization_specific": True,
}

# Forms
FORM_PERMISSION = {
    "name": "Can perform all event on forms.",
    "code": "21.00",
    "organization_specific": True,
    "category": P_FORM
}

FORM_QUESTION_AND_SETTING_VIEW_CREATE_UPDATE_DELETE_PERMISSION = {
    "name": "Can perform create, read, update, delete on form question and settings.",
    "code": "21.01",
    "organization_specific": True,
    "category": P_FORM
}


FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS = {
    "name": "Can view user form submissions.",
    "code": "21.02",
    "organization_specific": True,
    "category": P_FORM
}

FORM_CAN_VIEW_AND_ACT_ON_ANONYMOUS_FORMS = {
    "name": "Can view and act on anonymous form submissions.",
    "code": "21.03",
    "organization_specific": True,
    "category": P_FORM
}

FORM_APPROVAL_SETTING_PERMISSION = {
    "name": "Can perform all actions on form approval settings.",
    "code": "21.04",
    "organization_specific": True,
    "category": P_FORM
}

FORM_CAN_ASSIGN_UNASSIGN_USER_FORMS = {
    "name": "Can assign and unassign user form submissions.",
    "code": "21.05",
    "organization_specific": True,
    "category": P_FORM
}

FORM_CAN_VIEW_FORM_REPORT = {
    "name": "Can view form report.",
    "code": "21.06",
    "organization_specific": True,
    "category": P_FORM
}

FORM_READ_ONLY_PERMISSION = {
    "name": "Has read only permission in forms.",
    "code": "21.99",
    "organization_specific": True,
    "category": P_FORM
}

# The common filters should be allowed to all report viewers,
# GRANT read to REPORT_VIEWERS in (DIVISION, BRANCH, EMPLOYMENT_STATUS, etc.)
REPORT_VIEWERS = (
    ORGANIZATION_PERMISSION, ORGANIZATION_REPORT_PERMISSION,
    HRIS_PERMISSION, HRIS_REPORTS_PERMISSION,
    ATTENDANCE_PERMISSION, ATTENDANCE_REPORTS_PERMISSION,
    LEAVE_PERMISSION, LEAVE_REPORT_PERMISSION,
    TASK_PERMISSION, TASK_REPORT_PERMISSION,
    ALL_PAYROLL_PERMISSIONS, PAYROLL_REPORT_PERMISSION
)

from .assessment_questionnaire_training import *
from .performance_appraisal import *
