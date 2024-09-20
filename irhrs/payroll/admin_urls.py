from django.urls import path

from irhrs.payroll.views import HeadingExportView, HeadingImportView

app_name = 'payroll_admin'

urlpatterns = [
    path('export-heading', HeadingExportView.as_view(),
         name='export_heading'),
    path('import-heading', HeadingImportView.as_view(),
         name='import_heading'),

]
