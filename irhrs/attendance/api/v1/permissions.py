from rest_framework.permissions import BasePermission

from irhrs.permission.constants.permissions import (
    HAS_PERMISSION_FROM_METHOD,
    ATTENDANCE_PERMISSION,
    ATTENDANCE_OVERTIME_PERMISSION,
    ATTENDANCE_INDIVIDUAL_ATTENDANCE_SETTINGS_PERMISSION,
    ATTENDANCE_OFFLINE_PERMISSION,
    ATTENDANCE_DEVICE_SETTINGS_PERMISSION,
    ATTENDANCE_REPORTS_PERMISSION,
    ATTENDANCE_WORKING_SHIFT_PERMISSION,
    ATTENDANCE_ASSIGN_SHIFT_PERMISSION,
    ATTENDANCE_ASSIGN_OVERTIME_PERMISSION,
    ATTENDANCE_OVERTIME_CLAIM_PERMISSION, USER_PROFILE_PERMISSION, HAS_OBJECT_PERMISSION)
from irhrs.permission.constants.permissions.attendance import ATTENDANCE_APPROVAL_PERMISSION, \
    ATTENDANCE_TIMESHEET_REPORT_VIEW_PERMISSION
from irhrs.permission.permission_classes import permission_factory

AttendanceAdjustmentPermission = permission_factory.build_permission(
    "AttendanceAdjustmentPermission",
    limit_write_to=[
        HAS_PERMISSION_FROM_METHOD
    ]
)

AttendancePermission = permission_factory.build_permission(
    "AttendancePermission",
    allowed_to=[ATTENDANCE_PERMISSION]
)

AttendanceOvertimeSettingPermission = permission_factory.build_permission(
    "AttendanceOvertimeSettingPermission",
    allowed_to=[
        ATTENDANCE_PERMISSION,
        ATTENDANCE_OVERTIME_PERMISSION,
    ],
    limit_read_to=[
        ATTENDANCE_ASSIGN_OVERTIME_PERMISSION,
        ATTENDANCE_OVERTIME_PERMISSION,
        ATTENDANCE_PERMISSION,
        ATTENDANCE_INDIVIDUAL_ATTENDANCE_SETTINGS_PERMISSION
    ],
)

AttendanceWriteRestrictPermission = permission_factory.build_permission(
    "AttendancePermission",
    limit_write_to=[ATTENDANCE_PERMISSION]
)

AttendanceReportPermission = permission_factory.build_permission(
    "AttendanceReportPermission",
    allowed_to=[ATTENDANCE_PERMISSION, ATTENDANCE_REPORTS_PERMISSION,
                HAS_PERMISSION_FROM_METHOD],
    limit_read_to=[ATTENDANCE_PERMISSION, ATTENDANCE_REPORTS_PERMISSION,
                   HAS_PERMISSION_FROM_METHOD, USER_PROFILE_PERMISSION],
)

TimeSheetReportPermission = permission_factory.build_permission(
    "AttendanceTimeSheetReportPermission",
    allowed_to=[
        ATTENDANCE_PERMISSION, ATTENDANCE_REPORTS_PERMISSION,
        ATTENDANCE_TIMESHEET_REPORT_VIEW_PERMISSION
    ],
)

OvertimeClaimPermission = permission_factory.build_permission(
    "AttendanceReportPermission",
    limit_write_to=[
        ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION, HAS_PERMISSION_FROM_METHOD
    ]
)
UserActiveShiftPermission = AttendanceReportPermission

AttendanceSourcePermission = permission_factory.build_permission(
    "AttendanceSourcePermission",
    limit_write_to=[
        ATTENDANCE_DEVICE_SETTINGS_PERMISSION
    ],
    limit_read_to=[
        ATTENDANCE_DEVICE_SETTINGS_PERMISSION,
        ATTENDANCE_INDIVIDUAL_ATTENDANCE_SETTINGS_PERMISSION
    ]
)

AttendanceWorkShiftPermission = permission_factory.build_permission(
    "AttendanceWorkShiftPermission",
    limit_write_to=[ATTENDANCE_PERMISSION, ATTENDANCE_WORKING_SHIFT_PERMISSION]
)

AssignWorkShiftPermission = permission_factory.build_permission(
    "AssignWorkShiftPermission",
    limit_write_to=[
        ATTENDANCE_PERMISSION,
        ATTENDANCE_ASSIGN_SHIFT_PERMISSION
    ]
)

IndividualAttendanceSettingPermission = permission_factory.build_permission(
    "IndividualAttendanceSettingPermission",
    allowed_to=[ATTENDANCE_PERMISSION,
                ATTENDANCE_INDIVIDUAL_ATTENDANCE_SETTINGS_PERMISSION],
    limit_read_to=[
        ATTENDANCE_PERMISSION,
        ATTENDANCE_INDIVIDUAL_ATTENDANCE_SETTINGS_PERMISSION,
        ATTENDANCE_ASSIGN_SHIFT_PERMISSION,
        ATTENDANCE_OFFLINE_PERMISSION,
        ATTENDANCE_ASSIGN_OVERTIME_PERMISSION
    ],

)

OfflineAttendancePermission = permission_factory.build_permission(
    "OfflineAttendancePermission",
    allowed_to=[ATTENDANCE_PERMISSION,
                ATTENDANCE_OFFLINE_PERMISSION]
)

TimeSheetEntryApprovalPermission = permission_factory.build_permission(
            'TimeSheetEntryApprovalPermission',
            actions={
                'list': [HAS_PERMISSION_FROM_METHOD],
                'request_action': [HAS_PERMISSION_FROM_METHOD]
            }
        )
