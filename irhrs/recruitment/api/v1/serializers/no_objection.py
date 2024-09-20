from django.conf import settings
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db import transaction
from django.db.models import Q, F, FloatField, Subquery, OuterRef
from django.db.models.functions import Cast
from django.template.loader import render_to_string
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.recruitment.constants import (
    ASSESSMENT_TAKEN, SHORTLISTED,
    INTERVIEWED, PENDING, SALARY_DECLARED, APPROVED
)
from irhrs.recruitment.models import (
    NoObjection,
    Job, JobApply,
    Template, SalaryDeclaration
)


class NoObjectionSerializer(DynamicFieldsModelSerializer):
    valid_stage_choices = (
        (SHORTLISTED, 'Shortlisted'),
        (INTERVIEWED, 'Interviewed'),
        (SALARY_DECLARED, 'Salary Declared'),
    )
    stage = serializers.ChoiceField(choices=valid_stage_choices)

    email_template = serializers.SlugRelatedField(
        queryset=Template.objects.all(),
        slug_field='slug'
    )
    report_template = serializers.SlugRelatedField(
        queryset=Template.objects.all(),
        slug_field='slug'
    )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['title'] = serializers.SerializerMethodField()
        return fields

    def create(self, validated_data):
        validated_data['job'] = self.context.get('job')
        with transaction.atomic():
            instance = super().create(validated_data)
            # Freeze candidates depend upon stages

            # async_task(
            #     post_no_objection_mapper[instance.stage],
            #     instance,
            #     validated_data
            # )
        return instance

    # @staticmethod
    # def process_post_screen_no_objection(instance, validated_data):
        # qs = JobApply.objects.filter(
        #     job=instance.job,
        #     post_screening__isnull=False,
        #     post_screening__verified=True
        # ).values(
        #     'applicant__user__full_name',
        #     'post_screening__score',
        #     'post_screening__data__category'
        # )
        # columns = {
        #     'Candidate Name': 'applicant__user__full_name',
        #     'Overall Evaluation Score': 'post_screening__score',
        #     'Category': 'post_screening__data__category',
        # }
        # wb = ExcelExport.process(
        #     qs,
        #     title='No objection of candidate',
        #     columns=columns
        # )
        # file_content = ContentFile(save_virtual_workbook(wb))
        # instance.file.save('shortlist_no_objection', file_content)
        # instance.save()
        # instance.send_mail()

    class Meta:
        model = NoObjection
        fields = '__all__'
        read_only_fields = ('is_verified', 'remarks', 'file', 'status')
        extra_kwargs = {
            'status': {
                'required': True
            },
            'modified_template': {
                'required': True
            }
        }

    @staticmethod
    def get_title(obj):
        if obj.job_apply:
            return f'No Objection for Salary Declaration of candidate {obj.job_apply.candidate_name}'
        return obj.title


class MemorandumJobApplySerializer(DynamicFieldsModelSerializer):
    job_title = serializers.ReadOnlyField()
    candidate_name = serializers.ReadOnlyField()

    duty_location = serializers.ReadOnlyField(source='job.location')
    residing_at = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    total_salary = serializers.SerializerMethodField()

    hr_score_percentage = serializers.SerializerMethodField()
    hr_score = serializers.SerializerMethodField()
    hr_category = serializers.ReadOnlyField()
    hiring_manager_score_percentage = serializers.SerializerMethodField()
    hiring_manager_score = serializers.SerializerMethodField()
    final_interview_score_percentage = serializers.ReadOnlyField()
    final_interview_score = serializers.ReadOnlyField()
    salary = serializers.ReadOnlyField()
    assessment_score_percentage = serializers.ReadOnlyField()
    pre_screening_interview_score_percentage = serializers.ReadOnlyField()
    rostered = serializers.SerializerMethodField()

    cv = serializers.ReadOnlyField(source='applicant.cv_path', allow_null=True)

    class Meta:
        model = JobApply
        fields = '__all__'

    @property
    def no_objection(self):
        return self.context.get('no_objection')

    def get_date(self, apply):
        if self.no_objection:
            return self.no_objection.created_at.strftime("%d %b %Y")
        return ''

    @staticmethod
    def get_residing_at(apply):
        return str(apply.applicant.address)

    def get_total_salary(self, apply):
        if self.no_objection:
            try:
                SalaryDeclaration.objects.get(
                    status=APPROVED,
                    job_apply=self.no_objection.job_apply
                ).salary
            except SalaryDeclaration.DoesNotExist:
                return 0
        return 0

    @staticmethod
    def get_rostered(apply):
        return bool(apply.data.get('rostered'))

    @staticmethod
    def get_hr_score_percentage(apply):
        return apply.hr_score_percentage or 0

    @staticmethod
    def get_hiring_manager_score_percentage(apply):
        return apply.hiring_manager_score_percentage or 0

    @staticmethod
    def get_hr_score(apply):
        return apply.hr_score or 0

    @staticmethod
    def get_hiring_manager_score(apply):
        return apply.hiring_manager_score or 0

    @staticmethod
    def get_hr_category(apply):
        return apply.hiring_manager_score or 0


class MemorandumSerializer(DynamicFieldsModelSerializer):
    # Job info
    job_title = serializers.ReadOnlyField(source='title.title')
    job_link = serializers.SerializerMethodField()
    total_applicants = serializers.ReadOnlyField(allow_null=True)
    no_of_vacancies = serializers.ReadOnlyField(source='vacancies')

    # Counts
    total_eliminated_initially = serializers.ReadOnlyField(allow_null=True)
    total_duplicate = serializers.ReadOnlyField(allow_null=True)
    applicants_after_removing_duplication_test_data = serializers.SerializerMethodField()
    applicants_not_meeting_minimum_requirements = serializers.SerializerMethodField()
    hr_shortlisted = serializers.ReadOnlyField(allow_null=True)
    hiring_manager_shortlisted = serializers.ReadOnlyField(allow_null=True)
    interview_completed = serializers.ReadOnlyField(allow_null=True)
    interview_absent = serializers.ReadOnlyField(allow_null=True)
    long_list_eligible_candidate = serializers.ReadOnlyField(allow_null=True)

    pre_screening_questions = serializers.SerializerMethodField()
    interview_absent_names = serializers.SerializerMethodField()
    backup_candidates_names = serializers.SerializerMethodField()
    interview_total_score = serializers.ReadOnlyField(allow_null=True)

    # Tables
    cv_scoring_criteria_table = serializers.SerializerMethodField()
    preliminary_shortlisted_candidate_table = serializers.SerializerMethodField()
    shortlisted_candidate_detail_table = serializers.SerializerMethodField()
    application_data_interpretation_table = serializers.SerializerMethodField()
    final_shortlist_by_hiring_manager_table = serializers.SerializerMethodField()
    written_assessment_and_pre_screening_interview_table = serializers.SerializerMethodField()
    final_structured_interview_table = serializers.SerializerMethodField()
    recommended_candidate_table = serializers.SerializerMethodField()
    salary_declaration_table = serializers.SerializerMethodField()

    written_score = serializers.SerializerMethodField()
    interview_score = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'job_title',
            'job_link',
            'total_applicants',
            'no_of_vacancies',

            'total_duplicate',
            'applicants_after_removing_duplication_test_data',
            'applicants_not_meeting_minimum_requirements',
            'total_eliminated_initially',
            'hr_shortlisted',
            'hiring_manager_shortlisted',
            'interview_completed',
            'interview_absent',
            'long_list_eligible_candidate',

            'pre_screening_questions',
            'interview_absent_names',
            'backup_candidates_names',
            'interview_total_score',

            'cv_scoring_criteria_table',
            'preliminary_shortlisted_candidate_table',
            'shortlisted_candidate_detail_table',
            'application_data_interpretation_table',
            'final_shortlist_by_hiring_manager_table',
            'written_assessment_and_pre_screening_interview_table',
            'final_structured_interview_table',
            'recommended_candidate_table',
            'salary_declaration_table',

            'written_score',
            'interview_score',
        ]

    @staticmethod
    def get_applicants_after_removing_duplication_test_data(job):
        try:
            return job.total_applicants - job.total_duplicate
        except TypeError:
            return 0

    @staticmethod
    def get_written_score(job):
        return job.hiring_info.get('written_score', 25)

    @staticmethod
    def get_interview_score(job):
        return job.hiring_info.get('interview_score', 75)

    @staticmethod
    def get_interview_absent_names(job):
        return job.applications.filter(
            Q(
                Q(pre_screening_interview__status=PENDING) |
                Q(assessment__status=PENDING) |
                Q(interview__status=PENDING)
            )
        ).distinct().values_list('data__candidate_name', flat=True)

    @staticmethod
    def get_backup_candidates_names(job):
        return job.applications.filter(data__rostered=True).distinct().values_list(
            'data__candidate_name', flat=True)

    @staticmethod
    def get_applicants_not_meeting_minimum_requirements(job):
        try:
            return job.total_eliminated_initially - job.total_duplicate
        except TypeError:
            return 0

    @staticmethod
    def get_job_link(job):
        frontend_base_url = getattr(settings, 'FRONTEND_URL')
        return f'{frontend_base_url}/careers'

    def get_salary_declaration_table(self, job):
        fields = ['candidate_name', 'salary']
        context = {
            'table': 'salary_declaration_table',
            'applicant_list': MemorandumJobApplySerializer(
                self.annotate_application_fields(
                    job.applications.filter(salary_declarations__verified=True),
                    fields
                ),
                fields=fields,
                many=True
            ).data
        }
        return self.render_html_to_string(context)

    def get_cv_scoring_criteria_table(self, job):
        context = {
            'table': 'cv_scoring_criteria_table',
        }
        return self.render_html_to_string(context)

    def get_recommended_candidate_table(self, job):
        fields = ['candidate_name']

        context = {
            'table': 'recommended_candidate_table',
            'applicant_list': MemorandumJobApplySerializer(
                self.annotate_application_fields(
                    job.applications.filter(
                        Q(status=ASSESSMENT_TAKEN) & Q(data__rostered__isnull=True)
                    ),
                    fields
                ),
                fields=fields,
                many=True
            ).data
        }
        return self.render_html_to_string(context)

    def get_final_structured_interview_table(self, job):
        fields = ['candidate_name', 'final_interview_score_percentage', 'rostered']

        context = {
            'table': 'final_structured_interview_table',
            'applicant_list': MemorandumJobApplySerializer(
                self.annotate_application_fields(
                    job.applications.filter(status=ASSESSMENT_TAKEN),
                    fields
                ),
                fields=fields,
                many=True
            ).data
        }
        return self.render_html_to_string(context)

    def get_written_assessment_and_pre_screening_interview_table(self, job):
        fields = [
            'candidate_name', 'pre_screening_interview_score_percentage',
            'assessment_score_percentage', 'assessment_score',
            'final_interview_score_percentage', 'final_interview_score'
        ]

        context = {
            'table': 'written_assessment_and_pre_screening_interview_table',
            'applicant_list': MemorandumJobApplySerializer(
                self.annotate_application_fields(
                    job.applications.filter(pre_screening_interview__isnull=False),
                    fields
                ),
                fields=fields,
                many=True
            ).data,
            'interview_score': self.get_interview_score(job),
            'written_score': self.get_written_score(job),
            'interview_total_score': job.interview_total_score
        }
        return self.render_html_to_string(context)

    def get_final_shortlist_by_hiring_manager_table(self, job):
        fields = ['candidate_name', 'hiring_manager_score']

        context = {
            'table': 'final_shortlist_by_hiring_manager_table',
            'applicant_list': MemorandumJobApplySerializer(
                self.annotate_application_fields(
                    job.applications.filter(post_screening__isnull=False),
                    fields
                ),
                fields=fields,
                many=True
            ).data
        }
        return self.render_html_to_string(context)

    def get_shortlisted_candidate_detail_table(self, job):
        fields = [
            'candidate_name', 'hr_category',
            'hr_score_percentage', 'hiring_manager_score_percentage',
            'cv'
        ]

        context = {
            'table': 'shortlisted_candidate_detail_table',
            'applicant_list': MemorandumJobApplySerializer(
                self.annotate_application_fields(
                    job.applications.filter(pre_screening__isnull=False),
                    fields
                ),
                fields=fields,
                many=True
            ).data
        }
        return self.render_html_to_string(context)

    def get_preliminary_shortlisted_candidate_table(self, job):
        fields = ['candidate_name', 'hr_score_percentage']

        context = {
            'table': 'preliminary_shortlisted_candidate',
            'applicant_list': MemorandumJobApplySerializer(
                self.annotate_application_fields(
                    job.applications.filter(pre_screening__isnull=False),
                    fields
                ),
                fields=fields,
                many=True
            ).data
        }
        return self.render_html_to_string(context)

    def get_application_data_interpretation_table(self, job):
        context = {
            'table': 'application_data_interpretation_table',
            'total_applicants': job.total_applicants,
            'hiring_manager_shortlisted': job.hiring_manager_shortlisted,
            'interview_completed': job.interview_completed,
            'long_list_eligible_candidate': job.long_list_eligible_candidate,
            'organization_name': job.organization.name
        }
        return self.render_html_to_string(context)

    def get_pre_screening_questions(self, job):
        context = {
            'pre_screening_questions': job.pre_screening_questions
        }
        return self.render_html_to_string(context)

    @staticmethod
    def render_html_to_string(context):
        return render_to_string(
            'memorandum_report.html',
            context=context
        ).replace('\n', '')

    @staticmethod
    def annotate_application_fields(apply_queryset, fields):
        annotated_fields = dict(
            hr_score=F('pre_screening__data__total_score'),
            hr_score_percentage=F('pre_screening__score'),
            hr_category=F('pre_screening__category'),
            hiring_manager_score=Cast(
                KeyTextTransform('given_score', 'post_screening__data'), FloatField()
            ),
            hiring_manager_score_percentage=F('post_screening__score'),
            assessment_score_percentage=F('assessment__score'),
            assessment_score=Cast(
                KeyTextTransform('total_score', 'assessment__data'), FloatField()
            ),
            pre_screening_interview_score_percentage=F(
                'pre_screening_interview__score'
            ),
            final_interview_score_percentage=F('interview__score'),
            final_interview_score=Cast(
                KeyTextTransform('given_score', 'interview__data'), FloatField()
            ),
            salary=Subquery(
                SalaryDeclaration.objects.filter(
                    job_apply=OuterRef('pk'), verified=True).values('salary')[:1]
            )
        )

        valid_fields = {
            k: v for k, v in annotated_fields.items() if k in fields
        }

        return apply_queryset.annotate(**valid_fields)
