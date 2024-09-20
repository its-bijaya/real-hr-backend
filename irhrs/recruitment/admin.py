from django.contrib import admin

from irhrs.recruitment.models.applicant import ApplicantEducation
from irhrs.recruitment.models.common import AbstractSocialAccount, JobCategory, Language, Salary, Template
from irhrs.recruitment.models.external_profile import External, ExternalDocument, ReferenceChecker
from irhrs.recruitment.models.job import Job, JobAttachment, JobQuestion, JobSetting
from irhrs.recruitment.models.job_apply import Assessment, AssessmentAnswer, InterViewAnswer, \
    Interview, JobApply, JobApplyStage, JobApplyStageStatus, JobQuestionAnswer, NoObjection, \
    PostScreening, PreScreeningInterview, PreScreeningInterviewAnswer, ReferenceCheckAnswer, SalaryDeclaration
from irhrs.recruitment.models.location import City, Country, District, Province
from irhrs.recruitment.models.question import QuestionSet, \
    RecruitmentQuestionSection, RecruitmentQuestions
from irhrs.recruitment.report import Question
from .models import Applicant, ApplicantReference, \
    ApplicantWorkExperience, ApplicantAttachment, PreScreening, \
    Location, JobBenefit

from irhrs.core.utils.admin.filter import (
    SearchByTitle, AdminFilterByStatus, SearchByName,
    SearchByNameAndFilterByStatus, SearchByTitleAndFilterByStatus, AdminFilterByDate
)
from rangefilter.filter import DateRangeFilter

# Applicant


class ApplicantAdmin(admin.ModelAdmin):

    search_fields = [
        'user__full_name'
    ]
    list_display = [
        'user',
        'address',
        'education_degree',
        'experience_years'
    ]

    list_filter = [
        'education_degree'
    ]


admin.site.register(Applicant, ApplicantAdmin)


class ApplicantReferenceAdmin(admin.ModelAdmin):
    search_fields = [
        'applicant__user__full_name'
    ]
    list_display = [
        'applicant',
        'created_at',
        'modified_at'
    ]

    list_filter = [
        ('created_at', DateRangeFilter)
    ]


admin.site.register(ApplicantReference, ApplicantReferenceAdmin)


class ApplicantWorkExperienceAdmin(admin.ModelAdmin):
    search_fields = [
        'applicant__user__full_name',
        'designation'
    ]
    list_display = [
        'applicant',
        'org_name',
        'designation',
        'is_archived'
    ]
    list_filter = [
        'is_archived',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(ApplicantWorkExperience, ApplicantWorkExperienceAdmin)


class ApplicantEducationAdmin(admin.ModelAdmin):
    search_fields = [
        'applicant__user__full_name',
        'program'
    ]
    list_display = [
        'applicant',
        'degree',
        'program'
    ]
    list_filter = [
        'degree'
    ]


admin.site.register(ApplicantEducation, ApplicantEducationAdmin)


class ApplicantAttachmentAdmin(admin.ModelAdmin):

    search_fields = [
        'applicant__user__full_name',
        'name'
    ]
    list_display = [
        'applicant',
        'name',
        'type',
        'is_archived'
    ]

    list_filter = [
        'is_archived',
        'type'

    ]


admin.site.register(ApplicantAttachment, ApplicantAttachmentAdmin)


# Common
class LocationAdmin(admin.ModelAdmin):
    exclude = ('latitude', 'longitude')
    search_fields = ('city_name', )
    list_display = (
        'city_name',
        'address',
        'created_at',
        'status',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'status',
        'country'
    )


admin.site.register(Location, LocationAdmin)


class JobBenefitAdmin(admin.ModelAdmin):
    search_fields = [
        'name'
    ]
    list_display = [
        'name',
        'status',
        'created_at'
    ]
    list_filter = [
        'status',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(JobBenefit, JobBenefitAdmin)

admin.site.register(JobCategory, SearchByName)
admin.site.register(Salary, AdminFilterByDate)
admin.site.register(Language, SearchByNameAndFilterByStatus)
# admin.site.register(Question, SearchByName)
admin.site.register(Template, SearchByTitle)


# External profile
admin.site.register(External, AdminFilterByDate)


class ExternalDocumentAdmin(admin.ModelAdmin):
    search_fields = [
        'title',
        'user__user__full_name'
    ]
    list_display = [
        'title',
        'user',
        'category',
        'is_archived'
    ]
    list_filter = [
        'category',
        'is_archived'
    ]


admin.site.register(ExternalDocument, ExternalDocumentAdmin)


class ReferenceCheckerAdmin(admin.ModelAdmin):

    list_display = [
        'user',
        'uuid',
        'created_at'
    ]
    list_filter = [
        ('created_at', DateRangeFilter)
    ]


admin.site.register(ReferenceChecker, ReferenceCheckerAdmin)

# Job apply


class JobApplyAdmin(admin.ModelAdmin):

    search_fields = [
        'applicant__user__full_name',
        'job__title__title'
    ]
    list_display = [
        'applicant',
        'job',
        'status',
        'created_at'
    ]
    list_filter = [
        'status',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(JobApply, JobApplyAdmin)
admin.site.register(JobQuestionAnswer, AdminFilterByDate)
admin.site.register(JobApplyStage, AdminFilterByStatus)


class JobApplyStageStatusAdmin(admin.ModelAdmin):
    list_display = [
        'stage',
        'on_hold',
        'remarks',
        'created_at'
    ]
    list_filter = [
        ('created_at', DateRangeFilter),
        'on_hold'
    ]


admin.site.register(JobApplyStageStatus, JobApplyStageStatusAdmin)
admin.site.register(NoObjection, SearchByTitleAndFilterByStatus)


class SalaryDeclarationAdmin(admin.ModelAdmin):

    search_fields = [
        'job_apply__job__title__title'
    ]
    list_display = [
        'job_apply',
        'salary',
        'score',
        'status',
        'created_at'

    ]
    list_filter = [
        'status',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(SalaryDeclaration, SalaryDeclarationAdmin)


class PreScreeningAdmin(admin.ModelAdmin):

    search_fields = [
        'job_apply__job__title__title',
        'responsible_person__first_name',
        'responsible_person__middle_name',
        'responsible_person__last_name'

    ]
    list_display = [
        'job_apply',
        'responsible_person',
        'question_set',

    ]
    list_filter = [
        'question_set'
    ]


admin.site.register(PreScreening, PreScreeningAdmin)


class PostScreeningAdmin(admin.ModelAdmin):
    search_fields = [
        'job_apply__job__title__title',
        'responsible_person__first_name',
        'responsible_person__middle_name',
        'responsible_person__last_name'
    ]
    list_display = [
        'job_apply',
        'responsible_person',
        'question_set'
    ]
    list_filter = [
        'question_set'
    ]


admin.site.register(PostScreening, PostScreeningAdmin)


class PreScreeningInterviewAdmin(admin.ModelAdmin):
    search_fields = [
        'job_apply__job__title__title',
        'responsible_person__first_name',
        'responsible_person__middle_name',
        'responsible_person__last_name'
    ]
    list_display = [
        'job_apply',
        'responsible_person',
        'question_set'
    ]
    list_filter = [
        'question_set'
    ]


admin.site.register(PreScreeningInterview, PreScreeningInterviewAdmin)


class PreScreeningInterviewAnswerAdmin(admin.ModelAdmin):
    search_fields = [
        'pre_screening_interview__job_apply__job__title__title'
    ]
    list_display = [
        'pre_screening_interview',
        'internal_interviewer',
        'created_at'

    ]
    list_filter = [
        ('created_at', DateRangeFilter)
    ]


admin.site.register(PreScreeningInterviewAnswer,
                    PreScreeningInterviewAnswerAdmin)


class AssessmentAdmin(admin.ModelAdmin):
    search_fields = [
        'job_apply__job__title__title',
        'responsible_person__first_name',
        'responsible_person__middle_name',
        'responsible_person__last_name'
    ]
    list_display = [
        'job_apply',
        'responsible_person',
        'question_set'
    ]
    list_filter = [
        'question_set'
    ]


admin.site.register(Assessment, AssessmentAdmin)


class AssessmentAnswerAdmin(admin.ModelAdmin):
    search_fields = [
        'assessment__job_apply__job__title__title'
    ]
    list_display = [
        'assessment',
        'internal_assessment_verifier',
        'created_at'
    ]
    list_filter = [
        ('created_at', DateRangeFilter)
    ]


admin.site.register(AssessmentAnswer, AssessmentAnswerAdmin)


class InterviewAdmin(admin.ModelAdmin):
    search_fields = [
        'job_apply__job__title__title'
    ]
    list_display = [
        'job_apply',
        'question_set',
        'created_at'
    ]
    list_filter = [
        ('created_at', DateRangeFilter),
        'question_set'
    ]


admin.site.register(Interview, InterviewAdmin)


class InterviewAnswerAdmin(admin.ModelAdmin):

    list_display = [
        'interview',
        'internal_interviewer',
        'created_at'
    ]
    list_filter = [
        ('created_at', DateRangeFilter)
    ]


admin.site.register(InterViewAnswer, InterviewAnswerAdmin)

admin.site.register(ReferenceCheckAnswer, AdminFilterByStatus)

# Job


class JobAdmin(admin.ModelAdmin):
    search_fields = [
        'title__title',
        'organization__name'
    ]
    list_display = [
        'title',
        'organization',
        'branch',
        'employment_status'
    ]
    list_filter = [
        'branch',
        'employment_status'
    ]


admin.site.register(Job, JobAdmin)


class JobSettingAdmin(admin.ModelAdmin):
    search_fields = [
        'job__title__title'
    ]
    list_display = [
        'job',
        'is_gender_specific',
        'is_experience_required'
    ]
    list_filter = [
        'is_experience_required',
        'is_gender_specific',
        'gender'
    ]


admin.site.register(JobSetting, JobSettingAdmin)


class JobQuestionAdmin(admin.ModelAdmin):
    list_display = [
        'job',
        'question',
        'created_at'
    ]
    list_filter = [

        ('created_at', DateRangeFilter)
    ]


admin.site.register(JobQuestion, JobQuestionAdmin)


class JobAttachmentAdmin(admin.ModelAdmin):
    search_fields = [
        'name'
    ]
    list_display = [
        'name',
        'attachment',
        'job',
        'created_at'

    ]

    list_filter = [
        'is_archived',
        ('created_at', DateRangeFilter)
    ]


admin.site.register(JobAttachment, JobAttachmentAdmin)

# Location
admin.site.register(Country, SearchByName)
admin.site.register(Province, SearchByName)
admin.site.register(District, SearchByName)


class CityAdmin(admin.ModelAdmin):
    exclude = ('latitude', 'longitude', 'relevance')
    search_fields = ('name', )
    list_display = (
        '__str__',
        'created_at',
        'modified_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
    )


admin.site.register(City, CityAdmin)


# Question
admin.site.register(QuestionSet, SearchByName)


class RecruitmentQuestionsAdmin(admin.ModelAdmin):

    search_fields = [
        'question__title'
    ]
    list_display = [
        'is_mandatory',
        'question'

    ]

    list_filter = [

        'is_mandatory'
    ]


admin.site.register(RecruitmentQuestions, RecruitmentQuestionsAdmin)


class RecruitmentQuestionSectionAdmin(admin.ModelAdmin):
    search_fields = [
        'title'
    ]
    list_display = [
        'title',
        'created_at'
    ]
    list_filter = [
        ('created_at', DateRangeFilter)
    ]


admin.site.register(RecruitmentQuestionSection,
                    RecruitmentQuestionSectionAdmin)
