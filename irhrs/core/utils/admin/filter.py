# Common file that is responsible to admin customization for search and filter

from django.contrib import admin
from rangefilter.filter import DateRangeFilter


class SearchByTitle(admin.ModelAdmin):
    list_display = (
        '__str__',
        'created_at',
        'modified_at',
    )
    search_fields = ('title',)
    list_filter = (
        ('created_at', DateRangeFilter),
    )


class SearchByName(admin.ModelAdmin):
    list_display = (
        'name',
        'created_at',
        'modified_at',
    )
    search_fields = ('name',)
    list_filter = (
        ('created_at', DateRangeFilter),
    )


class AdminFilterByDate(admin.ModelAdmin):
    list_display = (
        '__str__',
        'created_at',
        'modified_at',
    )

    list_filter = (
        ('created_at', DateRangeFilter),
    )


class AdminFilterByStatus(admin.ModelAdmin):
    list_display = (
        '__str__',
        'status',
        'created_at',
        'modified_at',
    )

    list_filter = (
        'status',
        ('created_at', DateRangeFilter),
    )


class AdminFilterByCoefficient(admin.ModelAdmin):
    list_display = (
        'timesheet_user',
        'timesheet_for',
        'coefficient',
        'created_at',
    )
    list_select_related = ('timesheet_user', )
    list_filter = (
        ('created_at', DateRangeFilter),
        'coefficient',
    )
    search_fields = ['timesheet_user__id__iexact']


class SearchByNameAndFilterByStatus(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = (
        '__str__',
        'status',
        'created_at',
        'modified_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'status',
    )


class SearchByTitleAndFilterByStatus(admin.ModelAdmin):
    search_fields = ('title',)
    list_display = (
        '__str__',
        'status',
        'created_at',
        'modified_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'status',
    )
