from rest_framework.permissions import BasePermission

from irhrs.core.constants.payroll import REQUESTED, APPROVED, REPAYMENT, COMPLETED
from irhrs.permission.constants.permissions import (ALL_PAYROLL_PERMISSIONS,
                                                    ADVANCE_SALARY_SETTING_PERMISSION,
                                                    PAYROLL_SETTINGS_PERMISSION,
                                                    UNIT_OF_WORK_SETTINGS_PERMISSION)
from irhrs.permission.permission_classes import permission_factory

AdvanceSalarySettingPermission = permission_factory.build_permission(
    'AdvanceSalarySettingPermission',
    allowed_to=[ALL_PAYROLL_PERMISSIONS, ADVANCE_SALARY_SETTING_PERMISSION]
)


class AdvanceSalaryRequestObjectPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        if view.action == 'cancel':
            return obj.created_by == request.user and obj.status == REQUESTED
        elif view.action == 'approve':
            return obj.recipient == request.user and obj.status == REQUESTED
        elif view.action == 'deny':
            return (obj.recipient == request.user and obj.status == REQUESTED) or (
                view.mode == 'hr' and obj.status in [REQUESTED, APPROVED])
        elif view.action == 'pay_slip':
            return (view.mode == 'hr' and obj.status in [APPROVED, REPAYMENT, COMPLETED]) or (
                obj.employee == request.user and obj.status in [REPAYMENT, COMPLETED]
            )
        elif view.action == 'generate':
            return view.mode == 'hr' and obj.status == APPROVED
        elif view.action == 'settle_repayment':
            return view.mode == 'hr' and obj.status == REPAYMENT
        return True


UnitOfWorkSettingPermission = permission_factory.build_permission(
    'UnitOfWorkSettingPermission',
    limit_write_to=[
        ALL_PAYROLL_PERMISSIONS,
        PAYROLL_SETTINGS_PERMISSION,
        UNIT_OF_WORK_SETTINGS_PERMISSION
    ]
)
