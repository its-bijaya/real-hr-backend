from django.contrib import admin
from rangefilter.filter import DateRangeFilter

from .models.account import (
    LeaveAccount, LeaveAccountHistory, CompensatoryLeaveAccount, LeaveEncashment,
    LeaveEncashmentHistory, AdjacentTimeSheetOffdayHolidayPenalty
)
from .models.request import (
    LeaveRequest, LeaveRequestHistory, LeaveRequestDeleteHistory,
    LeaveRequestDeleteStatusHistory, LeaveSheet, HourlyLeavePerDay
)
from .models.rule import (
    AccumulationRule, AdjacentLeaveReductionTypes, CompensatoryLeave, CompensatoryLeaveCollapsibleRule, DeductionRule,
    LeaveIrregularitiesRule, LeaveRule, PriorApprovalRule, RenewalRule, YearsOfServiceRule,
    TimeOffRule, CreditHourRule
)
from .models.settings import LeaveType, MasterSetting, LeaveApproval
from irhrs.core.utils.admin.filter import AdminFilterByStatus, SearchByName, AdminFilterByDate

# Account


class LeaveAccountAdmin(admin.ModelAdmin):
    search_fields = [
        'user__first_name',
        'user__middle_name',
        'user__last_name'
    ]
    list_display = [
        'user',
        'rule',
        'balance'
    ]
    list_filter = [
        ('created_at', DateRangeFilter)
    ]


admin.site.register(LeaveAccount, LeaveAccountAdmin)


class CompensatoryLeaveAccountAdmin(admin.ModelAdmin):

    search_fields = [
        'leave_account__user__first_name',
        'leave_account__user__middle_name',
        'leave_account__user__last_name'

    ]

    list_display = [
        'leave_account',
        'leave_for',
        'timesheet',
        'created_at'
    ]
    list_filter = [
        ('leave_for', DateRangeFilter),
        ('created_at', DateRangeFilter)
    ]
    autocomplete_fields = ['leave_account', 'timesheet']


admin.site.register(CompensatoryLeaveAccount, CompensatoryLeaveAccountAdmin)


class LeaveAccountHistoryAdmin(admin.ModelAdmin):

    search_fields = [
        'user__first_name',
        'user__middle_name',
        'user__last_name'

    ]
    list_display = [

        'user',
        'account',
        'actor',

    ]
    list_filter = [

        ('created_at', DateRangeFilter)
    ]


admin.site.register(LeaveAccountHistory, LeaveAccountHistoryAdmin)


class LeaveEncashmentAdmin(admin.ModelAdmin):

    search_fields = [
        'user__first_name',
        'user__middle_name',
        'user__last_name'
    ]
    list_display = [
        'user',
        'account',
        'status'
    ]
    list_filter = ['status',
                   ('created_at', DateRangeFilter)]


admin.site.register(LeaveEncashment, LeaveEncashmentAdmin)


class LeaveEncashmentHistoryAdmin(admin.ModelAdmin):
    search_fields = [
        'actor__first_name',
        'actor__middle_name',
        'actor__last_name'
    ]
    list_display = [
        'actor',
        'encashment',
        'action'
    ]
    list_filter = [
        'action',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(LeaveEncashmentHistory, LeaveEncashmentHistoryAdmin)


class AdjacentTimeSheetOffdayHolidayPenaltyAdmin(admin.ModelAdmin):
    search_fields = [
        'penalty'
    ]
    list_display = [
        'penalty_for',
        'penalty',
        'leave_account'
    ]
    list_filter = [
        ('created_at', DateRangeFilter)
    ]


admin.site.register(AdjacentTimeSheetOffdayHolidayPenalty,
                    AdjacentTimeSheetOffdayHolidayPenaltyAdmin)

# Request


class LeaveRequestAdmin(admin.ModelAdmin):
    search_fields = [
        'user__first_name',
        'user__middle_name',
        'user__last_name'

    ]
    list_display = [
        'user',
        'recipient_type',
        'leave_rule',
        'status'

    ]
    list_filter = [
        'status',
        'recipient_type',
        ('created_at', DateRangeFilter)

    ]


admin.site.register(LeaveRequest, LeaveRequestAdmin)


class LeaveRequestHistoryAdmin(admin.ModelAdmin):
    search_fields = [
        'actor__first_name',
        'actor__middle_name',
        'actor__last_name'

    ]

    list_display = [
        'request',
        'action',
        'actor',
        'recipient_type'
    ]
    list_filter = [
        'action',
        'recipient_type',
        ('created_at', DateRangeFilter)

    ]


admin.site.register(LeaveRequestHistory, LeaveRequestHistoryAdmin)


class LeaveRequestDeleteHistoryAdmin(admin.ModelAdmin):
    search_fields = [
        'recipient__first_name',
        'recipient__middle_name',
        'recipient__last_name'
    ]
    list_display = [

        'recipient',
        'leave_request',
        'status'
    ]
    list_filter = [
        'status',
        ('created_at', DateRangeFilter)

    ]


admin.site.register(LeaveRequestDeleteHistory, LeaveRequestDeleteHistoryAdmin)

admin.site.register(LeaveRequestDeleteStatusHistory, AdminFilterByStatus)
admin.site.register(LeaveSheet, AdminFilterByDate)

# Rule


class LeaveRuleAdmin(admin.ModelAdmin):
    search_fields = [
        'name'
    ]
    list_display = [
        'name',
        'description',
        'leave_type',
        'is_paid'
    ]
    list_filter = [
        'is_paid',
        'is_archived',
        'leave_type',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(LeaveRule, LeaveRuleAdmin)


class AdjacentLeaveReductionTypesAdmin(admin.ModelAdmin):
    search_fields = [
        'leave_type__name'
    ]
    list_display = [
        'leave_type',
        'leave_rule',
        'order_field'
    ]
    list_filter = [
        'leave_type',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(AdjacentLeaveReductionTypes,
                    AdjacentLeaveReductionTypesAdmin)


admin.site.register(LeaveIrregularitiesRule, AdminFilterByDate)


class AccumulationRuleAdmin(admin.ModelAdmin):
    search_fields = [
        'rule__leave_type__name'
    ]
    list_display = [
        'rule',
        'duration',
        'duration_type',
        'balance_added'
    ]
    list_filter = [
        'duration_type',
        'duration'
    ]


admin.site.register(AccumulationRule, AccumulationRuleAdmin)


class RenewalRuleAdmin(admin.ModelAdmin):
    search_fields = [
        'rule__leave_type__name'
    ]
    list_display = [
        'rule',
        'duration_type',
        'duration'
    ]
    list_filter = [
        'duration_type',
        'duration'
    ]


admin.site.register(RenewalRule, RenewalRuleAdmin)


class DeductionRuleAdmin(admin.ModelAdmin):
    search_fields = [
        'rule__leave_type__name'
    ]
    list_display = [
        'rule',
        'duration',
        'duration_type',
        'balance_deducted'
    ]
    list_filter = [
        'duration_type',
        'duration'
    ]


admin.site.register(DeductionRule, DeductionRuleAdmin)


class YearsOfServiceRuleAdmin(admin.ModelAdmin):

    list_display = [
        'rule',
        'years_of_service',
        'balance_added'
    ]
    list_filter = [
        'years_of_service',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(YearsOfServiceRule, YearsOfServiceRuleAdmin)


class CompensatoryLeaveAdmin(admin.ModelAdmin):
    search_fields = [
        'rule__leave_type__name'
    ]
    list_display = [
        'rule',
        'balance_to_grant',
        'hours_in_off_day'
    ]
    list_filter = [
        'hours_in_off_day',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(CompensatoryLeave, CompensatoryLeaveAdmin)


class CompensatoryLeaveCollapsibleRuleAdmin(admin.ModelAdmin):
    list_display = [
        'rule',
        'collapse_after',
        'collapse_after_unit'
    ]
    list_filter = [
        'collapse_after',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(CompensatoryLeaveCollapsibleRule,
                    CompensatoryLeaveCollapsibleRuleAdmin)


class TimeOffRuleAdmin(admin.ModelAdmin):

    list_display = [
        'rule',
        'total_late_minutes',
        'leave_type'
    ]
    list_filter = [
        'leave_type'
    ]


admin.site.register(TimeOffRule, TimeOffRuleAdmin)
admin.site.register(CreditHourRule, AdminFilterByDate)
admin.site.register(PriorApprovalRule, AdminFilterByDate)

# Setting
admin.site.register(MasterSetting, SearchByName)
admin.site.register(LeaveType, SearchByName)
admin.site.register(LeaveApproval, AdminFilterByDate)


class HourlyLeavePerDayAdmin(admin.ModelAdmin):
    search_fields = [
        'user__first_name',
        'user__middle_name',
        'user__last_name'
    ]
    list_display = [
        'user',
        'leave_for',
        'is_paid',
        'balance'
    ]

    list_filter = [
        'is_paid',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(HourlyLeavePerDay, HourlyLeavePerDayAdmin)
