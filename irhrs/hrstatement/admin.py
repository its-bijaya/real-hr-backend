from django.contrib import admin

from irhrs.core.utils.admin.filter import SearchByTitle
from rangefilter.filter import DateRangeFilter

from .models import HRPolicyHeading, HRPolicyBody

class HRPolicyHeadingAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_display = (
        '__str__', 
        'created_at', 
        'modified_at'
        )
    list_filter = (
        ('created_at', DateRangeFilter),
        'status',
        )

admin.site.register(HRPolicyHeading, HRPolicyHeadingAdmin)
admin.site.register(HRPolicyBody, SearchByTitle)
