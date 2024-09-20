from django.contrib import admin
from .models import Export

from irhrs.core.utils.admin.filter import SearchByNameAndFilterByStatus

# Register your models here.
admin.site.register(Export, SearchByNameAndFilterByStatus)
