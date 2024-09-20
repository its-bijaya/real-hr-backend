from django.contrib import admin

# Register your models here.
from rangefilter.filter import DateRangeFilter

from irhrs.core.utils.admin.filter import AdminFilterByDate, AdminFilterByStatus, SearchByTitle
from .models.KAAR_question import KPIQuestion, KAARQuestionSet

from .models.appraiser_setting import Appraisal
from .models.form_design import PerformanceAppraisalFormDesign, \
    PerformanceAppraisalAnswerType, ResendPAForm
from .models.key_achievement_and_rating_pa import KeyAchievementAndRatingAppraisal, \
    KAARAppraiserConfig
from .models.kpi import IndividualKPI, ExtendedIndividualKPI
from .models.performance_appraisal import PerformanceAppraisalYear, \
    SubPerformanceAppraisalSlot, SubPerformanceAppraisalSlotMode, SubPerformanceAppraisalSlotWeight, SubPerformanceAppraisalYearWeight
from .models.performance_appraisal_setting import AppraisalSetting, \
    ExceptionalAppraiseeFilterSetting, ScoreAndScalingSetting, DeadlineExtendCondition, \
    DeadlineExceedScoreDeductionCondition, StepUpDownRecommendation, FormReviewSetting
from .models.question_set import PerformanceAppraisalQuestionSet, \
    QuestionSetUserType, PerformanceAppraisalQuestionSection

# appraiser_setting


class AppraisalAdmin(admin.ModelAdmin):
    search_fields = [
        'appraisee__first_name',
        'appraisee__middle_name',
        'appraisee__last_name'
    ]
    list_display = [
        'appraisee',
        'appraisal_type',
        'appraiser']
    list_filter = ['appraisal_type']


admin.site.register(Appraisal, AppraisalAdmin)


# form_design
admin.site.register(PerformanceAppraisalFormDesign, AdminFilterByDate)


class PerformanceAppraisalAnswerTypeAdmin(admin.ModelAdmin):

    list_display = [
        'form_design',
        'question_type',
        'answer_type',
        'created_at'
    ]
    list_filter = [('created_at', DateRangeFilter)]


admin.site.register(PerformanceAppraisalAnswerType,
                    PerformanceAppraisalAnswerTypeAdmin)
admin.site.register(ResendPAForm, AdminFilterByDate)

# performance_appraisal_setting


class AppraisalSettingAdmin(admin.ModelAdmin):
    search_fields = ['sub_performance_appraisal_slot__title']
    list_display = [
        'sub_performance_appraisal_slot',
        'duration_of_involvement',
        'duration_of_involvement_type'
    ]
    list_filter = [('created_at', DateRangeFilter),
                   'duration_of_involvement_type']


admin.site.register(AppraisalSetting, AppraisalSettingAdmin)


class ExceptionalAppraiseeFilterSettingAdmin(admin.ModelAdmin):
    search_fields = ['sub_performance_appraisal_slot__title']
    list_display = [
        'sub_performance_appraisal_slot',
        'appraisal_type',
        'created_at'
    ]
    list_filter = [('created_at', DateRangeFilter)]


admin.site.register(ExceptionalAppraiseeFilterSetting,
                    ExceptionalAppraiseeFilterSettingAdmin)


class ScoreAndScalingSettingAdmin(admin.ModelAdmin):
    search_fields = ['score', 'sub_performance_appraisal_slot__title']
    list_display = [
        'sub_performance_appraisal_slot',
        'name',
        'score'
    ]
    list_filter = ['score', ('created_at', DateRangeFilter)]


admin.site.register(ScoreAndScalingSetting, ScoreAndScalingSettingAdmin)


admin.site.register(DeadlineExtendCondition, AdminFilterByDate)


class DeadlineExceedScoreDeductionConditionAdmin(admin.ModelAdmin):
    search_fields = ['sub_performance_appraisal_slot__title']
    list_display = [
        'sub_performance_appraisal_slot',
        'deduction_type',
        'deduct_value'

    ]
    list_filter = [('created_at', DateRangeFilter)]


admin.site.register(DeadlineExceedScoreDeductionCondition,
                    DeadlineExceedScoreDeductionConditionAdmin)


class StepUpDownRecommendationAdmin(admin.ModelAdmin):
    search_fields = ['sub_performance_appraisal_slot__title']
    list_display = [
        'sub_performance_appraisal_slot',
        'score_acquired_from',
        'score_acquired_to']
    list_filter = [('created_at', DateRangeFilter)]


admin.site.register(StepUpDownRecommendation, StepUpDownRecommendationAdmin)


class FormReviewSettingAdmin(admin.ModelAdmin):

    search_fields = ['sub_performance_appraisal_slot__title']
    list_display = [
        'sub_performance_appraisal_slot',
        'viewable_appraisal_submitted_form_type',
        'can_hr_download_form']
    list_filter = ['can_hr_download_form']


admin.site.register(FormReviewSetting, FormReviewSettingAdmin)
# performance_appraisal


class PerformanceAppraisalYearAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'organization__name'
    ]
    list_display = [
        'name',
        'year',
        'organization'
    ]
    list_filter = [('year', DateRangeFilter)]


admin.site.register(PerformanceAppraisalYear, PerformanceAppraisalYearAdmin)


class SubPerformanceAppraisalSlotAdmin(admin.ModelAdmin):
    search_fields = ['title']
    list_display = [
        'title',
        'weightage',
        'from_date',
        'to_date'
    ]
    list_filter = ['from_date', 'to_date']


admin.site.register(SubPerformanceAppraisalSlot,
                    SubPerformanceAppraisalSlotAdmin)


class SubPerformanceAppraisalSlotModeAdmin(admin.ModelAdmin):
    search_fields = ['sub_performance_appraisal_slot__title', 'weightage']
    list_display = ['sub_performance_appraisal_slot',
                    'appraisal_type', 'weightage']
    list_filter = ['appraisal_type']


admin.site.register(SubPerformanceAppraisalSlotMode,
                    SubPerformanceAppraisalSlotModeAdmin)


class SubPerformanceAppraisalSlotWeightAdmin(admin.ModelAdmin):
    search_fields = [
        'appraiser__first_name',
        'appraiser__middle_name',
        'appraiser__last_name'
    ]
    list_display = [
        'appraiser',
        'sub_performance_appraisal_slot',
        'percentage'
    ]
    list_filter = [
        ('created_at', DateRangeFilter)
    ]


admin.site.register(SubPerformanceAppraisalSlotWeight,
                    SubPerformanceAppraisalSlotWeightAdmin)


class SubPerformanceAppraisalYearWeightAdmin(admin.ModelAdmin):
    search_fields = [
        'appraiser__first_name',
        'appraiser__middle_name',
        'appraiser__last_name',
    ]
    list_display = ('appraiser', 'performance_appraisal_year', 'percentage')


admin.site.register(SubPerformanceAppraisalYearWeight,
                    SubPerformanceAppraisalYearWeightAdmin)
# question_set
admin.site.register(PerformanceAppraisalQuestionSection, SearchByTitle)


class PerformanceAppraisalQuestionSetAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'description'
    ]
    list_display = [

        'name',
        'description',
        'organization'
    ]
    list_filter = [
        'name',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(PerformanceAppraisalQuestionSet,
                    PerformanceAppraisalQuestionSetAdmin)

admin.site.register(QuestionSetUserType, AdminFilterByDate)


class IndividualKPIAdmin(admin.ModelAdmin):
    search_fields = [
        'title',
        'user__first_name',
        'user__middle_name',
        'user__last_name'
    ]
    list_display = [
        'title',
        'user',
        'fiscal_year'
    ]
    list_filter = [
        'is_archived',
        'status',
        'fiscal_year',
    ]


admin.site.register(IndividualKPI, IndividualKPIAdmin)


class ExtendedIndividualKPIAdmin(admin.ModelAdmin):
    search_fields = ['individual_kpi__title', 'individual_kpi__user__first_name',
                     'individual_kpi__user__middle_name', 'individual_kpi__user__last_name']
    list_display = ['individual_kpi', 'weightage']
    list_filter = [
        'individual_kpi__status',
        'individual_kpi__is_archived',
        'individual_kpi__fiscal_year'
    ]


admin.site.register(ExtendedIndividualKPI, ExtendedIndividualKPIAdmin)


class KeyAchievementAndRatingAppraisalAdmin(admin.ModelAdmin):
    search_fields = [
        'appraisee__first_name',
        'appraisee__middle_name',
        'appraisee__last_name',
    ]
    list_display = ('appraisee', 'sub_performance_appraisal_slot', 'status')
    list_filter = ['status']


admin.site.register(KeyAchievementAndRatingAppraisal, KeyAchievementAndRatingAppraisalAdmin)


class KAARAppraiserConfigAdmin(admin.ModelAdmin):
    search_fields = [
        'appraiser__first_name',
        'appraiser__middle_name',
        'appraiser__last_name',
    ]
    list_display = ('appraiser', 'kaar_appraisal', 'question_status', 'appraiser_type')
    list_filter = ['appraiser_type', 'question_status']


admin.site.register(KAARAppraiserConfig, KAARAppraiserConfigAdmin)


class KAARQuestionSetAdmin(admin.ModelAdmin):
    search_fields = [
        'kaar_appraisal__appraisee__first_name',
        'kaar_appraisal__appraisee__middle_name',
        'kaar_appraisal__appraisee__last_name',
    ]
    list_display = ('name', 'kaar_appraisal', 'question_type')
    list_filter = ['question_type', 'is_archived']


admin.site.register(KAARQuestionSet, KAARQuestionSetAdmin)


class KPIQuestionAdmin(admin.ModelAdmin):
    search_fields = [
        'extended_individual_kpi__individual_kpi__title',
        'question_set__kaar_appraisal__appraisee__first_name',
        'question_set__kaar_appraisal__appraisee__middle_name',
        'question_set__kaar_appraisal__appraisee__last_name'
    ]
    list_display = ('question_set', 'extended_individual_kpi')


admin.site.register(KPIQuestion, KPIQuestionAdmin)

