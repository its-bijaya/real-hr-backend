from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from irhrs.core.mixins.admin import ModelResourceMetaMixin
from irhrs.core.utils.admin.filter import (
    SearchByNameAndFilterByStatus, AdminFilterByStatus,
    SearchByTitle, SearchByName, AdminFilterByDate,
)
from rangefilter.filter import DateRangeFilter

from .models import (
    Organization, OrganizationBank, OrganizationAddress,
    OrganizationAppearance, OrganizationBranch, OrganizationDocument,
    OrganizationEquipment, OrganizationDivision,
    EmploymentLevel, EmploymentStatus, EmploymentJobTitle, EmploymentStep,
    OrganizationMission, OrganizationVision, MessageToUser, UserOrganization, Holiday,
    HolidayRule, FiscalYear, FiscalYearMonth, EquipmentAssignedTo, AssignedEquipmentStatus,
    KnowledgeSkillAbility, MeetingRoom, MeetingRoomAttachment, MeetingRoomStatus, OrganizationEthics,
    NotificationTemplateMap, ContractSettings, ApplicationSettings, EmailNotificationSetting)


# Assets
class OrganizationEquipmentAdmin(ImportExportModelAdmin):
    search_fields = ('name', )
    list_display = (
        'name',
        'created_at',
        'modified_at',
        'released_date'
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'is_damaged',
        'organization',
        'category',
    )


admin.site.register(OrganizationEquipment, OrganizationEquipmentAdmin)


class EquipmentAssignedToAdmin(ImportExportModelAdmin):

    search_fields = [
        'user__first_name', 'user__last_name', 'division__name',
        'branch__organization__name', 'assigned_date', 'released_date',
        'equipment__name',
    ]
    list_display = (
        'user',
        'division',
        'branch',
        'released_date'
    )
    list_filter = (
        ('assigned_date', DateRangeFilter),
        'branch',
    )


admin.site.register(EquipmentAssignedTo, EquipmentAssignedToAdmin)


class AssignedEquipmentStatusAdmin(ImportExportModelAdmin):

    search_fields = [
        'assigned_equipment__equipment__name',
    ]
    list_display = (
        'assigned_equipment',
        'confirmed_by',
        'status',
        'confirmed'
    )
    list_filter = (
        'confirmed',
        'status'
    )


admin.site.register(AssignedEquipmentStatus, AssignedEquipmentStatusAdmin)

# Bank
admin.site.register(OrganizationBank, AdminFilterByDate)

# Bank and division


class OrganizationDivisionResource(resources.ModelResource):
    class Meta(ModelResourceMetaMixin):
        model = OrganizationDivision


class OrganizationDivisionAdmin(ImportExportModelAdmin):
    resource_class = OrganizationDivisionResource
    search_fields = ('name', )
    list_display = (
        'name',
        'created_at',
        'modified_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
    )


admin.site.register(OrganizationDivision, OrganizationDivisionAdmin)


class OrganizationBranchResource(resources.ModelResource):
    class Meta(ModelResourceMetaMixin):
        model = OrganizationBranch


class OrganizationBranchAdmin(ImportExportModelAdmin):
    resource_class = OrganizationBranchResource
    search_fields = ('name', )
    list_display = (
        'name',
        'created_at',
        'modified_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
    )


admin.site.register(OrganizationBranch, OrganizationBranchAdmin)


# Employment
class EmploymentLevelResource(resources.ModelResource):
    class Meta(ModelResourceMetaMixin):
        model = EmploymentLevel


class EmploymentLevelAdmin(ImportExportModelAdmin):
    resource_class = EmploymentLevelResource
    search_fields = ('title', 'code', 'organization__name')
    list_display = (
        'title',
        'created_at',
        'modified_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'level',
    )


admin.site.register(EmploymentLevel, EmploymentLevelAdmin)


class EmploymentStatusResource(resources.ModelResource):
    class Meta(ModelResourceMetaMixin):
        model = EmploymentStatus


class EmploymentStatusAdmin(ImportExportModelAdmin):
    resource_class = EmploymentStatusResource
    search_fields = ('title', )
    list_display = (
        'title',
        'created_at',
        'modified_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
    )


admin.site.register(EmploymentStatus, EmploymentStatusAdmin)


class EmploymentJobTitleResource(resources.ModelResource):
    class Meta(ModelResourceMetaMixin):
        model = EmploymentJobTitle


class EmploymentJobTitleAdmin(ImportExportModelAdmin):
    resource_class = EmploymentJobTitleResource
    search_fields = ('title', )
    list_display = (
        'title',
        'created_at',
        'modified_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'organization',
    )


admin.site.register(EmploymentJobTitle, EmploymentJobTitleAdmin)


class EmploymentStepAdmin(ImportExportModelAdmin):
    search_fields = ('title',)
    list_display = (
        'title',
        'organization',
        'created_at',
    )
    list_filter = (
        'title',
        ('created_at', DateRangeFilter),
    )


admin.site.register(EmploymentStep, EmploymentStepAdmin)


# Fiscal year
class FiscalYearAdmin(SearchByName, AdminFilterByDate):
    search_fields = ('name',)
    list_filter = (
        ('created_at', DateRangeFilter),
        'organization__name'
    )


admin.site.register(FiscalYear, FiscalYearAdmin)


class FiscalYearMonthAdmin(AdminFilterByDate):
    search_fields = ('display_name', 'fiscal_year__name')
    list_display = (
        'display_name',
        'start_at',
        'end_at'
    )
    list_filter = (
        ('start_at', DateRangeFilter),
        'fiscal_year__name',
    )


admin.site.register(FiscalYearMonth, FiscalYearMonthAdmin)

# Holiday


class HolidayAdmin(SearchByName):
    search_fields = (
        'name',
        'organization__name',
    )
    list_display = (
        'name',
        'date',
    )
    list_filter = (
        'category',
        'organization__name'
    )


admin.site.register(Holiday, HolidayAdmin)

admin.site.register(HolidayRule, AdminFilterByDate)

# Knowledge skill ability


class KnowledgeSkillAbilityAdmin(SearchByName):
    search_fields = ('name', 'organization__name')
    list_display = (
        'name',
        'ksa_type',
        'organization'
    )
    list_filter = (
        'ksa_type',
        'organization'
    )


admin.site.register(KnowledgeSkillAbility, KnowledgeSkillAbilityAdmin)

# Meeting room


class MeetingRoomAdmin(SearchByName):
    search_fields = (
        'name',
        'location',
        'capacity',
    )
    list_display = (
        'name',
        'location',
        'branch'
    )
    list_filter = (
        'organization__name',
        'capacity',
    )


admin.site.register(MeetingRoom, MeetingRoomAdmin)
admin.site.register(MeetingRoomAttachment, AdminFilterByDate)


class MeetingRoomStatusAdmin(AdminFilterByDate):
    search_fields = ('meeting_room__name',)
    list_display = (
        'meeting_room',
        'booked_from',
        'booked_to',
    )


admin.site.register(MeetingRoomStatus, MeetingRoomStatusAdmin)

# Message to user


class MessageToUserAdmin(SearchByTitle):
    search_fields = ('title',)
    list_display = (
        'title',
        'message_from',
        'published'
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'published',
    )


admin.site.register(MessageToUser, MessageToUserAdmin)

# Mission and vision
admin.site.register(OrganizationVision, SearchByTitle)
admin.site.register(OrganizationMission, SearchByTitle)

# Organization


class OrganizationResource(resources.ModelResource):
    class Meta(ModelResourceMetaMixin):
        model = Organization


def attendance_action(self):
    return format_html(
        '<a href="{}">Assign Shift</a>',
        reverse(
            'attendance_admin:assign_shift_from_date',
            kwargs={
                'organization': self.slug
            }
        )
    )


attendance_action.short_description = 'Actions'
attendance_action.allow_tags = True


class OrganizationAdmin(ImportExportModelAdmin):
    resource_class = OrganizationResource
    search_fields = ('name', )
    list_display = (
        'name', 'abbreviation', 'organization_head', attendance_action
    )
    list_filter = (
        ('created_at', DateRangeFilter),
    )


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(OrganizationAddress, AdminFilterByDate)
admin.site.register(OrganizationAppearance, AdminFilterByDate)
admin.site.register(OrganizationDocument, SearchByTitle)


class UserOrganizationAdmin(AdminFilterByDate):
    search_fields = (
        'user__first_name',
        'organization__name',
    )
    list_display = (
        'user',
        'organization',
        'can_switch'
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'can_switch',
        'organization'
    )


admin.site.register(UserOrganization, UserOrganizationAdmin)

# Others


class OrganizationEthicsAdmin(SearchByTitle):
    search_fields = (
        'title',
        'organization__name',
    )
    list_display = (
        'title',
        'organization',
        'published'
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'published',
        'organization'
    )


admin.site.register(OrganizationEthics, OrganizationEthicsAdmin)


class NotificationTemplateMapAdmin(AdminFilterByDate):
    search_fields = (
        'organization__name',
        'template__name'
    )
    list_display = (
        'template',
        'organization',
        'is_active'
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'organization'
    )


admin.site.register(NotificationTemplateMap, NotificationTemplateMapAdmin)

# Settings


class ContractSettingsAdmin(SearchByName):
    search_fields = ('organization__name',)
    list_display = (
        'organization',
        'safe_days',
        'critical_days',
    )
    list_filter = (
        'safe_days',
        'critical_days'
    )


admin.site.register(ContractSettings, ContractSettingsAdmin)
admin.site.register(ApplicationSettings)
admin.site.register(EmailNotificationSetting)
