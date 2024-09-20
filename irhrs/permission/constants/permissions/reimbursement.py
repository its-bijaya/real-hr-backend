from irhrs.core.constants.common import P_REIMBURSEMENT

EXPANSE_APPROVAL_SETTING_PERMISSION = {
    "name": "Can perform reimbursement setting.",
    "code": "17.01",
    "category": P_REIMBURSEMENT,
    "organization_specific": True,
    "description": ""
}


ADVANCE_EXPENSE_REQUEST_ACTION_PERMISSION = {
    "name": "Can view/perform actions on requested advance expense.",
    "code": "17.02",
    "category": P_REIMBURSEMENT,
    "organization_specific": True,
    "description": ""
}

EXPENSE_SETTLEMENT_IS_TAXBALE_EDIT_PERMISSION = {
    "name": "Can alter is_taxable on expense settlement.",
    "code": "17.03",
    "category": P_REIMBURSEMENT,
    "organization_specific": True,
    "description": ""
}
