from django.db.models import Q

from irhrs.permission.constants.permissions import (
    USER_PROFILE_PERMISSION,
    HAS_OBJECT_PERMISSION,
    HRIS_IMPORT_EMPLOYEE_PERMISSION,
    HRIS_PERMISSION,
    USER_BANK_INFORMATION_IMPORT_PERMISSION,
    USER_EXPERIENCE_IMPORT_PERMISSION,
    USER_CONTACT_DETAIL_IMPORT_PERMISSION,
    USER_LEGAL_INFO_IMPORT_PERMISSION,
)
from irhrs.permission.permission_classes import permission_factory

ud_permission = permission_factory.build_permission(
    "UserDetailPermission",
    limit_edit_to=[USER_PROFILE_PERMISSION, HAS_OBJECT_PERMISSION],
    actions={
        'create': [USER_PROFILE_PERMISSION],
        'destroy': [USER_PROFILE_PERMISSION],
        'change_password': [HAS_OBJECT_PERMISSION]
    },
    allowed_user_fields=['user'],
)

UserExperienceImportPermission = permission_factory.build_permission(
    "UserExperienceBulkImportPermission",
    allowed_to=[
        USER_EXPERIENCE_IMPORT_PERMISSION
    ],
)
UserContactDetailPermission = permission_factory.build_permission(
    "UserContactDetailBulkImportPermission",
    allowed_to=[
        USER_CONTACT_DETAIL_IMPORT_PERMISSION
    ],
)

UserLegalInfoImportPermission = permission_factory.build_permission(
    "UserLegalInfoBulkImportPermission",
    allowed_to=[
        USER_LEGAL_INFO_IMPORT_PERMISSION
    ],
)

UserBankInfoImportPermission = permission_factory.build_permission(
    "UserBankInfoImportPermission",
    allowed_to=[
        USER_BANK_INFORMATION_IMPORT_PERMISSION
    ],
)

class UserDetailPermission(ud_permission):
    def filter_queryset(self, request, view, queryset):

        # filter user list by switchable organization list and self
        switchable_pks = request.user.switchable_organizations_pks
        if switchable_pks:
            # allow list of user not associated with any organization to
            # be seen if user can switch to at least one
            # organization
            fil = Q(
                organization_id__in=request.user.switchable_organizations_pks
            ) | Q(organization__isnull=True) | Q(user_id=request.user.id)
        else:
            fil = Q(user_id=request.user.id)

        return queryset.filter(fil)


UserImportPermission = permission_factory.build_permission(
    "UserImportPermission",
    allowed_to=[HRIS_PERMISSION, HRIS_IMPORT_EMPLOYEE_PERMISSION]
)
