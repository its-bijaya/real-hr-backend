from irhrs.organization.api.v1.permissions import (
    CommonSettingsWritePermission, CommonSettingsPermission
)
from irhrs.permission.constants.permissions import (
    FORM_PERMISSION,
    FORM_READ_ONLY_PERMISSION,
    FORM_APPROVAL_SETTING_PERMISSION,
    FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS,
    FORM_CAN_VIEW_AND_ACT_ON_ANONYMOUS_FORMS,
    FORM_CAN_ASSIGN_UNASSIGN_USER_FORMS,
    FORM_CAN_VIEW_FORM_REPORT,
    FORM_QUESTION_AND_SETTING_VIEW_CREATE_UPDATE_DELETE_PERMISSION,
    HAS_PERMISSION_FROM_METHOD
)
from irhrs.permission.permission_classes import permission_factory

FormCRUDPermission = permission_factory.build_permission(
    'FormPermission',
    limit_write_to=[
        FORM_QUESTION_AND_SETTING_VIEW_CREATE_UPDATE_DELETE_PERMISSION
    ],
)

FormAnonymousPermission = permission_factory.build_permission(
    'FormAnonymousPermission',
    allowed_to=[
        HAS_PERMISSION_FROM_METHOD
    ],
)

FormSubmissionReadAndActPermission = permission_factory.build_permission(
    'FormSubmissionReadAndActPermission',
    limit_read_to=[
        FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS,
    ],
)

FormApprovalSettingPermission = permission_factory.build_permission(
    'FormApprovalSettingPermission',
    limit_write_to=[
        FORM_APPROVAL_SETTING_PERMISSION,
    ],
)

FormAssignUnassignPermission = permission_factory.build_permission(
    'FormAssignUnassignPermission ',
    limit_write_to=[
        FORM_CAN_ASSIGN_UNASSIGN_USER_FORMS
    ],
)

FormAnonymousReadAndActPermission = permission_factory.build_permission(
    'FormAnonymousReadAndActPermission',
    allowed_to=[
        FORM_CAN_VIEW_AND_ACT_ON_ANONYMOUS_FORMS
    ],
)

FormReportsPermission = permission_factory.build_permission(
    'FormReportsPermission',
    allowed_to=[
        FORM_CAN_VIEW_FORM_REPORT
    ],
)
