from irhrs.permission.constants.permissions import REPORT_BUILDER_PERMISSION, LEAVE_REPORT_PERMISSION, LEAVE_PERMISSION
from irhrs.permission.permission_classes import permission_factory

ReportBuilderPermission = permission_factory.build_permission(
    "ReportBuilderPermission",
    allowed_to=[REPORT_BUILDER_PERMISSION]
)
AttendanceAndLeavePermission = permission_factory.build_permission(
    "ReportBuilderPermission",
    allowed_to=[
        REPORT_BUILDER_PERMISSION,
        LEAVE_REPORT_PERMISSION,
        LEAVE_PERMISSION
    ])
