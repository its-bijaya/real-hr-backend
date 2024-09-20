from rest_framework.permissions import BasePermission

from irhrs.core.constants.payroll import REQUESTED, APPROVED
from irhrs.permission.constants.permissions import OVERALL_REIMBURSEMENT_PERMISSION, \
    EXPANSE_APPROVAL_SETTING_PERMISSION, HAS_PERMISSION_FROM_METHOD, \
    ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION,\
    EXPENSE_SETTLEMENT_IS_TAXBALE_EDIT_PERMISSION
from irhrs.permission.permission_classes import permission_factory

ExpenseSettingPermission = permission_factory.build_permission(
    'ExpenseSettingPermission',
    allowed_to=[
        OVERALL_REIMBURSEMENT_PERMISSION,
        EXPANSE_APPROVAL_SETTING_PERMISSION
    ]
)

ExpenseSettingReadPermission = permission_factory.build_permission(
    'ExpenseSettingReadOnlyPermission',
    limit_write_to=[
        OVERALL_REIMBURSEMENT_PERMISSION,
        EXPANSE_APPROVAL_SETTING_PERMISSION
    ]
)

ExpenseSettlementPermission = permission_factory.build_permission(
    'ExpenseSettlementPermission',
    allowed_to=[HAS_PERMISSION_FROM_METHOD],
    actions={
        'settlement_option': [ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION]
    }
)

ExpenseSettlementIsTaxableEditPermission = permission_factory.build_permission(
    'ExpenseSettlementIsTaxableEditPermission',
    actions={
        "is-taxable": [EXPENSE_SETTLEMENT_IS_TAXBALE_EDIT_PERMISSION]
    }
)

AdvanceExpenseRequestPermission = permission_factory.build_permission(
    'AdvanceExpenseRequestPermission',
    allowed_to=[]
)


class AdvanceExpenseRequestObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action == 'cancel':
            return view.mode == 'hr' or (obj.employee == request.user and obj.status == REQUESTED)
        elif view.action == 'approve':
            return obj.recipient.filter(id=request.user.id).exists() and obj.status == REQUESTED
        elif view.action in ['partial_update', 'update']:
            return obj.recipient.filter(id=request.user.id).exists() or view.mode == 'hr'
        elif view.action == 'deny':
            return (obj.recipient.filter(id=request.user.id).exists() and obj.status == REQUESTED) \
                   or (view.mode == 'hr' and obj.status in [REQUESTED, APPROVED])
        return True

# class ExpenseSettlementObjectPermission(AdvanceExpenseRequestObjectPermission):
#     def has_object_permission(self, request, view, obj):
#         if view.action == 'settlement_option':
#             context = view.get_serializer_context()
#             is_authority = validate_permissions(
#                 request.user.get_hrs_permissions(context.get('organization')),
#                 [ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION]
#             )
#             import ipdb
#             ipdb.set_trace()
#             return True
#         return super().has_object_permission(request, view, obj)
