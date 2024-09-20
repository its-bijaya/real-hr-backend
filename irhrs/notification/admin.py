from django.contrib import admin

from .models.notification import Notification, OrganizationNotification

from irhrs.core.utils.admin.filter import AdminFilterByDate
from rangefilter.filter import DateRangeFilter


class NotificationAdmin(admin.ModelAdmin):
    readonly_fields = (
        'actor', 'action_content_type', 'action_object_id', 'recipient'
    )
    list_display = (
        '__str__',
        'created_at',
        'modified_at',
        )
    list_filter = (
        ('created_at', DateRangeFilter),
    )


admin.site.register(Notification, NotificationAdmin)
admin.site.register(OrganizationNotification, AdminFilterByDate)
