from django.contrib import admin

from .models import Report, ReportDisplayField, ReportFilterField, ReportFilter, ReportRelatedFieldsInfo

from irhrs.core.utils.admin.filter import SearchByName

admin.site.register(Report, SearchByName)

admin.site.register([
    ReportDisplayField, ReportFilterField, ReportFilter, ReportRelatedFieldsInfo
    ])
