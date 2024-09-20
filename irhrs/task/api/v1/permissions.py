from irhrs.permission.constants.permissions import TASK_PERMISSION, \
    TASK_REPORT_PERMISSION, TASK_APPROVALS_PERMISSION, \
    TASK_RESULT_AREA_AND_CORE_TASK_PERMISSION, TASK_PROJECT_PERMISSION, \
    CORE_TASK_RELATED_PERMISSIONS, \
    ASSIGN_CORE_TASK_PERMISSION, TASK_SETTINGS_PERMISSION
from irhrs.permission.permission_classes import permission_factory

TaskViewSetPermission = permission_factory.build_permission(
    "TaskViewSetPermission",
    actions={
        "overview": [TASK_PERMISSION]
    }
)

TaskPermission = permission_factory.build_permission(
    "TaskPermission",
    allowed_to=[TASK_PERMISSION]
)

TaskProjectWritePermission = permission_factory.build_permission(
    "TaskProjectWritePermission",
    limit_write_to=[TASK_PERMISSION]
)

TaskReportPermission = permission_factory.build_permission(
    'TaskReportPermission',
    allowed_to=[TASK_PERMISSION, TASK_REPORT_PERMISSION]
)

TaskApprovalsPermission = permission_factory.build_permission(
    'TaskApprovalsPermission',
    allowed_to=[TASK_PERMISSION, TASK_APPROVALS_PERMISSION]
)

TaskResultAreaAndCoreTaskPermission = permission_factory.build_permission(
    'TaskResultAreaAndCoreTaskPermission',
    limit_write_to=[CORE_TASK_RELATED_PERMISSIONS, TASK_RESULT_AREA_AND_CORE_TASK_PERMISSION],
    limit_read_to=[
        CORE_TASK_RELATED_PERMISSIONS,
        ASSIGN_CORE_TASK_PERMISSION,
        TASK_RESULT_AREA_AND_CORE_TASK_PERMISSION
    ],
)

TaskProjectPermission = permission_factory.build_permission(
    'TaskProjectPermission',
    limit_write_to=[TASK_PERMISSION, TASK_PROJECT_PERMISSION]
)

TaskSettingsPermission = permission_factory.build_permission(
    "TaskSettingsPermission",
    allowed_to=[TASK_SETTINGS_PERMISSION]
)
