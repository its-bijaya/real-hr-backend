from rest_framework.permissions import BasePermission

from irhrs.core.utils.common import validate_permissions
from irhrs.leave.constants.model_constants import REQUESTED, FORWARDED
from irhrs.permission.constants.permissions import LEAVE_PERMISSION, \
    HAS_OBJECT_PERMISSION, HAS_PERMISSION_FROM_METHOD, LEAVE_REPORT_PERMISSION, \
    LEAVE_BALANCE_PERMISSION, \
    MASTER_SETTINGS_PERMISSION, ASSIGN_LEAVE_PERMISSION, OFFLINE_LEAVE_PERMISSION, \
    LEAVE_REQUEST_PERMISSION
from irhrs.permission.permission_classes import permission_factory

LeavePermission = permission_factory.build_permission(
    "LeavePermission",
    allowed_to=[LEAVE_PERMISSION]
)

LeaveReadPermission = permission_factory.build_permission(
    "LeavePermission",
    limit_write_to=[LEAVE_PERMISSION, MASTER_SETTINGS_PERMISSION],
)

LeaveAccountPermission = permission_factory.build_permission(
    "LeaveAccountPermission",
    actions={
        'update_balance': [LEAVE_PERMISSION, LEAVE_BALANCE_PERMISSION]
    }
)

LeaveAccountHistoryPermission = permission_factory.build_permission(
    "LeaveAccountHistoryPermission",
    allowed_to=[LEAVE_PERMISSION, HAS_PERMISSION_FROM_METHOD,
                LEAVE_BALANCE_PERMISSION]
)

UserLeavePermission = permission_factory.build_permission(
    "LeaveAccountHistoryPermission",
    allowed_to=[LEAVE_PERMISSION, HAS_PERMISSION_FROM_METHOD]
)

UserLeaveReportPermission = permission_factory.build_permission(
    "LeaveAccountHistoryPermission",
    allowed_to=[LEAVE_PERMISSION, LEAVE_REPORT_PERMISSION,
                HAS_PERMISSION_FROM_METHOD]
)

LeaveReportPermission = permission_factory.build_permission(
    "LeaveAccountHistoryPermission",
    allowed_to=[LEAVE_PERMISSION, LEAVE_REPORT_PERMISSION,
                HAS_PERMISSION_FROM_METHOD]
)

AdminOnlyLeaveReportPermission = permission_factory.build_permission(
    "LeaveAccountHistoryPermission",
    allowed_to=[LEAVE_PERMISSION, LEAVE_REPORT_PERMISSION]
)

LeaveMasterSettingPermission = permission_factory.build_permission(
    "LeaveMasterSettingPermission",
    allowed_to=[LEAVE_PERMISSION, MASTER_SETTINGS_PERMISSION],
    limit_read_to=[
        LEAVE_PERMISSION, MASTER_SETTINGS_PERMISSION,
        ASSIGN_LEAVE_PERMISSION
    ],
)

LeaveAssignPermission = permission_factory.build_permission(
    "LeaveAssignPermission",
    allowed_to=[LEAVE_PERMISSION, ASSIGN_LEAVE_PERMISSION]
)

LeaveRequestPermission = permission_factory.build_permission(
    "LeaveRequestPermission",
    allowed_to=[LEAVE_PERMISSION, LEAVE_REQUEST_PERMISSION]
)

OfflineLeavePermission = permission_factory.build_permission(
    "OfflineLeavePermission",
    allowed_to=[LEAVE_PERMISSION, OFFLINE_LEAVE_PERMISSION]
)

LeaveRequestDeletePermission = permission_factory.build_permission(
    'LeaveRequestDeletePermission',
    actions={
        'get_status_history': [
            LEAVE_PERMISSION, HAS_OBJECT_PERMISSION,
            LEAVE_REQUEST_PERMISSION
        ]
    },
    allowed_user_fields=['leave_request.user']
)


class LeaveRequestDeleteObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        mode = request.query_params.get('as', 'user')
        if view.action == 'delete_leave_request':
            if mode == 'hr':
                return validate_permissions(
                    request.user.get_hrs_permissions(view.organization),
                    LEAVE_PERMISSION, LEAVE_REQUEST_PERMISSION
                )
            return request.user == obj.recipient
        return True
