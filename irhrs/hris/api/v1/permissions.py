from rest_framework.permissions import BasePermission

from irhrs.core.constants.payroll import REQUESTED, APPROVED
from irhrs.hris.constants import ONBOARDING, OFFBOARDING, CHANGE_TYPE, OFFER_LETTER, CUSTOM
from irhrs.permission.constants.permissions import (
    HRIS_PERMISSION,
    HAS_PERMISSION_FROM_METHOD,
    HRIS_REPORTS_PERMISSION,
    HRIS_CHANGE_REQUEST_PERMISSION,
    HRIS_ID_CARD_PERMISSION,
    ASSIGN_UNASSIGN_DUTY_STATION_PERMISSION,
    HRIS_TASK_TEMPLATES_PERMISSION,
    HRIS_ON_BOARDING_PERMISSION,
    HRIS_EMPLOYMENT_REVIEW_PROCESS_PERMISSION,
    HRIS_OFF_BOARDING_PERMISSION,
    HRIS_LETTER_TEMPLATE_PERMISSION,
    HRIS_EMPLOYMENT_REVIEW_PERMISSION,
    HRIS_SEPARATION_TYPE_PERMISSION,
    WRITE_PAYROLL_PACKAGE_HEADINGS_PERMISSION,
    GENERATE_PAYROLL_PERMISSION,
    PAYROLL_REPORT_PERMISSION,
    ASSIGN_PAYROLL_PACKAGES_PERMISSION,
    PAYROLL_REBATE_PERMISSION,
    PAYROLL_HOLD_PERMISSION,
    PAYROLL_SETTINGS_PERMISSION,
    PROFILE_COMPLETENESS_REPORT_PERMISSION,
    USER_PROFILE_PERMISSION,
    ALL_PAYROLL_PERMISSIONS,
    ADVANCE_SALARY_SETTING_PERMISSION, WRITE_PAYROLL_HEADINGS_PERMISSION)
from irhrs.permission.permission_classes import permission_factory

ON_BOARDING_OFF_BOARDING_PROCESSES_GROUP = [
    HRIS_PERMISSION,
    HRIS_ON_BOARDING_PERMISSION,
    HRIS_EMPLOYMENT_REVIEW_PROCESS_PERMISSION,
    HRIS_OFF_BOARDING_PERMISSION
]

HRISPermission = permission_factory.build_permission(
    "HRISPermission",
    allowed_to=[HRIS_PERMISSION]
)

HRISUserPermission = permission_factory.build_permission(
    "HRISUserPermission",
    allowed_to=[
        HRIS_PERMISSION, HAS_PERMISSION_FROM_METHOD,
        USER_PROFILE_PERMISSION
    ],
)

HRISWritePermission = permission_factory.build_permission(
    "HRISWritePermission",
    limit_write_to=[HRIS_PERMISSION]
)

HRISReportPermission = permission_factory.build_permission(
    "HRISReportPermission",
    limit_read_to=[
        HRIS_PERMISSION, HRIS_REPORTS_PERMISSION, HAS_PERMISSION_FROM_METHOD,
        USER_PROFILE_PERMISSION
    ],
    limit_write_to=[HRIS_PERMISSION, HRIS_REPORTS_PERMISSION]
)

HRISReportHROnlyPermission = permission_factory.build_permission(
    "HRISReportPermission",
    allowed_to=[HRIS_PERMISSION, HRIS_REPORTS_PERMISSION],
)

ChangeRequestPermission = permission_factory.build_permission(
    "ChangeRequestPermission",
    allowed_to=[
        HRIS_PERMISSION, HRIS_CHANGE_REQUEST_PERMISSION,
        HAS_PERMISSION_FROM_METHOD
    ],
    limit_write_to=[HRIS_PERMISSION, HRIS_CHANGE_REQUEST_PERMISSION]
)

IDCardPermission = permission_factory.build_permission(
    "IDCardReportPermission",
    allowed_to=[HRIS_PERMISSION, HRIS_ID_CARD_PERMISSION],
)

AssignUnassignDutyStationPermission = permission_factory.build_permission(
    "AssignUnassignDutyStationPermission",
    allowed_to=[
        ASSIGN_UNASSIGN_DUTY_STATION_PERMISSION,
    ]
)

ProfileCompletenessReportPermission = permission_factory.build_permission(
    "AssignUnassignDutyStationPermission",
    allowed_to=[
        PROFILE_COMPLETENESS_REPORT_PERMISSION
    ]
)

TaskTemplatesPermission = permission_factory.build_permission(
    "TaskTemplatePermission",
    allowed_to=[HRIS_PERMISSION, HRIS_TASK_TEMPLATES_PERMISSION],
    limit_read_to=[
        *ON_BOARDING_OFF_BOARDING_PROCESSES_GROUP,
        HRIS_TASK_TEMPLATES_PERMISSION
    ]
)

OnBoardingPermission = permission_factory.build_permission(
    "OnBoardingPermission",
    allowed_to=[
        HRIS_PERMISSION, HRIS_ON_BOARDING_PERMISSION,
        HAS_PERMISSION_FROM_METHOD  # check if the action is tasks-summary
    ]
)

LetterTemplatePermission = permission_factory.build_permission(
    "LetterTemplatePermission",
    allowed_to=[HRIS_PERMISSION, HRIS_LETTER_TEMPLATE_PERMISSION],
    limit_read_to=[
        HRIS_PERMISSION,
        HRIS_LETTER_TEMPLATE_PERMISSION,
        *ON_BOARDING_OFF_BOARDING_PROCESSES_GROUP,
    ]
)

GeneratedLettersPermission = permission_factory.build_permission(
    "GeneratedLetterPermission",
    allowed_to=[HRIS_PERMISSION, *ON_BOARDING_OFF_BOARDING_PROCESSES_GROUP],
)

EmploymentReviewPermission = permission_factory.build_permission(
    "EmploymentReviewPermission",
    allowed_to=[
        HRIS_PERMISSION, HRIS_EMPLOYMENT_REVIEW_PERMISSION,
        # HAS_PERMISSION_FROM_METHOD  # check if the action is tasks-summary
    ],
)

ChangeTypePermission = permission_factory.build_permission(
    "ChangeTypePermission",
    limit_write_to=[HRIS_PERMISSION, HRIS_EMPLOYMENT_REVIEW_PERMISSION],
    limit_read_to=[
        HRIS_PERMISSION,
        HRIS_ON_BOARDING_PERMISSION,
        HRIS_EMPLOYMENT_REVIEW_PERMISSION,
        HRIS_EMPLOYMENT_REVIEW_PROCESS_PERMISSION,
        USER_PROFILE_PERMISSION,
    ]
)

SeparationTypePermission = permission_factory.build_permission(
    "SeparationTypePermission",
    allowed_to=[HRIS_PERMISSION, HRIS_SEPARATION_TYPE_PERMISSION],
    limit_read_to=[HRIS_OFF_BOARDING_PERMISSION, HRIS_PERMISSION,
                   HRIS_SEPARATION_TYPE_PERMISSION]
)

OffBoardingPermission = permission_factory.build_permission(
    "OffBoardingPermission",
    allowed_to=[
        HRIS_PERMISSION, HRIS_OFF_BOARDING_PERMISSION,
        HAS_PERMISSION_FROM_METHOD  # check if the action is tasks-summary
    ]
)


# Payroll Permissions
PayrollWriteHeadingPermission = permission_factory.build_permission(
    "PayrollWriteHeadingPermission",
    allowed_to=[WRITE_PAYROLL_PACKAGE_HEADINGS_PERMISSION],
    limit_read_to=[
        WRITE_PAYROLL_PACKAGE_HEADINGS_PERMISSION,
        GENERATE_PAYROLL_PERMISSION,
        PAYROLL_REPORT_PERMISSION,
        ASSIGN_PAYROLL_PACKAGES_PERMISSION,
        *ON_BOARDING_OFF_BOARDING_PROCESSES_GROUP
    ]
)

heading_limit_read_to = [
        PAYROLL_SETTINGS_PERMISSION,
        WRITE_PAYROLL_HEADINGS_PERMISSION,
        GENERATE_PAYROLL_PERMISSION,
        PAYROLL_REPORT_PERMISSION,
        ALL_PAYROLL_PERMISSIONS,
        ADVANCE_SALARY_SETTING_PERMISSION,
    ]
PayrollHeadingPermission = permission_factory.build_permission(
    "PayrollHeadingPermission",
    limit_write_to=[WRITE_PAYROLL_HEADINGS_PERMISSION],
    actions={
        'choices': [],
        'list': heading_limit_read_to,
        'retrieve': heading_limit_read_to,
    }
)

PayrollBulkApplyToUserPermission = permission_factory.build_permission(
    "PayrollBulkApplyToUserPermission",
    allowed_to=[WRITE_PAYROLL_HEADINGS_PERMISSION],
)

AssignPayrollPackagePermission = permission_factory.build_permission(
    "AssignPayrollPackagePermission",
    allowed_to=[ASSIGN_PAYROLL_PACKAGES_PERMISSION],
)

ViewEmployeeExperiencePackage = permission_factory.build_permission(
    "AssignPayrollPackagePermission",
    limit_write_to=[ASSIGN_PAYROLL_PACKAGES_PERMISSION],
    limit_read_to=[
        ASSIGN_PAYROLL_PACKAGES_PERMISSION, PAYROLL_REPORT_PERMISSION
    ]
)

GeneratePayrollPermission = permission_factory.build_permission(
    "GeneratePayrollPermission",
    allowed_to=[GENERATE_PAYROLL_PERMISSION]
)

ViewPayrollReportPermission = permission_factory.build_permission(
    "ViewPayrollReportPermission",
    limit_read_to=[PAYROLL_REPORT_PERMISSION]
)

PayrollSettingsPermission = permission_factory.build_permission(
    "PayrollSettingsPermission",
    allowed_to=[PAYROLL_SETTINGS_PERMISSION],
    limit_read_to=[
        ASSIGN_PAYROLL_PACKAGES_PERMISSION,
        PAYROLL_SETTINGS_PERMISSION,
        PAYROLL_REPORT_PERMISSION,
        GENERATE_PAYROLL_PERMISSION,
        WRITE_PAYROLL_PACKAGE_HEADINGS_PERMISSION
    ],
)

PayrollRebatePermission = permission_factory.build_permission(
    "PayrollRebatePermission",
    allowed_to=[PAYROLL_REBATE_PERMISSION]
)

HoldPayrollPermission = permission_factory.build_permission(
    "PayrollHoldPermission",
    allowed_to=[PAYROLL_HOLD_PERMISSION]
)

EmployeePayrollViewPermission = permission_factory.build_permission(
    "PayrollHoldPermission",
    allowed_to=[GENERATE_PAYROLL_PERMISSION],
    limit_read_to=[GENERATE_PAYROLL_PERMISSION, PAYROLL_REPORT_PERMISSION]
)


# End Payroll Permissions


class OnBoardingOffBoardingPermissionMixin:
    permission_classes = [GeneratedLettersPermission]

    def filter_queryset_by_permission(self, queryset):
        user_permissions = self.request.user.get_hrs_permissions(
            self.organization
        ).intersection(
            set(
                permission.get('code') for permission in
                ON_BOARDING_OFF_BOARDING_PROCESSES_GROUP
            )
        )

        types = [CUSTOM]
        if HRIS_ON_BOARDING_PERMISSION.get('code') in user_permissions:
            types.append(OFFER_LETTER)
            types.append(ONBOARDING)
        if HRIS_OFF_BOARDING_PERMISSION.get('code') in user_permissions:
            types.append(OFFBOARDING)
        if HRIS_EMPLOYMENT_REVIEW_PROCESS_PERMISSION.get(
                'code') in user_permissions:
            types.append(CHANGE_TYPE)
        return queryset.filter(
            letter_template__type__in=types
        )


class HRISReportPermissionMixin:
    permission_classes = [HRISReportPermission]

    def has_user_permission(self):
        if self.request.query_params.get('supervisor'):
            return self.request.query_params.get('supervisor') == str(
                self.request.user.id)
        return False


class UserResignationObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action == 'cancel':
            return obj.employee == request.user and obj.status == REQUESTED
        elif view.action == 'approve':
            return obj.recipient == request.user and obj.status == REQUESTED and \
                view.mode == 'approver'
        elif view.action == 'deny':
            return (obj.recipient == request.user and obj.status == REQUESTED) or (
                view.mode == 'hr' and obj.status in [REQUESTED, APPROVED])
        elif view.action == 'approve_by_hr':
            return view.mode == 'hr' and obj.status == APPROVED
        return True
