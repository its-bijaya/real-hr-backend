from django.contrib import admin

from .models.worklog import WorkLog, WorkLogAttachment, WorkLogComment

from irhrs.core.utils.admin.filter import AdminFilterByDate

admin.site.register(WorkLog, AdminFilterByDate)
admin.site.register(WorkLogAttachment, AdminFilterByDate)
admin.site.register(WorkLogComment, AdminFilterByDate)
