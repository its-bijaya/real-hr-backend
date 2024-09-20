from irhrs.organization.api.v1.permissions import (
    CommonSettingsWritePermission, CommonSettingsPermission
)
from irhrs.permission.constants.permissions import (
    HRIS_PERMISSION, HAS_PERMISSION_FROM_METHOD,
    ASSIGN_UNASSIGN_DUTY_STATION_PERMISSION,
    ALL_COMMON_SETTINGS_PERMISSION,
    COMMON_BANK_PERMISSION,
    HOLIDAY_CATEGORY_PERMISSION,
    RELIGION_AND_ETHNICITY_PERMISSION,
    DOCUMENT_CATEGORY_PERMISSION,
    EQUIPMENT_CATEGORY_PERMISSION,
    NOTICE_BOARD_SETTING_PERMISSION, COMMON_SMTP_PERMISSION,
    COMMON_CENTRAL_DASHBOARD_PERMISSION, DUTY_STATION_PERMISSION)
from irhrs.permission.permission_classes import permission_factory


class CommonPermissionMixin:
    permission_classes = [CommonSettingsPermission]


class CommonWritePermissionMixin:
    permission_classes = [CommonSettingsWritePermission]


CommonBankPermission = permission_factory.build_permission(
    'CommonBankPermission',
    limit_write_to=[
        ALL_COMMON_SETTINGS_PERMISSION,
        COMMON_BANK_PERMISSION
    ]
)

CommonHolidayCategoryPermission = permission_factory.build_permission(
    'CommonHolidayCategoryPermission',
    limit_write_to=[
        ALL_COMMON_SETTINGS_PERMISSION,
        HOLIDAY_CATEGORY_PERMISSION
    ]
)

CommonReligionEthnicityPermission = permission_factory.build_permission(
    'CommonReligionEthnicityPermission',
    limit_write_to=[
        ALL_COMMON_SETTINGS_PERMISSION,
        RELIGION_AND_ETHNICITY_PERMISSION
    ]
)

CommonEquipmentCategoryPermission = permission_factory.build_permission(
    'CommonEquipmentCategoryPermission',
    limit_write_to=[
        ALL_COMMON_SETTINGS_PERMISSION,
        EQUIPMENT_CATEGORY_PERMISSION
    ]
)

CommonDocumentCategoryPermission = permission_factory.build_permission(
    'CommonDocumentCategoryPermission',
    limit_write_to=[
        ALL_COMMON_SETTINGS_PERMISSION,
        DOCUMENT_CATEGORY_PERMISSION
    ]
)

CommonNoticeBoardSettingPermission = permission_factory.build_permission(
    'CommonNoticeBoardSettingPermission',
    allowed_to=[
        ALL_COMMON_SETTINGS_PERMISSION,
        NOTICE_BOARD_SETTING_PERMISSION
    ]
)

CommonExchangeRatePermission = permission_factory.build_permission(
    "commonExchangeRatePermission",
    limit_write_to=[
        ALL_COMMON_SETTINGS_PERMISSION
    ]
)


CommonSMTPServerPermission = permission_factory.build_permission(
    'CommonSMTPServerPermission',
    allowed_to=[COMMON_SMTP_PERMISSION]
)


CentralDashboardPermission = permission_factory.build_permission(
    'CentralDashboardPermission',
    limit_read_to=[
        COMMON_CENTRAL_DASHBOARD_PERMISSION
    ]
)

DutyStationPermission = permission_factory.build_permission(
    'DutyStationPermission',
    limit_write_to=[
        DUTY_STATION_PERMISSION,
    ]
)

