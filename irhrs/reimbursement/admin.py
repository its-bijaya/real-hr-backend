from django.contrib import admin
from .models.reimbursement import *
from .models.setting import *
from .models.settlement import *

from irhrs.core.utils.admin.filter import AdminFilterByStatus, SearchByName, AdminFilterByDate

# Reimbursement
admin.site.register(AdvanceExpenseRequest, AdminFilterByStatus)
admin.site.register(AdvanceExpenseRequestDocuments, SearchByName)
admin.site.register(AdvanceExpenseRequestApproval, AdminFilterByDate)
admin.site.register(AdvanceExpenseRequestHistory, AdminFilterByDate)

# Setting
admin.site.register(ReimbursementSetting, AdminFilterByDate)
admin.site.register(ExpenseApprovalSetting, AdminFilterByDate)
admin.site.register(SettlementOptionSetting, AdminFilterByDate)

# Settlement
admin.site.register(ExpenseSettlement, AdminFilterByStatus)
admin.site.register(SettlementDocuments, SearchByName)
admin.site.register(SettlementOption, AdminFilterByDate)
admin.site.register(SettlementApproval, AdminFilterByDate)
admin.site.register(SettlementHistory, AdminFilterByDate)
