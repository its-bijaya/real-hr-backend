from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.query import Prefetch
from django.template.defaultfilters import striptags
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import ListCreateViewSetMixin, \
    ListRetrieveUpdateViewSetMixin
from irhrs.core.utils import nested_get
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.notification.utils import add_notification
from irhrs.permission.constants.permissions import OVERALL_RECRUITMENT_PERMISSION
from irhrs.recruitment.api.v1.mixins import (
    DynamicFieldViewSetMixin,
    HrAdminOrSelfQuerysetMixin,
    ExtraInfoApiMixin, ApplicantFreezeMixin, RecruitmentPermissionMixin,
    RecruitmentOrganizationMixin, ApplicantProcessViewSetMixin, ApplicantProcessAnswerViewSetMixin)
from irhrs.recruitment.api.v1.permissions import RecruitmentPermission
from irhrs.recruitment.api.v1.serializers.job_apply import ApplicationShortlistDetailSerializer
from irhrs.recruitment.api.v1.serializers.screening_assessment import (
    PreScreeningSerializer,
    PostScreeningSerializer,
    PreScreeningInterviewSerializer,
    AssessmentSerializer, PreScreeningInterviewAnswerSerializer, AssessmentAnswerSerializer
)
from irhrs.recruitment.constants import (
    APPLIED, SCREENED, COMPLETED, SELECTED, SHORTLISTED,
    PRE_SCREENING_INTERVIEWED, ASSESSMENT_TAKEN,
    REJECTED, INTERVIEWED)
from irhrs.recruitment.models import (
    PreScreening,
    PostScreening,
    Job, JobApply,
    JobApplyStage, PreScreeningInterview,
    Assessment,
    NoObjection,
    ReferenceCheck, ReferenceChecker, PreScreeningInterviewAnswer, External,
    AssessmentAnswer, RecruitmentQuestions
)
from irhrs.recruitment.utils.stages import (
    ApplicantInitialization,
    PreScreeningStage,
    RecruitmentProcess,
    get_next_stage,
    get_stage_filters,
)
from irhrs.recruitment.utils.util import get_no_objection_info, \
    raise_exception_if_job_apply_is_not_in_completed_step
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from django.db.models.functions import Lower

USER = get_user_model()


class ApplicantInitialProcessMixin(
    ApplicantFreezeMixin,
    ExtraInfoApiMixin,
    RecruitmentPermissionMixin,
    HrAdminOrSelfQuerysetMixin,
    DynamicFieldViewSetMixin,
    ListRetrieveUpdateViewSetMixin,
):
    filter_backends = [DjangoFilterBackend,
                       SearchFilter,
                       OrderingFilter,
                       FilterMapBackend,
                       OrderingFilterMap, ]
    ordering_fields = ('scheduled_at', 'score')
    permission_classes = [IsAuthenticated, ]
    user_field = 'responsible_person'
    filter_map = {
        'candidate_name': 'job_apply__applicant__user__full_name',
        'scheduled_at': 'scheduled_at',
        'score': 'score'
    }
    ordering_fields_map = {
        'candidate_name': 'candidate_name',
        'scheduled_at': 'scheduled_at',
        'score': 'score'
    }

    def check_permissions(self, request):
        if self.action == 'create':
            self.permission_denied(request, 'Create action is not valid')
        super().check_permissions(request)

    def get_queryset(self):
        assert self.queryset is not None
        status = self.request.query_params.get('status')
        if status == 'Forwarded' and self.forwarded_qs is not None:
            self.queryset = self.forwarded_qs

        queryset = super().get_queryset().annotate(
            candidate_name=Lower("job_apply__applicant__user__full_name")
        )
        queryset = queryset.filter(job_apply__job=self.job)
        if not self.is_hr_admin:  # ( or self.is_audit_user):
            queryset = queryset.exclude(status=COMPLETED).filter(
                responsible_person=self.request.user
            )
        return queryset.select_related(
            'responsible_person', 'question_set', 'job_apply__job__title'
        ).order_by('-score')

    @action(
        detail=True,
        methods=['POST'],
        url_name='complete',
        url_path='complete',
        permission_classes=[RecruitmentPermission]
    )
    def mark_as_complete(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.data is None or obj.score is None:
            raise ValidationError(_('Applicant score has not been filled.'))
        obj.verified = True
        obj.status = COMPLETED
        obj.save()
        return Response({'status': 'Completed'})

    @action(
        detail=False,
        url_name='question-answers',
        url_path='question-answers',
        permission_classes=[RecruitmentPermission]
    )
    def question_answers_list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response({
            'data': [
                obj.completed_question_answer_list() for obj in queryset
            ]
        })

    @property
    def job(self):
        if not self._job and self.kwargs.get('job_slug'):
            self._job = get_object_or_404(Job, slug=self.kwargs.get('job_slug'))
        return self._job


class PreScreeningViewSet(
    BackgroundExcelExportMixin,
    ApplicantInitialProcessMixin
):
    queryset = PreScreening.objects.filter(
        job_apply__post_screening__isnull=True
    ).select_related(
        'responsible_person', 'question_set'
    ).distinct()
    serializer_class = PreScreeningSerializer
    forwarded_qs = PreScreening.objects.filter(
        job_apply__post_screening__isnull=False
    ).annotate(
        candidate_name=Lower("job_apply__applicant__user__full_name")
    )
    no_objection_stage = SHORTLISTED
    # *************** Report Section *******************
    filter_backends = [OrderingFilterMap]
    ordering_fields_map = {
        'candidate_name': 'job_apply__applicant__user__full_name',
    }
    notification_permissions = [OVERALL_RECRUITMENT_PERMISSION]

    def get_stage_filters(self, is_null):
        return get_stage_filters(self.job, SCREENED, is_null)

    def get_queryset(self):
        status = self.request.query_params.get('status')
        if status == 'Forwarded':
            return self.get_forwarded_qs()

        filters = self.get_stage_filters(is_null=True)
        return PreScreening.objects.filter(**filters).select_related(
            'responsible_person', 'question_set'
        ).exclude(job_apply__status__in=[SELECTED, REJECTED]).distinct()

    def get_forwarded_qs(self):
        filters = self.get_stage_filters(is_null=False)
        qs = PreScreening.objects.filter(**filters).select_related(
            'responsible_person', 'question_set'
        ).distinct()
        next_stage = get_next_stage(self.job, SCREENED)
        if next_stage in [SELECTED, REJECTED]:
            qs = qs.filter(job_apply__status__in=[SELECTED, REJECTED])
        return qs

    @cached_property
    def questions(self):
        question_set_id = nested_get(self.job.hiring_info or {}, 'pre_screening.id')
        questions = []
        if question_set_id:
            questions = RecruitmentQuestions.objects.filter(
                question_section__question_set=question_set_id
            ).distinct().values_list(
                'question__title',
                'question__id'
            )
        return questions

    def get_export_type(self):
        return f'Preliminary Shortlisting'

    def get_extra_export_data(self):
        ctx = super().get_extra_export_data()
        ctx['prepare_export_object_context'] = {'questions': self.questions}
        return ctx

    def get_export_data(self):
        return PreScreening.objects.filter(job_apply__job=self.job)

    @staticmethod
    def prepare_export_object(obj, **kwargs):

        extracted_data = PreScreening.extract_question_answer(obj)

        def get_score(q):
            question_answers = extracted_data.get('question_answers', list())
            if question_answers:
                question = list(filter(lambda x: x.get('id') == q, question_answers))
                if question:
                    return question[0].get('score', 0)
            return None

        def get_status():
            if obj.job_apply.status == REJECTED:
                return REJECTED
            else:
                return obj.status

        def get_remarks():
            if obj.job_apply.status == REJECTED:
                stage_obj = obj.job_apply.apply_stages.filter(status=REJECTED).first()
                if stage_obj:
                    return stage_obj.remarks
                return 'N/A'
            else:
                return striptags(extracted_data.get('remarks', 'N/A'))

        questions = kwargs.get('questions', [])
        if questions:
            [setattr(obj, f"score_of_{q_pk}", get_score(q_pk)) for _, q_pk in questions]

        setattr(
            obj,
            'total_score',
            extracted_data.get('total_score', 0)
        )

        setattr(
            obj,
            'total_score_percentage',
            extracted_data.get('percentage', 0)
        )

        setattr(
            obj,
            'apply_status',
            get_status()
        )

        setattr(
            obj,
            'hr_remarks',
            get_remarks()
        )

        return obj

    def get_export_fields(self):

        return {
            'S.N.': '#SN',
            'Name': 'job_apply.candidate_name',
            'Address': 'job_apply.candidate_address',
            'Recent Position': 'job_apply.recent_position',
            'Recent Organization': 'job_apply.recent_organization',
            **{
                striptags(title): f"score_of_{q_pk}" for title, q_pk in self.questions
            },
            'Total': 'total_score',
            '% Score': 'total_score_percentage',
            'Status': 'apply_status',
            'Hr Comments': 'hr_remarks',
        }

    def get_frontend_redirect_url(self):
        return f'/admin/{self.organization.slug}/recruitment/application-list'

    # *************** Report Section End *******************

    @action(
        detail=False,
        methods=['post', ],
        url_path='forward',
        url_name='post_screening_forward',
        permission_classes=[RecruitmentPermission]
    )
    def forward_to_post_screening(self, request, *args, **kwargs):
        """
        Takes {categories: array, score: int, assigned_to: int}
        and set post screening of those applicants who falls under
        these categories, score and assigned to none of the fields are mandatory
        """
        process = PreScreeningStage(
            data=self.request.data,
            job=self.job,
            current_stage=SCREENED
        )
        process.forward()
        return Response({'status': 'Forwarded'})

    @staticmethod
    def send_success_email(new_instances):
        for instance in new_instances:
            instance.send_mail()

    @action(
        detail=False,
        methods=['post', ],
        url_path='initialize',
        url_name='initialize',
        permission_classes=[RecruitmentPermission]
    )
    def forward(self, request, *args, **kwargs):
        raise_exception_if_job_apply_is_not_in_completed_step(
            PreScreening, self.job
        )
        process = ApplicantInitialization(
            data=self.request.data,
            job=self.job,
            current_stage=APPLIED
        )
        process.forward()
        return Response({'status': 'Forwarded'})


class PostScreeningViewSet(ApplicantInitialProcessMixin):
    queryset = PostScreening.objects.filter(
        job_apply__pre_screening_interview__isnull=True
    )
    serializer_class = PostScreeningSerializer
    forwarded_qs = PostScreening.objects.filter(
        job_apply__pre_screening_interview__isnull=False
    ).annotate(
        candidate_name=Lower("job_apply__applicant__user__full_name")
    )
    no_objection_stage = SHORTLISTED
    filter_backends = [OrderingFilterMap]
    ordering_fields_map = {
        'candidate_name': 'job_apply__applicant__user__full_name',
    }

    def get_stage_filters(self, is_null):
        return get_stage_filters(self.job, SHORTLISTED, is_null)

    def get_queryset(self):
        status = self.request.query_params.get('status')
        if status == 'Forwarded':
            return self.get_forwarded_qs()

        filters = self.get_stage_filters(is_null=True)
        return PostScreening.objects.filter(**filters).exclude(
            job_apply__status__in=[SELECTED, REJECTED]
        )

    def get_forwarded_qs(self):
        filters = self.get_stage_filters(is_null=False)
        qs = PostScreening.objects.filter(**filters).annotate(
            candidate_name=Lower("job_apply__applicant__user__full_name")
        )
        next_stage = get_next_stage(self.job, SHORTLISTED)
        if next_stage in [SELECTED, REJECTED]:
            qs = qs.filter(job_apply__status__in=[SELECTED, REJECTED])
        return qs

    @staticmethod
    def get_additional_info(job):
        return {
            'requested_by': UserThinSerializer(instance=job.created_by).data,
            'no_objection': get_no_objection_info(SHORTLISTED, job)
        }

    @action(
        detail=False,
        methods=['post', ],
        url_path='forward',
        url_name='pre_screening_interview_forward',
        permission_classes=[RecruitmentPermission]
    )
    def forward(self, request, *args, **kwargs):
        raise_exception_if_job_apply_is_not_in_completed_step(
            PostScreening, self.job
        )
        process = RecruitmentProcess(
            data=self.request.data,
            job=self.job,
            current_stage=SHORTLISTED
        )
        process.forward()
        return Response({'status': 'Forwarded'})

    @staticmethod
    def send_success_email(new_instances):
        for instance in new_instances:
            instance.send_mail()


class PreScreeningInterviewViewSet(ApplicantProcessViewSetMixin):
    queryset = PreScreeningInterview.objects.filter(
        job_apply__assessment__isnull=True
    ).annotate(
        candidate_name=Lower("job_apply__applicant__user__full_name")
    )
    serializer_class = PreScreeningInterviewSerializer
    forwarded_qs = PreScreeningInterview.objects.filter(
        job_apply__assessment__isnull=False
    ).annotate(
        candidate_name=Lower("job_apply__applicant__user__full_name")
    )
    no_objection_stage = INTERVIEWED
    reverse_question_answer = "pre_screening_interview_question_answers"
    filter_backends = [DjangoFilterBackend,
                       SearchFilter,
                       OrderingFilter,
                       FilterMapBackend,
                       OrderingFilterMap, ]
    filter_map = {
        'candidate_name': 'job_apply__applicant__user__full_name',
        'scheduled_at': 'scheduled_at',
        'score': 'score'
    }
    ordering_fields_map = {
        'candidate_name': 'candidate_name',
        'scheduled_at': 'scheduled_at',
        'score': 'score'
    }

    def get_stage_filters(self, is_null):
        return get_stage_filters(self.job, PRE_SCREENING_INTERVIEWED, is_null)

    def get_queryset(self):
        status = self.request.query_params.get('status')
        if status == 'Forwarded':
            return self.get_forwarded_qs()

        filters = self.get_stage_filters(is_null=True)
        qs = PreScreeningInterview.objects.filter(**filters).exclude(
            job_apply__status__in=[SELECTED, REJECTED]
        )
        qs = qs.annotate(
            candidate_name=Lower("job_apply__applicant__user__full_name")
        )
        qs = qs.select_related(
            'job_apply__job__title', 'job_apply__applicant__user',
            'email_template'
        ).prefetch_related(
            Prefetch(
                'pre_screening_interview_question_answers',
                queryset=PreScreeningInterviewAnswer.objects.select_related(
                    'internal_interviewer',
                    'external_interviewer__user'
                )
            )
        )
        job_slug = self.kwargs.get('job_slug')
        if job_slug:
            return qs.filter(job_apply__job__slug=job_slug)
        return qs.order_by('-score')

    def get_forwarded_qs(self):
        filters = self.get_stage_filters(is_null=False)
        next_stage = get_next_stage(self.job, PRE_SCREENING_INTERVIEWED)
        qs = PreScreeningInterview.objects.filter(**filters).annotate(
            candidate_name=Lower("job_apply__applicant__user__full_name")
        )
        if next_stage in [SELECTED, REJECTED]:
            qs = qs.filter(job_apply__status__in=[SELECTED, REJECTED])
        return qs

    def get_serializer_include_fields(self):
        if self.request.method.lower() in ['PUT', 'PATCH']:
            return ['scheduled_at', 'question_set', 'location', 'email_template']
        return super().get_serializer_include_fields()

    @action(
        detail=False,
        methods=['post', ],
        url_path='forward',
        url_name='assessment_forward',
        permission_classes=[RecruitmentPermission]
    )
    def forward(self, request, *args, **kwargs):
        """
        Takes {categories: array, score: int, assigned_to: int}
        and set post screening of those applicants who falls under
        these categories, score and assigned to none of the fields are mandatory
        """
        raise_exception_if_job_apply_is_not_in_completed_step(
            PreScreeningInterview, self.job
        )
        process = RecruitmentProcess(
            data=self.request.data,
            job=self.job,
            current_stage=PRE_SCREENING_INTERVIEWED
        )
        process.forward()
        return Response({'status': 'Forwarded'})

    @staticmethod
    def send_success_email(new_instances):
        for instance in new_instances:
            instance.send_mail()


class PreScreeningInterviewViewAnswerViewSet(ApplicantProcessAnswerViewSetMixin):
    queryset = PreScreeningInterviewAnswer.objects.all()
    serializer_class = PreScreeningInterviewAnswerSerializer
    internal_user_field = 'internal_interviewer'
    external_user_field = 'external_interviewer'

    @staticmethod
    def get_user_object(uuid):
        return get_object_or_404(External, user__uuid=uuid)


class AssessmentViewSet(ApplicantProcessViewSetMixin):
    queryset = Assessment.objects.filter(
        job_apply__interview__isnull=True
    )
    serializer_class = AssessmentSerializer
    forwarded_qs = Assessment.objects.filter(
        job_apply__interview__isnull=False
    ).annotate(
        candidate_name=Lower("job_apply__applicant__user__full_name")
    )
    no_objection_stage = INTERVIEWED
    reverse_question_answer = "assessment_question_answers"
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        FilterMapBackend,
        OrderingFilterMap,
    ]
    filter_map = {
        'candidate_name': 'job_apply__applicant__user__full_name',
        'scheduled_at': 'scheduled_at',
        'score': 'score'
    }
    ordering_fields_map = {
        'candidate_name': 'candidate_name',
        'scheduled_at': 'scheduled_at',
        'score': 'score'
    }

    def get_stage_filters(self, is_null):
        return get_stage_filters(self.job, ASSESSMENT_TAKEN, is_null)

    def get_queryset(self):
        status = self.request.query_params.get('status')
        if status == 'Forwarded':
            return self.get_forwarded_qs()

        filters = self.get_stage_filters(is_null=True)
        qs = Assessment.objects.filter(**filters).exclude(
            job_apply__status__in=[SELECTED, REJECTED]
        )
        qs = qs.annotate(
            candidate_name=Lower("job_apply__applicant__user__full_name")
        )
        qs = qs.select_related(
            'job_apply__job__title', 'job_apply__applicant__user',
            'email_template'
        ).prefetch_related(
            Prefetch(
                'assessment_question_answers',
                queryset=AssessmentAnswer.objects.select_related(
                    'internal_assessment_verifier',
                    'external_assessment_verifier'
                )
            )
        )
        job_slug = self.kwargs.get('job_slug')
        if job_slug:
            return qs.filter(job_apply__job__slug=job_slug)
        return qs.order_by('-score')

    def get_forwarded_qs(self):
        filters = self.get_stage_filters(is_null=False)
        qs = Assessment.objects.filter(**filters)
        next_stage = get_next_stage(self.job, ASSESSMENT_TAKEN)
        if next_stage in [SELECTED, REJECTED]:
            qs = qs.filter(job_apply__status__in=[SELECTED, REJECTED])
        return qs

    @action(
        detail=False,
        methods=['post', ],
        url_path='forward',
        url_name='interview_forward',
        permission_classes=[RecruitmentPermission]
    )
    def forward(self, request, *args, **kwargs):
        raise_exception_if_job_apply_is_not_in_completed_step(
            Assessment, self.job
        )
        process = RecruitmentProcess(
            data=self.request.data,
            job=self.job,
            current_stage=ASSESSMENT_TAKEN
        )
        process.forward()
        return Response({'status': 'Forwarded'})

    @staticmethod
    def send_success_email(new_instances):
        for instance in new_instances:
            instance.send_mail()


class AssessmentAnswerViewSet(ApplicantProcessAnswerViewSetMixin):
    queryset = AssessmentAnswer.objects.all()
    serializer_class = AssessmentAnswerSerializer
    internal_user_field = 'internal_assessment_verifier'
    external_user_field = 'external_assessment_verifier'

    @staticmethod
    def get_user_object(uuid):
        return get_object_or_404(External, user__uuid=uuid)


class RosteredViewSet(
    RecruitmentOrganizationMixin,
    DynamicFieldViewSetMixin,
    ListCreateViewSetMixin,
):
    queryset = JobApply.objects.filter(data__rostered=True).filter(
        status=ASSESSMENT_TAKEN
    ).select_related('applicant__user')
    serializer_class = ApplicationShortlistDetailSerializer
    permission_classes = [RecruitmentPermission, ]
    serializer_exclude_fields = [
        'skills', 'answer', 'education_degree',
        'experience'
    ]
    _job = None

    def check_permissions(self, request):
        if self.action == 'create':
            self.permission_denied(request)
        super().check_permissions(request)

    def get_queryset(self):
        job_slug = self.kwargs.get('job_slug')

        qs = super().get_queryset()
        if job_slug:
            qs = qs.filter(job__slug=job_slug)
        return qs

    @action(
        detail=True,
        methods=['post', ],
        url_path='forward',
        url_name='reference_check_forward',
        permission_classes=[RecruitmentPermission]
    )
    def forward_to_reference_check(self, request, *args, **kwargs):
        no_objection = NoObjection.objects.filter(
            stage=INTERVIEWED,
            job=self.job
        ).order_by('-created_at').first()

        if no_objection and no_objection.verified:
            apply_obj = self.get_object()

            if apply_obj.status == INTERVIEWED:
                raise ValidationError(
                    {"non_field_errors": ["Candidate is already forwarded."]})

            with transaction.atomic():
                if self.job.hiring_info and self.job.hiring_info.get('reference_check_letter'):
                    letter = {
                        'email_template_id': self.job.hiring_info.get(
                            'reference_check_letter').get('id')
                    }

                apply_obj.status = INTERVIEWED
                JobApplyStage.objects.create(status=INTERVIEWED, job_apply=apply_obj)
                apply_obj.save()

                instance = ReferenceCheck.objects.create(
                    job_apply=apply_obj,
                    **letter
                )

                if letter:
                    transaction.on_commit(lambda: instance.send_mail())

                ReferenceChecker.objects.bulk_create([
                    ReferenceChecker(
                        user=reference_checker
                    ) for reference_checker in apply_obj.applicant.references.all()
                ], ignore_conflicts=True)

            return Response({'status': 'Forwarded'})

        else:
            raise ValidationError(
                {"non_field_errors": ["No Objection has not been verified yet."]})

    @property
    def job(self):
        if not self._job:
            self._job = get_object_or_404(Job, slug=self.kwargs.get('job_slug'))
        return self._job
