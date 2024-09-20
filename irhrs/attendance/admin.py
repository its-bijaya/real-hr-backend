from irhrs.attendance.models.breakout_penalty import BreakoutPenaltyLeaveDeductionSetting, TimeSheetPenaltyToPayroll
from django.contrib import admin
from django.contrib.admin import ModelAdmin

from irhrs.attendance.models.attendance_extraheadings import AttendanceHeadingReportSetting
from irhrs.attendance.models.overtime import OvertimeEntryDetail

from irhrs.attendance.models.shift_roster import TimeSheetRoster
from .models import *
from irhrs.core.utils.admin.filter import (
    AdminFilterByStatus, AdminFilterByCoefficient,
    SearchByName, AdminFilterByDate
)
from rangefilter.filter import DateRangeFilter


class AttendanceSourceAdmin(ModelAdmin):
    search_fields = ('name',)
    list_display = (
        '__str__',
        'created_at',
        'modified_at',
    )
    readonly_fields = 'extra_data',
    list_filter = (
        ('created_at', DateRangeFilter),
    )


class TimeSheetReportRequestAdmin(ModelAdmin):
    list_display = [
        'user', 'status', 'month_name', 'month_from_date',
        'month_to_date', 'year_name', 'year_from_date',
        'year_to_date', 'created_at', 'modified_at'
    ]

    list_filter = (
        ('created_at', DateRangeFilter),
        'status',
    )


def disable_entry(modeladmin, request, queryset):
    for entry in queryset:
        if not entry.is_deleted:
            entry.soft_delete()


def re_enable_entry(modeladmin, request, queryset):
    for entry in queryset:
        if entry.is_deleted:
            entry.revert_soft_delete()


class TimeSheetEntryAdmin(ModelAdmin):
    list_display = ['timesheet_user', 'timesheet_for', 'timestamp', 'entry_method', 'category',
                    'remark_category', 'remarks', 'is_deleted']
    readonly_fields = ('timesheet', 'is_deleted')

    list_filter = (
        ('created_at', DateRangeFilter),
        'entry_method',
    )

    actions = [disable_entry, re_enable_entry]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('timesheet', 'timesheet__timesheet_user')

    def timesheet_user(self, obj):
        return obj.timesheet.timesheet_user

    def timesheet_for(self, obj):
        return obj.timesheet.timesheet_for


# Attendance adjustment
# admin.site.register(AttendanceSource, AttendanceSourceAdmin)
class AttendanceAdjustmentAdmin(admin.ModelAdmin):

    list_display=[
        'timesheet',
        'category',
        'status'
    ]
    list_filter=[
        'status',
        'category'
    ]
    autocomplete_fields=[
        'timesheet'

    ]
admin.site.register(AttendanceAdjustment, AttendanceAdjustmentAdmin)
admin.site.register(AttendanceAdjustmentHistory, AdminFilterByDate)

# Timesheet Approval
class TimeSheetApprovalAdmin(admin.ModelAdmin):
    list_display=[
       'timesheet',
       'status'
    ]
    list_filter=[
        'status'
    ]
    autocomplete_fields=['timesheet']
admin.site.register(TimeSheetApproval, TimeSheetApprovalAdmin)
admin.site.register(TimeSheetEntryApproval, AdminFilterByStatus)

# Attendance
admin.site.register(IndividualAttendanceSetting, AdminFilterByDate)
admin.site.register(IndividualUserShift, AdminFilterByDate)
admin.site.register(IndividualWorkingHour, AdminFilterByDate)
class WebAttendanceFilterAdmin(admin.ModelAdmin):
    search_fields=[
        'setting__user__first_name',
        'setting__user__middle_name',
        'setting__user__last_name'
    ]
    list_display=[
        'setting',
        'cidr',
        'allow'
    ]
    list_filter=[
        'allow'
    ]

admin.site.register(WebAttendanceFilter,WebAttendanceFilterAdmin)
admin.site.register(AttendanceUserMap, AdminFilterByDate)


class TimeSheetAdmin(AdminFilterByCoefficient):
    search_fields = (
        'timesheet_user__first_name',
        'timesheet_user__middle_name',
        'timesheet_user__last_name',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        ('timesheet_for', DateRangeFilter),
        'coefficient',
    )

admin.site.register(TimeSheet, TimeSheetAdmin)
admin.site.register(TimeSheetEntry, TimeSheetEntryAdmin)

# Breakout penalty setting
admin.site.register(TimeSheetUserPenalty, AdminFilterByStatus)
admin.site.register(TimeSheetUserPenaltyStatusHistory, AdminFilterByStatus)
admin.site.register(BreakOutPenaltySetting, AdminFilterByDate)
admin.site.register(BreakoutPenaltyLeaveDeductionSetting, AdminFilterByDate)
class PenaltyRuleAdmin(admin.ModelAdmin):
    search_fields=[
        'penalty_setting__title',
        'penalty_setting__organization__name'
    ]
    list_display=[
        'penalty_setting',
        'calculation_type',
        'penalty_duration_in_days'
    ]
    list_filter=[
        ('created_at',DateRangeFilter),
        'calculation_type',
        'penalty_setting__organization__name'
    ]
admin.site.register(PenaltyRule,PenaltyRuleAdmin)
class BreakOutReportViewAdmin(admin.ModelAdmin):
    list_display=[
        'remark_category',
        'total_lost',
        'timesheet_for'

    ]
    list_filter=[
        'remark_category'
    ]
    autocomplete_fields=['timesheet','user']
   
admin.site.register(BreakOutReportView,BreakOutReportViewAdmin)

admin.site.register(AttendanceEntryCache, AdminFilterByDate)

# Credit hour
admin.site.register(CreditHourSetting, SearchByName)
admin.site.register(CreditHourRequest, AdminFilterByStatus)
admin.site.register(CreditHourRequestHistory, AdminFilterByDate)
class CreditHourTimeSheetEntryAdmin(admin.ModelAdmin):
    list_display=[
        'timesheet',
        'credit_setting',
        'earned_credit_hours',
        'status'
    ]
    list_filter=[
        'status',
        'is_archived'
    ]
    autocomplete_fields=[
        'timesheet',
        'credit_setting',
    ]
admin.site.register(CreditHourTimeSheetEntry, CreditHourTimeSheetEntryAdmin)
admin.site.register(CreditHourDeleteRequest, AdminFilterByStatus)
admin.site.register(CreditHourDeleteRequestHistory, AdminFilterByDate)

# Overtime
admin.site.register(OvertimeSetting, SearchByName)
admin.site.register(OvertimeClaim, AdminFilterByStatus)
class OvertimeEntryAdmin(admin.ModelAdmin):
    search_fields=[
        'user__first_name',
        'user__middle_name',
        'user__last_name'
    ]
    list_display=[
        'user',
        'overtime_settings',
        'timesheet'
    ]
    list_filter=[
        'overtime_settings__organization'
    ]
    autocomplete_fields=[
        'user',
        'overtime_settings',
        'timesheet'
    ]
admin.site.register(OvertimeEntry,OvertimeEntryAdmin )
admin.site.register(OvertimeClaimHistory, AdminFilterByDate)
admin.site.register(OvertimeEntryDetail, AdminFilterByDate)
class OvertimeRateAdmin(admin.ModelAdmin):
    readonly_fields=[]
    search_fields=[
        'overtime_settings__name'
    ]
    list_display=[
        'overtime_settings',
        'rate',
        'rate_type'
    ]
    list_filter=[
        'overtime_settings__organization__name'
    ]
admin.site.register(OvertimeRate,OvertimeRateAdmin)
admin.site.register(OvertimeEntryDetailHistory, AdminFilterByDate)

# Pre-approval
admin.site.register(PreApprovalOvertime, AdminFilterByStatus)
admin.site.register(PreApprovalOvertimeHistory, AdminFilterByDate)

# shift_roster
class TimeSheetRosterAdmin(ModelAdmin):
    search_fields = [
        'user__first_name',
        'user__last_name',
        'shift__name'
    ]
    list_display = ('user', 'shift', 'date')
    list_filter = (('date', DateRangeFilter), 'shift')
admin.site.register(TimeSheetRoster, TimeSheetRosterAdmin)
# Source
admin.site.register(AttendanceSource, AdminFilterByDate)

# Timesheet report request
admin.site.register(TimeSheetReportRequest, TimeSheetReportRequestAdmin)
admin.site.register(TimeSheetReportRequestHistory, AdminFilterByDate)

# Timesheet report setting
admin.site.register(TimeSheetRegistrationReportSettings, AdminFilterByDate)

# Travel attendance
admin.site.register(TravelAttendanceRequest, AdminFilterByStatus)
admin.site.register(TravelAttendanceRequestHistory, AdminFilterByStatus)
admin.site.register(TravelAttendanceDeleteRequest, AdminFilterByStatus)
admin.site.register(TravelAttendanceDeleteRequestHistory, AdminFilterByDate)
admin.site.register(TravelAttendanceSetting, AdminFilterByDate)
class TravelAttendanceDaysAdmin(admin.ModelAdmin):
 
    list_display=[
        'user',
        'is_archived',
        'day'
        
    ]
    list_filter=[
        'is_archived'
        
    ]
    autocomplete_fields=[
        'user',
        'timesheets'
    ]
admin.site.register(TravelAttendanceDays, TravelAttendanceDaysAdmin)
class TravelAttendanceAttachmentsAdmin(admin.ModelAdmin):
    readonly_fields=[]
    search_fields=[
        'travel_request__user__first_name',
        'travel_request__user__middle_name',
        'travel_request__user__last_name'
    ]
    list_display=[
        'travel_request',
        'filename'
    ]
    list_filter=[
        'travel_request__status'
    ]
admin.site.register(TravelAttendanceAttachments,TravelAttendanceAttachmentsAdmin)

# Workshifts
admin.site.register(WorkShift, SearchByName)
admin.site.register(WorkDay, AdminFilterByDate)
admin.site.register(WorkTiming, AdminFilterByDate)


# TimeSheet Penalty to Payroll [Lost hours/minutes to payroll]
class TimeSheetPenaltyToPayrollAdmin(admin.ModelAdmin):
    search_fields=[
        'user_penalty__user__first_name',
        'user_penalty__user__middle_name',
        'user_penalty__user__last_name'
    ]
    readonly_fields=[]
    list_display=[
        'user_penalty',
        'confirmed_on',
        'is_archived'
    ]
    list_filter=[
        ('confirmed_on',DateRangeFilter),
        'is_archived'
    ]
admin.site.register(TimeSheetPenaltyToPayroll,TimeSheetPenaltyToPayrollAdmin)

admin.site.register(AttendanceHeadingReportSetting)
