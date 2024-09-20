from rest_framework.permissions import BasePermission

from irhrs.core.utils.common import validate_permissions
from irhrs.permission.constants.permissions import (
    PERFORMANCE_APPRAISAL_PERMISSION, PERFORMANCE_APPRAISAL_SETTING_PERMISSION,
    PERFORMANCE_APPRAISAL_FORM_SUBMISSION_ACTION_PERMISSION,
    PERFORMANCE_APPRAISAL_QUESTION_SET_PERMISSION, HAS_PERMISSION_FROM_METHOD,
    KPI_PERMISSION, INDIVIDUAL_KPI_PERMISSION
)
from irhrs.permission.permission_classes import permission_factory

PerformanceAppraisalSettingPermission = permission_factory.build_permission(
    'PerformanceAppraisalSettingPermission',
    limit_write_to=[
        PERFORMANCE_APPRAISAL_PERMISSION, PERFORMANCE_APPRAISAL_SETTING_PERMISSION
    ],
    limit_edit_to=[
        PERFORMANCE_APPRAISAL_PERMISSION, PERFORMANCE_APPRAISAL_SETTING_PERMISSION
    ]
)

PerformanceAppraisalFormSubmissionActionPermission = permission_factory.build_permission(
    'PermissionAppraisalFormSubmissionActionPermission',
    allowed_to=[
        PERFORMANCE_APPRAISAL_PERMISSION,
        PERFORMANCE_APPRAISAL_FORM_SUBMISSION_ACTION_PERMISSION
    ]
)

PerformanceAppraisalQuestionSetPermission = permission_factory.build_permission(
    'PerformanceAppraisalQuestionSetPermission',
    allowed_to=[
        PERFORMANCE_APPRAISAL_PERMISSION,
        PERFORMANCE_APPRAISAL_QUESTION_SET_PERMISSION
    ]
)

ListOfAppraiserWithRespectToAppraiseePermission = permission_factory.build_permission(
    'ListOfAppraiserWithRespectToAppraiseePermission',
    allowed_to=[
        PERFORMANCE_APPRAISAL_PERMISSION,
        PERFORMANCE_APPRAISAL_SETTING_PERMISSION,
        HAS_PERMISSION_FROM_METHOD
    ]
)

KPIPermission = permission_factory.build_permission(
    'KPIPermission',
    allowed_to=[KPI_PERMISSION]
)


class AssignKPIPermission(BasePermission):
    def has_permission(self, request, view):
        if view.mode == 'hr':
            return validate_permissions(
                view.request.user.get_hrs_permissions(view.get_organization()),
                INDIVIDUAL_KPI_PERMISSION
            )
        return True
