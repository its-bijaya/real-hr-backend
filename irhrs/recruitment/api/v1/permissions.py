from rest_framework.permissions import BasePermission

from irhrs.permission.constants.permissions import OVERALL_RECRUITMENT_PERMISSION, \
    EXTERNAL_USER_PERMISSION
from irhrs.permission.permission_classes import permission_factory

RecruitmentPermission = permission_factory.build_permission(
    'RecruitmentPermission',
    allowed_to=[OVERALL_RECRUITMENT_PERMISSION]
)

RecruitmentAuditUserPermission = permission_factory.build_permission(
    'RecruitmentAuditUserPermission',
    allowed_to=[EXTERNAL_USER_PERMISSION]
)


CountryPermission = permission_factory.build_permission(
    'CountryPermission',
    limit_write_to=[OVERALL_RECRUITMENT_PERMISSION]
)

CityPermission = permission_factory.build_permission(
    'CityPermission',
    limit_write_to=[OVERALL_RECRUITMENT_PERMISSION]
)

SkillPermission = permission_factory.build_permission(
    'SkillPermission',
    limit_write_to=[OVERALL_RECRUITMENT_PERMISSION]
)
