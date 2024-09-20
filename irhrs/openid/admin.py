from django.contrib import admin
from oauth2_provider.models import get_application_model
from .models import *

from irhrs.core.utils.admin.filter import SearchByName, AdminFilterByDate
from rangefilter.filter import DateRangeFilter

class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "name", "user", "client_type",
        "authorization_grant_types",
        )
    list_filter = (
        "client_type", "skip_authorization",
        )
    radio_fields = {
        "client_type": admin.HORIZONTAL,
    }
    raw_id_fields = ("user", )

Application = get_application_model()


admin.site.register(ApplicationUser)

admin.site.unregister(Application)
admin.site.register(Application, ApplicationAdmin)

class ApplicationGroupAdmin(admin.ModelAdmin):
    search_fields = ('name',)

admin.site.register(ApplicationGroup, ApplicationGroupAdmin)
