from django.urls import path

from irhrs.leave.views.master_setting_import_export import (
    MasterSettingExportView,
    MasterSettingImportView
)
from irhrs.leave.views.leave_balance_import import (
    LeaveBalanceImportView, LeaveBalanceSampleDownloadView)
app_name = 'leave_admin'

urlpatterns = [
    path('export-master-setting', MasterSettingExportView.as_view(),
         name='export_master_setting'),
    path('import-master-setting', MasterSettingImportView.as_view(),
         name='import_master_setting'),
    path('import-leave-balance', LeaveBalanceImportView.as_view(),
         name="import_leave_balance"),
    path('import-leave-balance/sample/<int:organization_id>',
         LeaveBalanceSampleDownloadView.as_view(),
         name="import_leave_balance_sample"),

]
