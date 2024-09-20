# release: 2.9.26
# Populate preexisting ExpenseApprovalSetting data in SettlmenetApprovalSetting

from irhrs.reimbursement.models.setting import (
    ExpenseApprovalSetting, 
    SettlementApprovalSetting
)

def main():
    expense_request_settings = ExpenseApprovalSetting.objects.all()
    for setting in expense_request_settings:
        settlement_settings = SettlementApprovalSetting.objects.create(
            created_by = setting.created_by,
            modified_by = setting.modified_by,
            approve_by = setting.approve_by,
            supervisor_level = setting.supervisor_level,
            approval_level = setting.approval_level,
            organization = setting.organization
        )
        settlement_settings.employee.set(setting.employee.all())


if __name__ == "__main__":
    main()
