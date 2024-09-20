from django.contrib import admin

from django import forms
from django.db import models
from import_export.admin import ImportExportModelAdmin

from .models import *

from irhrs.core.utils.admin.filter import (
    AdminFilterByStatus, SearchByTitle, SearchByName,
    AdminFilterByDate,
)

from rangefilter.filter import DateRangeFilter

from .models.EmployeeMetricsSetting import EmployeeMetricHeadingReportSetting
from .models.payslip_report_setting import PayslipReportSetting
from .models.unit_of_work_settings import UserOperationRate


# Advance salary request


class AdvanceSalaryRequestAdmin(AdminFilterByStatus):
    search_fields = (
        'employee__first_name',
    )
    list_display = (
        'employee',
        'amount',
        'reason_for_request',
        'status'
    )
    list_filter = (
        'status',
        ('created_at', DateRangeFilter),
    )


admin.site.register(AdvanceSalaryRequest, AdvanceSalaryRequestAdmin)


admin.site.register(AdvanceSalaryRequestDocument, SearchByName)


class AdvanceSalaryRequestApprovalAdmin(AdminFilterByStatus):
    search_fields = (
        'user__first_name',
    )
    list_display = (
        'user',
        'request',
        'role',
        'status',
    )
    list_filter = (
        'status',
        ('created_at', DateRangeFilter),
    )


admin.site.register(AdvanceSalaryRequestApproval, AdvanceSalaryRequestApprovalAdmin)


class AdvanceSalarySurplusRequestAdmin(AdminFilterByStatus):
    search_fields = (
        'employee__first_name',
    )
    list_display = (
        'employee',
        'amount',
        'reason_for_request',
        'acted_by',
        'acted_on',
    )
    list_filter = (
        'status',
        ('created_at', DateRangeFilter)
    )


admin.site.register(AdvanceSalarySurplusRequest, AdvanceSalarySurplusRequestAdmin)


class AdvanceSalaryRepaymentAdmin(AdminFilterByDate):
    search_fields = (
        'payment_type',
    )
    list_display = (
        'request',
        'amount',
        'paid',
        'paid_on',
        'payment_type'
    )
    list_filter = (
        'payment_type',
        'paid',
        ('created_at', DateRangeFilter)
    )


admin.site.register(AdvanceSalaryRepayment, AdvanceSalaryRepaymentAdmin)


class AdvanceSalaryRequestHistoryAdmin(AdminFilterByDate):
    search_fields = (
        'actor__first_name',
    )
    list_display = (
        'request',
        'actor',
        'action'
    )
    list_filter = (
        'action',
        ('created_at', DateRangeFilter)
    )


admin.site.register(AdvanceSalaryRequestHistory, AdvanceSalaryRequestHistoryAdmin)

# Advance salary setting
admin.site.register(AdvanceSalarySetting, AdminFilterByDate)
class AmountSettingAdmin(admin.ModelAdmin):

    search_fields=[
        'advance_salary_setting__organization__name',
        'payroll_heading__name'
    ]
    list_display=[
    'advance_salary_setting',
    'payroll_heading',
    'created_at'

    ]
    list_filter=[
        ('payroll_heading',DateRangeFilter)
    ]

admin.site.register(AmountSetting, AmountSettingAdmin)
class ApprovalSettingAdmin(admin.ModelAdmin):
    search_fields=[
        'advance_salary_setting__organization__name',
        'employee__first_name',
        'employee__middle_name',
        'employee__last_name'
    ]
    list_display=[
        'advance_salary_setting',
        'employee',
        'approve_by',
        'supervisor_level',

    ]
    list_filter=[
        'approve_by',
        ('created_at',DateRangeFilter)
    ]
admin.site.register(ApprovalSetting, ApprovalSettingAdmin)

# Payroll approval setting


class PayrollApprovalSettingAdmin(AdminFilterByDate):
    search_fields = (
        'organization__name',
        'user__first_name',
    )
    list_display = (
        'user',
        'organization',
        'approval_level'
    )
    list_filter = (
        'organization',
        'approval_level',
        ('created_at', DateRangeFilter)
    )


admin.site.register(PayrollApprovalSetting, PayrollApprovalSettingAdmin)

# Payroll approval
admin.site.register(PayrollApproval, AdminFilterByStatus)
admin.site.register(PayrollApprovalHistory, AdminFilterByDate)

# Payroll increment


class PayrollIncrementAdmin(AdminFilterByDate):
    search_fields = (
        'employee__first_name',
    )
    list_display = (
        'employee',
        'percentage_increment',
        'effective_from',
    )


admin.site.register(PayrollIncrement, PayrollIncrementAdmin)

# PaySlip report Setting


class MonthlyTaxReportSettingAdmin(admin.ModelAdmin):
    search_fields = (
        'organization__name',
    )
    list_display = (
        'organization',
        'category',
        'heading',
    )


admin.site.register(MonthlyTaxReportSetting, MonthlyTaxReportSettingAdmin)


class PayslipReportSettingAdmin(admin.ModelAdmin):
    search_fields = (
        'organization__name',
    )
    list_display = (
        'organization',
    )


admin.site.register(PayslipReportSetting, PayslipReportSettingAdmin)

# Plugin


class PayrollVariablePluginAdmin(admin.ModelAdmin):
    search_fields = (
        'organization__name',
        'name'
    )
    list_display = (
        'organization',
        'name',
    )


admin.site.register(PayrollVariablePlugin, PayrollVariablePluginAdmin)
# Payroll


class HeadingAdmin(AdminFilterByDate):
    search_fields = (
        'organization__name',
        'name'
    )
    list_display = (
        'organization',
        'name',
        'taxable',

    )
    list_filter = (
        'type',
        'absent_days_impact',
    )


admin.site.register(Heading, HeadingAdmin)
class ExtraHeadingReportSettingAdmin(admin.ModelAdmin):
    search_fields=[
        'organization__name'
    ]
    list_display=[
        'organization',
        'headings'

    ]
    list_filter=[
        'organization'
    ]
admin.site.register(ExtraHeadingReportSetting,ExtraHeadingReportSettingAdmin)
class HeadingDependencyAdmin(admin.ModelAdmin):
    search_fields=[
        'source__name',
    ]
    list_display=[
        'source',
        'target'
    ]
    list_filter=[
        'source'
    ]
admin.site.register(HeadingDependency,HeadingDependencyAdmin)

class PackageAdmin(admin.ModelAdmin):
    search_fields = ('name', )
    list_display = ('name', 'created_at')
    list_filter = (
        'organization',
        ('created_at', DateRangeFilter),
        )


admin.site.register(Package, PackageAdmin)


class PackageHeadingAdmin(AdminFilterByDate):
    search_fields = (
        'package__name',
        'heading__name'
    )
    list_display = (
        'package',
        'heading',
        'type'
    )
    list_filter = (
        'taxable',
        'type',
        'heading'
    )


admin.site.register(PackageHeading, PackageHeadingAdmin)


class YearlyHeadingDetailAdmin(AdminFilterByDate):
    search_fields = (
        'heading__name',
    )
    list_display = (
        'heading',
        'fiscal_year',
        'date'
    )
    list_filter = (
        ('date', DateRangeFilter),
    )


admin.site.register(YearlyHeadingDetail, YearlyHeadingDetailAdmin)


class RebateSettingAdmin(admin.ModelAdmin):
    search_fields = (
        'organization__name',
        'title'
    )
    list_display = (
        'organization',
        'title',
        'amount'
    )
    list_filter=[
        'organization'
    ]

admin.site.register(RebateSetting, RebateSettingAdmin)
class PackageHeadingDependencyAdmin(admin.ModelAdmin):
    search_fields=[
        'source__package__name'
    ]
    list_display=[
        'source',
        'target'
    ]
    list_filter=[
        'source__package__name'
    ]
    autocomplete_fields=['source','target']
admin.site.register(PackageHeadingDependency,PackageHeadingDependencyAdmin)


class PayrollAdmin(admin.ModelAdmin):
    search_fields = (
        'organization__name',
    )
    list_display = (
        'organization',
        'status',
        'approved_by',
        'from_date',
        'to_date'
        )

    list_filter = (
        'status',
        ('from_date', DateRangeFilter),
        )


admin.site.register(Payroll, PayrollAdmin)
class SignedPayrollHistoryAdmin(admin.ModelAdmin):
    search_fields=[
        'payroll__organization__name'
    ]
    list_display=[
        'payroll',
        'is_latest',
        'created_at'
    ]
    list_filter=[
        ('created_at',DateRangeFilter)
    ]
admin.site.register(SignedPayrollHistory, SignedPayrollHistoryAdmin)
admin.site.register(PayrollGenerationHistory, AdminFilterByStatus)
class PayrollExcelUpdateHistoryAdmin(admin.ModelAdmin):
    search_fields=[
        'payroll__organization__name'
    ]
    list_display=[
        'payroll',
        'status',
        'created_at'
    ]
    list_filter=[
        ('created_at',DateRangeFilter)
    ]
admin.site.register(PayrollExcelUpdateHistory, PayrollExcelUpdateHistoryAdmin)


class EmployeePayrollAdmin(admin.ModelAdmin):
    search_fields = (
        'employee__first_name',
        'package__name'
    )
    list_display = (
        'employee',
        'payroll',
        'package',
        'acknowledgement_status'
    )
    list_filter = (
        'package',
    )


admin.site.register(EmployeePayroll, EmployeePayrollAdmin)
admin.site.register(EmployeePayrollComment, AdminFilterByDate)
class PayrollEditHistoryAmountAdmin(admin.ModelAdmin):
    search_fields=[
        'heading__name'
    ]
    list_display=[
        'heading',
        'old_amount',
        'new_amount'
    ]
admin.site.register(PayrollEditHistoryAmount,PayrollEditHistoryAmountAdmin)
admin.site.register(EmployeePayrollHistory, AdminFilterByDate)


class ReportRowRecordAdmin(admin.ModelAdmin):
    search_fields = (
        'heading__name',
    )
    list_display = (

        'heading',
        'employee_payroll'
    )
    list_filter = (
        ('from_date', DateRangeFilter),
    )


admin.site.register(ReportRowRecord, ReportRowRecordAdmin)


class SalaryHoldingAdmin(admin.ModelAdmin):
    search_fields = (
        'employee__first_name',
    )
    list_display = (
        'employee',
        'from_date',
        'to_date',
        'released'
    )
    list_filter = (
        'released',
    )


admin.site.register(SalaryHolding, SalaryHoldingAdmin)
class UserExperiencePackageSlotAdmin(admin.ModelAdmin):
    search_fields=[
        'user_experience__user__first_name',
        'user_experience__user__middle_name',
        'user_experience__user__last_name',
        'user_experience__job_title__title',
        'package__name'
    ]
    list_display=[
        'user_experience',
        'package',
        'active_from_date'
    ]
    list_filter=[
        ('active_from_date',DateRangeFilter),
        'user_experience__job_title__title'
    ]
admin.site.register(UserExperiencePackageSlot,UserExperiencePackageSlotAdmin)


class ReportRowUserExperiencePackageAdmin(admin.ModelAdmin):
    search_fields = (
        'package_heading__package__name',
    )
    list_display = (
        'package_slot',
        'package_heading',
        'package_amount'
    )

admin.site.register(ReportRowUserExperiencePackage, ReportRowUserExperiencePackageAdmin)

class OverviewConfigAdmin(admin.ModelAdmin):

    list_display=[
        'organization',
        'salary_payable',
        'gratuity'
    ]
    list_filter=[
        'organization'
    ]
admin.site.register(OverviewConfig,OverviewConfigAdmin)


class OrganizationPayrollConfigAdmin(admin.ModelAdmin):
    search_fields = (
        'organization__name',
    )
    list_display = (
        'organization',
        'start_fiscal_year'
    )


admin.site.register(OrganizationPayrollConfig, OrganizationPayrollConfigAdmin)

class ReportSalaryBreakDownRangeConfigAdmin(admin.ModelAdmin):
    list_display=[
        'overview_config',
        'from_amount',
        'to_amount'
    ]

admin.site.register(ReportSalaryBreakDownRangeConfig,ReportSalaryBreakDownRangeConfigAdmin)


class ExternalTaxDiscountAdmin(SearchByTitle):
    search_fields = (
        'title',
        'employee__first_name',
    )
    list_display = (
        'employee',
        'fiscal_year',
        'title',
        'amount'
    )


admin.site.register(ExternalTaxDiscount, ExternalTaxDiscountAdmin)
class BackdatedCalculationAdmin(admin.ModelAdmin):
    search_fields=[
        'package_slot__package__name'
    ]
    list_display=[
        'package_slot',
        'heading',
        'previous_amount',
        'current_amount'
    ]
admin.site.register(BackdatedCalculation,BackdatedCalculationAdmin)


class ExcelPayrollPackageAdmin(admin.ModelAdmin):
    search_fields = (
        'name',
        'organization__name',
    )
    list_display = (
        'name',
        'organization',
        'assigned_date',
        'status'
    )
    list_filter = (
        'status',
        ('assigned_date', DateRangeFilter),
    )


admin.site.register(ExcelPayrollPackage, ExcelPayrollPackageAdmin)

# Unit of work requests


class UnitOfWorkRequestAdmin(AdminFilterByStatus):
    search_fields = (
        'user__first_name',
        'recipient__first_name',
    )
    list_display = (
        'user',
        'recipient',
        'status',
        'confirmed_on'
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'status'
    )


admin.site.register(UnitOfWorkRequest, UnitOfWorkRequestAdmin)


class UnitOfWorkRequestHistoryAdmin(AdminFilterByDate):
    list_display = (
        'request',
        'action_performed',
        'action_performed_by'
    )


admin.site.register(UnitOfWorkRequestHistory, UnitOfWorkRequestHistoryAdmin)

# Unit of work settings


class OperationAdmin(SearchByTitle):
    list_display = (
        'title',
        'organization',
    )
    list_filter = (
        'organization',
        ('created_at', DateRangeFilter),
    )


admin.site.register(Operation, OperationAdmin)


class OperationCodeAdmin(SearchByTitle):
    list_display = (
        'title',
        'description',
    )
    list_filter = (
        'organization',
    )


admin.site.register(OperationCode, OperationCodeAdmin)


class OperationRateAdmin(AdminFilterByDate):
    search_fields = (
        'operation__title',
    )
    list_display = (
        'operation',
        'operation_code',
        'rate',
    )


admin.site.register(OperationRate, OperationRateAdmin)


class UserOperationRateAdmin(admin.ModelAdmin):
    search_fields = (
        'user__first_name',
    )
    list_display = (
        'user',
        'rate'
    )


admin.site.register(UserOperationRate, UserOperationRateAdmin)


class BinaryFileInput(forms.ClearableFileInput):

    def is_initial(self, value):
        """
        Return whether value is considered to be initial value.
        """
        return bool(value)

    def format_value(self, value):
        """Format the size of the value in the db.

        We can't render it's name or url, but we'd like to give some information
        as to wether this file is not empty/corrupt.
        """
        if self.is_initial(value):
            return f'{len(value)} bytes'


    def value_from_datadict(self, data, files, name):
        """Return the file contents so they can be put in the db."""
        upload = super().value_from_datadict(data, files, name)
        if upload:
            return upload.read()

class PayrollVariablePluginField(forms.CharField):
    def to_python(self, value):
        """Return a string."""
        if value in self.empty_values:
            return self.empty_value
        return value

class PayrollVariablePluginForm(forms.ModelForm):
    module = PayrollVariablePluginField(widget=BinaryFileInput())

    class Meta:
        model = PayrollVariablePlugin
        fields = ('name', 'module', 'organization')

class PayrollVariablePluginAdmin(admin.ModelAdmin):
     form = PayrollVariablePluginForm

# admin.site.register(PayrollVariablePlugin, PayrollVariablePluginAdmin)


# User Voluntary Rebate Request

class UserVoluntaryRebateAdmin(ImportExportModelAdmin):
    search_fields = [
        'title',
        'rebate__title',
        'fiscal_year__name'
    ]
    list_display = (
        'title',
        'user',
        'fiscal_year'
    )
    list_filter = (
        'fiscal_year__name',
    )


admin.site.register(UserVoluntaryRebate, UserVoluntaryRebateAdmin)


class UserVoluntaryRebateDocumentAdmin(ImportExportModelAdmin):
    search_fields = [
        'file_name'
    ]
    list_display = (
        'user_voluntary_rebate',
        'file_name'
    )
    list_filter = (
        'user_voluntary_rebate__title',
    )


admin.site.register(UserVoluntaryRebateDocument, UserVoluntaryRebateDocumentAdmin)


admin.site.register(UserVoluntaryRebateAction, AdminFilterByDate)

admin.site.register(EmployeeMetricHeadingReportSetting)
