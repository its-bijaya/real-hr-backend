from django.contrib import admin
from django.forms import ModelForm
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from irhrs.core.utils.admin.filter import (
    SearchByName, SearchByTitle, AdminFilterByStatus,
    AdminFilterByDate,
)
from rangefilter.filter import DateRangeFilter

from irhrs.hris.models.duty_station import DutyStationAssignment

from .models import ResultArea, CoreTask, UserResultArea
from .models.email_setting import *
from .models.exit_interview import *
from .models.id_card import *
from .models.onboarding_offboarding import *
from .models.resignation import *

from ..core.mixins.admin import ModelResourceMetaMixin, AdminNotRequiredFormMixin

# duty_station


class DutyStationAssignmentAdmin(admin.ModelAdmin):
    search_fields = [
        'duty_station__name',
        'user__first_name',
        'user__middle_name',
        'user__last_name'
    ]
    list_display = [
        'duty_station',
        'user',
        'organization'
    ]

    list_filter = [
        ('created_at', DateRangeFilter),
        'duty_station'
    ]


admin.site.register(DutyStationAssignment, DutyStationAssignmentAdmin)


admin.site.register([
    ResultArea, CoreTask, UserResultArea
])
# Email setting


class EmailSettingAdmin(admin.ModelAdmin):
    search_fields = [
        'user__first_name',
        'user__middle_name',
        'user__last_name'
    ]
    list_display = [
        'user',
        'leave',
        'created_at'
    ]
    list_filter = [
        ('created_at', DateRangeFilter),
        'leave'
    ]


admin.site.register(EmailSetting, EmailSettingAdmin)


class ExitInterviewResource(resources.ModelResource):
    class Meta(ModelResourceMetaMixin):
        model = ExitInterview


class ExitInterviewAdmin(ImportExportModelAdmin):
    resource_class = ExitInterviewResource
    search_fields = [
        'interviewer__first_name',
        'interviewer__middle_name',
        'interviewer__last_name',
        'question_set__name'
    ]
    list_display = (
        'question_set',
        'interviewer',
        'created_at'
    )
    list_filter = (
        ('created_at', DateRangeFilter),
    )


admin.site.register(ExitInterview, ExitInterviewAdmin)

# Exit interview Question Set


class ExitInterViewQuestionSetResource(resources.ModelResource):
    class Meta(ModelResourceMetaMixin):
        model = ExitInterviewQuestionSet


class ExitInterViewQuestionSetAdmin(ImportExportModelAdmin):
    resource_class = ExitInterViewQuestionSetResource
    search_fields = ('name', 'description')
    list_display = [
        'name',
        'description',
        'is_archived',

    ]
    list_filter = [
        'is_archived'
    ]


admin.site.register(ExitInterviewQuestionSet, ExitInterViewQuestionSetAdmin)

# Id card
admin.site.register(IdCardTemplate, SearchByName)


class IdCardAdmin(admin.ModelAdmin):
    search_fields = [
        'template__name',
        'user__first_name',
        'user__middle_name',
        'user__last_name'

    ]
    list_display = [
        'template',
        'user',
        'issued_on',
        'expire_on'
    ]
    list_filter = [
        ('issued_on', DateRangeFilter),
        ('expire_on', DateRangeFilter)
    ]


admin.site.register(IdCard, IdCardAdmin)


# Resignation
admin.site.register(UserResignation, AdminFilterByStatus)
admin.site.register(UserResignationApproval, AdminFilterByDate)
admin.site.register(HRApprovalUserResignation, AdminFilterByDate)
admin.site.register(ResignationApprovalSetting, AdminFilterByDate)
admin.site.register(UserResignationHistory, AdminFilterByDate)


# Onboarding Offboarding Models

""" Pre Employment """


class EmploymentSeparationResource(resources.ModelResource):
    class Meta(ModelResourceMetaMixin):
        model = EmployeeSeparation


class EmploymentSeparationAdminForm(AdminNotRequiredFormMixin):
    not_required_fields = [
        'parted_date', 'effective_date', 'release_date',
        'pre_task', 'post_task'
    ]

    class Meta(ModelResourceMetaMixin):
        model = EmployeeSeparation


class EmploymentSeparationAdmin(ImportExportModelAdmin):
    resource_class = EmploymentSeparationResource
    list_display = ['employee', 'separation_type', 'parted_date', 'effective_date',
                    'release_date', 'status', 'created_at', 'modified_at', ]
    form = EmploymentSeparationAdminForm
    list_filter = (
        ('created_at', DateRangeFilter),
        'status',
    )


admin.site.register(EmployeeSeparation, EmploymentSeparationAdmin)


class EmploymentSeparationTypeResource(resources.ModelResource):
    class Meta(ModelResourceMetaMixin):
        model = EmployeeSeparationType


class EmploymentSeparationTypeAdmin(ImportExportModelAdmin):
    resource_class = EmploymentSeparationTypeResource
    list_display = (
        'title', 'display_leave', 'display_payroll',
        'display_attendance_details', 'display_pending_tasks',
        'is_assigned', 'badge_visibility', 'category',
        'created_at', 'modified_at',
    )
    search_fields = ('title', )
    list_filter = (
        ('created_at', DateRangeFilter),
    )


admin.site.register(EmployeeSeparationType, EmploymentSeparationTypeAdmin)

# Others onboarding and offboarding models

admin.site.register(TaskTemplateTitle, SearchByName)
admin.site.register(TaskFromTemplate, SearchByTitle)
admin.site.register(TaskFromTemplateChecklist, SearchByTitle)
admin.site.register(LetterTemplate, SearchByTitle)
admin.site.register(PreEmployment, AdminFilterByStatus)
admin.site.register(ChangeType, SearchByTitle)
admin.site.register(EmploymentReview, AdminFilterByStatus)
admin.site.register(GeneratedLetter, AdminFilterByStatus)
admin.site.register(GeneratedLetterHistory, AdminFilterByStatus)
admin.site.register(StatusHistory, AdminFilterByStatus)
admin.site.register(LeaveChangeType, AdminFilterByDate)
admin.site.register(EmployeeChangeTypeDetail, AdminFilterByDate)
admin.site.register(TaskTemplateMapping, AdminFilterByDate)
admin.site.register(TaskFromTemplateAttachment, AdminFilterByDate)
admin.site.register(TaskFromTemplateResponsiblePerson, AdminFilterByDate)
admin.site.register(TaskTracking, AdminFilterByDate)


class LeaveEncashmentOnSeparationAdmin(admin.ModelAdmin):
    search_fields = [
        'separation__employee__first_name',
        'separation__employee__middle_name',
        'separation__employee__last_name',
        'separation__separation_type__title'
    ]
    list_display = [
        'separation',
        'encashment_balance',
        'created_at'
    ]
    list_filter = [
        ('created_at', DateRangeFilter)
    ]


admin.site.register(LeaveEncashmentOnSeparation,
                    LeaveEncashmentOnSeparationAdmin)


class LeaveEncashmentOnSeparationChangeHistoryAdmin(admin.ModelAdmin):
    search_fields = [
        'encashment__separation__separation_type__title'
    ]
    list_display = [
        'encashment',
        'actor'

    ]
    list_filter = [
        ('created_at', DateRangeFilter)
    ]


admin.site.register(LeaveEncashmentOnSeparationChangeHistory,
                    LeaveEncashmentOnSeparationChangeHistoryAdmin)
