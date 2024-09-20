from irhrs.core.constants.common import P_ATTENDANCE

ATTENDANCE_REPORTS_PERMISSION = {
    "name": "Can view Attendance Reports.",
    "code": "5.01",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_DEVICE_SETTINGS_PERMISSION = {
    "name": "Can update Attendance Devices",
    "code": "5.02",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_WORKING_SHIFT_PERMISSION = {
    "name": "Can create/update/delete Work Shifts.",
    "code": "5.03",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_OVERTIME_PERMISSION = {
    "name": "Can create overtime settings.",
    "code": "5.04",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_INDIVIDUAL_ATTENDANCE_SETTINGS_PERMISSION = {
    "name": "Can assign individual attendance settings.",
    "code": "5.05",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_ASSIGN_SHIFT_PERMISSION = {
    "name": "Can assign Work Shift to employees.",
    "code": "5.06",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_ASSIGN_OVERTIME_PERMISSION = {
    "name": "Can Assign Overtime to User.",
    "code": "5.07",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_IMPORT_PERMISSION = {
    "name": "Can Import Attendance",
    "code": "5.08",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_OFFLINE_PERMISSION = {
    "name": "Can perform Offline Attendance.",
    "code": "5.09",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_ADJUSTMENTS_REQUEST_PERMISSION = {
    "name": "Can act on adjustment requests.",
    "code": "5.10",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_OVERTIME_CLAIM_PERMISSION = {
    "name": "Can act on overtime claims.",
    "code": "5.11",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_TRAVEL_PERMISSION = {
    "name": "Can act on attendance travel requests.",
    "code": "5.12",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_TRAVEL_SETTING_PERMISSION = {
    "name": "Can modify attendance travel setting.",
    "code": "5.13",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_CREDIT_HOUR_PERMISSION = {
    "name": "Can modify attendance Credit Hour Setting.",
    "code": "5.14",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_CREDIT_HOUR_REQUEST_PERMISSION = {
    "name": "Can perform actions on Credit Hour Request.",
    "code": "5.15",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_TIMESHEET_REPORT_PERMISSION = {
    "name": "Can confirm/deny timesheet reports of users.",
    "code": "5.16",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_APPROVAL_PERMISSION = {
    "name": "Can approve/deny timesheet for a day.",
    "code": "5.17",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_BREAK_OUT_PENALTY_SETTING_PERMISSION = {
    "name": "Can modify settings related to break-out penalty mechanism.",
    "code": "5.18",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_BREAK_OUT_PENALTY_PERMISSION = {
    "name": "Can view break-out report of users.",
    "code": "5.19",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_TIMESHEET_REPORT_SETTING_PERMISSION = {
    "name": "Can modify timesheet report settings.",
    "code": "5.20",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_TIMESHEET_REPORT_VIEW_PERMISSION = {
    "name": "Can view time-sheet report of users.",
    "code": "5.21",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

ATTENDANCE_TIMESHEET_ROSTER_PERMISSION = {
    "name": "Can view time-sheet roster report of users.",
    "code": "5.22",
    "category": P_ATTENDANCE,
    "organization_specific": True,
    "description": ""
}

__all__ = (
    'ATTENDANCE_REPORTS_PERMISSION',
    'ATTENDANCE_DEVICE_SETTINGS_PERMISSION',
    'ATTENDANCE_WORKING_SHIFT_PERMISSION',
    'ATTENDANCE_OVERTIME_PERMISSION',
    'ATTENDANCE_INDIVIDUAL_ATTENDANCE_SETTINGS_PERMISSION',
    'ATTENDANCE_ASSIGN_SHIFT_PERMISSION',
    'ATTENDANCE_ASSIGN_OVERTIME_PERMISSION',
    'ATTENDANCE_IMPORT_PERMISSION',
    'ATTENDANCE_OFFLINE_PERMISSION',
    'ATTENDANCE_ADJUSTMENTS_REQUEST_PERMISSION',
    'ATTENDANCE_OVERTIME_CLAIM_PERMISSION',
    'ATTENDANCE_TRAVEL_PERMISSION',
    'ATTENDANCE_TRAVEL_SETTING_PERMISSION',
    'ATTENDANCE_CREDIT_HOUR_PERMISSION',
    'ATTENDANCE_CREDIT_HOUR_REQUEST_PERMISSION',
    'ATTENDANCE_TIMESHEET_REPORT_PERMISSION',
    'ATTENDANCE_APPROVAL_PERMISSION',
    'ATTENDANCE_BREAK_OUT_PENALTY_SETTING_PERMISSION',
    'ATTENDANCE_BREAK_OUT_PENALTY_PERMISSION',
    'ATTENDANCE_TIMESHEET_REPORT_SETTING_PERMISSION',
    'ATTENDANCE_TIMESHEET_REPORT_VIEW_PERMISSION',
    'ATTENDANCE_TIMESHEET_ROSTER_PERMISSION'
)
