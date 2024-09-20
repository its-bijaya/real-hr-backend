from rest_framework.permissions import BasePermission

from irhrs.core.utils.common import get_today
from irhrs.hris.api.v1.permissions import \
    ON_BOARDING_OFF_BOARDING_PROCESSES_GROUP
from irhrs.permission.constants.permissions import (
    ORGANIZATION_PERMISSION, HAS_PERMISSION_FROM_METHOD,
    ORGANIZATION_REPORT_PERMISSION, ORGANIZATION_DOCUMENTS_PERMISSION,
    ORGANIZATION_SETTINGS_PERMISSION,
    SYSTEM_EMAIL_LOG_PERMISSION,
    ORGANIZATION_SETTINGS_VIEW_PERMISSION,
    ALL_COMMON_SETTINGS_PERMISSION, REPORT_VIEWERS, USER_PROFILE_PERMISSION,
    ASSIGN_LEAVE_PERMISSION, LEAVE_PERMISSION, APPLICATION_SETTING_PERMISSION,
    MISSION_AND_VISION_PERMISSION, FISCAL_YEAR_PERMISSION, HOLIDAY_PERMISSION,
    ORGANIZATION_ETHICS_PERMISSION, OFFICE_EQUIPMENTS_PERMISSION, DIVISION_PERMISSION,
    EMPLOYMENT_TYPE_PERMISSION, JOB_TITLE_PERMISSION, BRANCH_PERMISSION,
    ORGANIZATION_BANK_PERMISSION, MEETING_ROOM_PERMISSION, EMPLOYMENT_LEVEL_PERMISSION,
    KNOWLEDGE_SKILL_ABILITY_PERMISSION, DUTY_STATION_PERMISSION,
    ORGANIZATION_EMAIL_SETTING_PERMISSION,
)
from irhrs.permission.permission_classes import permission_factory

OrganizationPermission = permission_factory.build_permission(
    "OrganizationPermission",
    allowed_to=[ORGANIZATION_PERMISSION],
)

OrganizationWritePermission = permission_factory.build_permission(
    "OrganizationWritePermission",
    limit_write_to=[ORGANIZATION_PERMISSION],
)

OrganizationDivisionPermission = permission_factory.build_permission(
    "OrganizationDivisionPermission",
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        DIVISION_PERMISSION
    ],
)

OrganizationBranchPermission = permission_factory.build_permission(
    "OrganizationBranchPermission",
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        BRANCH_PERMISSION,
        HAS_PERMISSION_FROM_METHOD
    ],
)

HolidayPermission = permission_factory.build_permission(
    "HolidayPermission",
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        HOLIDAY_PERMISSION
    ],
    actions={'download_sample': [ORGANIZATION_PERMISSION]}
)

# BEGIN Extended ORGANIZATION PERMISSION

OrganizationReportPermission = permission_factory.build_permission(
    "OrganizationReportPermission",
    allowed_to=[ORGANIZATION_PERMISSION, ORGANIZATION_REPORT_PERMISSION]
)

OrganizationDocumentPermission = permission_factory.build_permission(
    "OrganizationDocumentPermission",
    limit_write_to=[
        ORGANIZATION_PERMISSION, ORGANIZATION_DOCUMENTS_PERMISSION,
        HAS_PERMISSION_FROM_METHOD
    ]
)

OrganizationSettingsWritePermission = permission_factory.build_permission(
    "OrganizationSettingsPermission",
    allowed_to=[ORGANIZATION_PERMISSION, ORGANIZATION_SETTINGS_PERMISSION],
    limit_read_to=[
        ORGANIZATION_SETTINGS_VIEW_PERMISSION,
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        *ON_BOARDING_OFF_BOARDING_PROCESSES_GROUP,
        USER_PROFILE_PERMISSION
    ]
)

OrganizationSettingsWritePermissionWithReportReadAccess = permission_factory.build_permission(
    "OrganizationSettingsPermission",
    allowed_to=[ORGANIZATION_PERMISSION, ORGANIZATION_SETTINGS_PERMISSION],
    limit_read_to=[
        ORGANIZATION_SETTINGS_VIEW_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        *REPORT_VIEWERS,
        USER_PROFILE_PERMISSION,
        LEAVE_PERMISSION,
        ASSIGN_LEAVE_PERMISSION
    ]
)

OrganizationSettingsWriteOnlyPermission = permission_factory.build_permission(
    "OrganizationSettingsWriteOnlyPermission",
    limit_write_to=[ORGANIZATION_PERMISSION, ORGANIZATION_SETTINGS_PERMISSION],
)

OrganizationSettingsPermission = permission_factory.build_permission(
    "OrganizationSettingsPermission",
    allowed_to=[
        ORGANIZATION_SETTINGS_VIEW_PERMISSION, ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION, APPLICATION_SETTING_PERMISSION,
        MISSION_AND_VISION_PERMISSION, FISCAL_YEAR_PERMISSION, HOLIDAY_PERMISSION,
        ORGANIZATION_ETHICS_PERMISSION, OFFICE_EQUIPMENTS_PERMISSION, DIVISION_PERMISSION,
        EMPLOYMENT_TYPE_PERMISSION, JOB_TITLE_PERMISSION, BRANCH_PERMISSION,
        ORGANIZATION_BANK_PERMISSION, MEETING_ROOM_PERMISSION, EMPLOYMENT_LEVEL_PERMISSION
    ],
)

CommonSettingsPermission = permission_factory.build_permission(
    "OrganizationSettingsPermission",
    allowed_to=[ALL_COMMON_SETTINGS_PERMISSION,]
)

CommonSettingsWritePermission = permission_factory.build_permission(
    "OrganizationSettingsPermission",
    limit_write_to=[ALL_COMMON_SETTINGS_PERMISSION]
)

SystemEmailLogPermission = permission_factory.build_permission(
    "SystemEmailLogPermission",
    allowed_to=[ALL_COMMON_SETTINGS_PERMISSION, SYSTEM_EMAIL_LOG_PERMISSION]
)

# END Extended ORGANIZATION PERMISSION
OfficeEquipmentPermission = permission_factory.build_permission(
    'OrganizationEquipmentPermission',
    allowed_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        OFFICE_EQUIPMENTS_PERMISSION
    ],
    limit_read_to=[
        ORGANIZATION_SETTINGS_VIEW_PERMISSION,
        OFFICE_EQUIPMENTS_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        ORGANIZATION_PERMISSION
    ]
)

EquipmentAssignedToPermission = permission_factory.build_permission(
    'EquipmentAssignedToPermission',
    allowed_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        OFFICE_EQUIPMENTS_PERMISSION,
        HAS_PERMISSION_FROM_METHOD
    ],
    limit_read_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        OFFICE_EQUIPMENTS_PERMISSION,
        HAS_PERMISSION_FROM_METHOD,
        USER_PROFILE_PERMISSION
    ]
)

MeetingRoomPermission = permission_factory.build_permission(
    'MeetingRoomPermission',
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        MEETING_ROOM_PERMISSION,
    ],
)

ApplicationSettingPermission = permission_factory.build_permission(
    'ApplicationSettingPermission',
    allowed_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        APPLICATION_SETTING_PERMISSION
    ],
    limit_read_to=[
        ORGANIZATION_SETTINGS_VIEW_PERMISSION,
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        APPLICATION_SETTING_PERMISSION
    ]
)

OrganizationEmailNotificationSettingPermission = permission_factory.build_permission(
    'OrganizationEmailNotificationSettingPermission',
    allowed_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        ORGANIZATION_EMAIL_SETTING_PERMISSION
    ],
    limit_read_to=[
        ORGANIZATION_SETTINGS_VIEW_PERMISSION,
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        ORGANIZATION_EMAIL_SETTING_PERMISSION
    ]
)

MissionAndVisionPermission = permission_factory.build_permission(
    'MissionAndVisionPermission',
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        MISSION_AND_VISION_PERMISSION
    ]
)

FiscalYearPermission = permission_factory.build_permission(
    'FiscalYearPermission',
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        FISCAL_YEAR_PERMISSION
    ]
)

OrganizationEthicsPermission = permission_factory.build_permission(
    'OrganizationEthicsPermission',
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        ORGANIZATION_ETHICS_PERMISSION
    ]
)

EmploymentStatusPermission = permission_factory.build_permission(
    "EmploymentStatusPermission",
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        EMPLOYMENT_TYPE_PERMISSION
    ],
    # limit_read_to=[
    #     ORGANIZATION_SETTINGS_VIEW_PERMISSION,
    #     ORGANIZATION_SETTINGS_PERMISSION,
    #     EMPLOYMENT_TYPE_PERMISSION,
    #     *REPORT_VIEWERS,
    #     USER_PROFILE_PERMISSION,
    #     LEAVE_PERMISSION,
    #     ASSIGN_LEAVE_PERMISSION
    # ]
)

EmploymentLevelPermission = permission_factory.build_permission(
    "EmploymentLevelPermission",
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        EMPLOYMENT_LEVEL_PERMISSION
    ],
    # limit_read_to=[
    #     ORGANIZATION_SETTINGS_VIEW_PERMISSION,
    #     ORGANIZATION_SETTINGS_PERMISSION,
    #     EMPLOYMENT_LEVEL_PERMISSION,
    #     *REPORT_VIEWERS,
    #     USER_PROFILE_PERMISSION,
    #     LEAVE_PERMISSION,
    #     ASSIGN_LEAVE_PERMISSION
    # ]
)

EmploymentJobTitlePermission = permission_factory.build_permission(
    "EmploymentJobTitlePermission",
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        JOB_TITLE_PERMISSION
    ],
    # limit_read_to=[
    #     ORGANIZATION_SETTINGS_VIEW_PERMISSION,
    #     ORGANIZATION_SETTINGS_PERMISSION,
    #     ORGANIZATION_PERMISSION,
    #     JOB_TITLE_PERMISSION,
    #     *ON_BOARDING_OFF_BOARDING_PROCESSES_GROUP,
    #     USER_PROFILE_PERMISSION
    # ]
)

OrganizationBankPermission = permission_factory.build_permission(
    "OrganizationBankPermission",
    allowed_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        ORGANIZATION_BANK_PERMISSION
    ],
    limit_read_to=[
        ORGANIZATION_SETTINGS_VIEW_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        ORGANIZATION_PERMISSION,
        ORGANIZATION_BANK_PERMISSION
    ]
)


DutyStationPermission = permission_factory.build_permission(
    'DutyStationPermission',
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        DUTY_STATION_PERMISSION,
    ]
)

KnowledgeSkillAbilityPermission = permission_factory.build_permission(
    'KnowledgeSkillAbilityPermission',
    limit_write_to=[
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        KNOWLEDGE_SKILL_ABILITY_PERMISSION
    ]
)


class DisallowUpdateOfPastHoliday(BasePermission):
    def has_object_permission(self, request, view, obj):
        # either method is GET/DELETE or holiday is of future
        # if holiday does not have date attr, it is from create
        return (request.method.upper() in ['GET', 'DELETE']
                or not hasattr(obj, 'date')
                or obj.date > get_today())
