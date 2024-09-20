from django.db.models import Count, Prefetch, Case, When, Value, \
    IntegerField, Q, Subquery, OuterRef
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models.functions import Lower
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap

from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import (
    CreateViewSetMixin,
    UpdateViewSetMixin,
    ListViewSetMixin
)
from irhrs.recruitment.api.v1.filterset_classes import ApplicationShortlistFilter
from irhrs.recruitment.api.v1.mixins import DynamicFieldViewSetMixin, RecruitmentOrganizationMixin
from irhrs.recruitment.api.v1.permissions import RecruitmentPermission
from irhrs.recruitment.api.v1.serializers.job_apply import (
    JobApplyCreateSerializer,
    JobApplyStatusChangeSerializer,
    ApplicationShortlistDetailSerializer,
    EligibleCandidateSerializer, RejectedCandidateSerializer)
from irhrs.recruitment.constants import (
    APPLIED, SCREENED,
    SHORTLISTED,
    INTERVIEWED,
    REJECTED,
    SELECTED,
    REFERENCE_VERIFIED, ASSESSMENT_TAKEN, PENDING, COMPLETED, SALARY_DECLARED)
from irhrs.recruitment.models import (
    JobApply,
    Job,
    Applicant,
    JobApplyStage, SalaryDeclaration, NoObjection
)
from irhrs.recruitment.utils.stages import display_name_mapper


class JobApplyCreateViewSet(CreateViewSetMixin):
    queryset = JobApply.objects.all()
    serializer_class = JobApplyCreateSerializer
    permission_classes = []  # it is public api

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        recaptcha_token = self.request.query_params.get('recaptcha_token')
        ctx['recaptcha_token'] = recaptcha_token
        job_slug = self.kwargs.get('job_slug')
        if job_slug is not None:
            job = get_object_or_404(
                Job.get_qs(),
                slug=self.kwargs.get('job_slug')
            )
            ctx['job'] = job
        return ctx


class InternalJobApplyCreateViewSet(CreateViewSetMixin):
    queryset = JobApply.objects.all()
    serializer_class = JobApplyCreateSerializer
    permission_classes = [IsAuthenticated, ]  # it is public api

    def get_serializer_context(self):
        ctx = super().get_serializer_context()

        job_slug = self.kwargs.get('job_slug')
        if job_slug is not None:
            job = get_object_or_404(
                Job.get_qs(is_internal=True),
                slug=self.kwargs.get('job_slug')
            )
            ctx['job'] = job
        return ctx


class JobApplicationShortlistViewSet(
    RecruitmentOrganizationMixin,
    DynamicFieldViewSetMixin,
    UpdateViewSetMixin,
    ListViewSetMixin
):
    queryset = JobApply.objects.all()
    serializer_class = ApplicationShortlistDetailSerializer
    permission_classes = [RecruitmentPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = (
        'applicant__user__full_name',
        'applicant__user__email',
        'applicant__user__phone_number'
    )
    filter_fields = ('status',)
    ordering_fields = ()
    filterset_class = ApplicationShortlistFilter

    def get_queryset(self):

        fil = dict()
        job_slug = self.kwargs.get('job_slug')
        if job_slug:
            fil.update({'job__slug': job_slug})

        qs = JobApply.objects.all().select_related(
            'job__title',
        ).prefetch_related(
            'pre_screening',
            'answer',
            Prefetch(
                'applicant',
                queryset=Applicant.objects.select_related(
                    'user', 'expected_salary', 'address'
                ).prefetch_related('skills')
            ),
            Prefetch(
                'apply_stages',
                queryset=JobApplyStage.objects.all()
            )
        ).filter(**fil).annotate(
            weight=Case(
                When(status=REJECTED, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            ),
            remarks=Subquery(
                JobApplyStage.objects.filter(
                    job_apply=OuterRef('pk')
                ).order_by('-created_at').values('remarks')[:1]
            )
        ).order_by('weight', '-modified_at')
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if self.job:
            response.data['stages'] = [
                display_name_mapper[stage] for stage in self.job.stages
                if stage not in [APPLIED, SELECTED, REJECTED]
            ]
        return response

    def update(self, request, *args, **kwargs):
        apply_instance = self.get_object()
        status = self.request.data.get('status')
        if status != REJECTED:
            raise ValidationError(_('Only rejected status is supported.'))

        ser = JobApplyStatusChangeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(job_apply=apply_instance)
        apply_instance.status = status
        apply_instance.save()
        JobApplyStage.objects.create(
            job_apply=apply_instance, status=REJECTED)
        return Response(data=ser.data)

    @action(
        methods=['GET'],
        detail=False,
        url_path='stat',
        url_name='stat'
    )
    def get_stats(self, request, *args, **kwargs):
        stat = {
            APPLIED: Count('id', distinct=True),
            'preliminary_shortlisted': Count(
                'id', filter=Q(pre_screening__verified=True), distinct=True),
            'final_shortlisted': Count(
                'id', filter=Q(post_screening__verified=True), distinct=True),
            'preliminary_interviewed': Count(
                'id', filter=Q(pre_screening_interview__verified=True), distinct=True),
            ASSESSMENT_TAKEN: Count(
                'id', filter=Q(assessment__verified=True), distinct=True),
            INTERVIEWED: Count(
                'id', filter=Q(interview__verified=True), distinct=True),
            REFERENCE_VERIFIED: Count(
                'id', filter=Q(reference_check__verified=True), distinct=True),
            'salary_declared': Count(
                'id', filter=Q(status=SALARY_DECLARED), distinct=True),
            SELECTED: Count(
                'id', filter=Q(status=SELECTED), distinct=True),
            REJECTED: Count(
                'id',
                filter=Q(
                    Q(status=REJECTED)
                ),
                distinct=True
            ),
            'duplicate': Count(
                'id',
                filter=Q(data__duplicate=True),
                distinct=True
            )
        }

        stats = dict()
        if self.job:
            stats = JobApply.objects.filter(job=self.job).aggregate(**stat)
            stats['job_title'] = self.job.title.title
        return Response(stats)

    @action(
        methods=['GET'],
        detail=False,
        url_path='pending-stat',
        url_name='pending-stat'
    )
    def get_pending_stats(self, request, *args, **kwargs):
        stat = {
            'preliminary_shortlisted': Count(
                'id', filter=Q(pre_screening__status=PENDING), distinct=True),
            'final_shortlisted': Count(
                'id', filter=Q(post_screening__status=PENDING), distinct=True),
            'preliminary_interviewed': Count(
                'id', filter=Q(pre_screening_interview__status=PENDING), distinct=True),
            ASSESSMENT_TAKEN: Count(
                'id', filter=Q(assessment__status=PENDING), distinct=True),
            INTERVIEWED: Count(
                'id', filter=Q(interview__status=PENDING), distinct=True),
            REFERENCE_VERIFIED: Count(
                'id', filter=Q(reference_check__status=PENDING), distinct=True),
            'salary_declared': Count(
                'id', filter=Q(salary_declarations__status=PENDING), distinct=True),
        }
        stats = dict()
        if self.job:
            stats = JobApply.objects.filter(job=self.job).aggregate(**stat)
            stats['no_objection'] = NoObjection.objects.filter(
                job=self.job, status=COMPLETED, verified=False).count()
        return Response(stats)

    @action(
        detail=True,
        methods=['post'],
        url_name='mark_as_duplicate',
        url_path='mark-as-duplicate'
    )
    def mark_as_duplicate(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status == REJECTED:
            raise ValidationError(_('Applicant is already rejected'))
        obj.remarks = 'Duplicate Candidate'
        obj.data['duplicate'] = True
        obj.status = REJECTED
        obj.save()
        JobApplyStage.objects.create(
            job_apply=obj, status=REJECTED)
        return Response({'status': 'Success'})

    @property
    def job(self):
        if self.kwargs.get('job_slug'):
            return get_object_or_404(Job, slug=self.kwargs.get('job_slug'))
        return None


class ApplicationVerificationViewSet(CreateViewSetMixin):
    queryset = JobApply.objects.all()
    serializer_class = DummySerializer
    permission_classes = []

    def create(self, request, *args, **kwargs):
        uuid = request.data.get('uuid')

        data = {
            'applied': False
        }
        if uuid:
            from django.core.exceptions import ValidationError
            try:
                applied_job = JobApply.objects.filter(applicant__user__uuid=uuid).first()
                if applied_job:
                    data['applied'] = True
                    data['job_title'] = applied_job.job_title
            except ValidationError:
                pass
        return Response(data=data)


class EligibleCandidateViewSet(
    RecruitmentOrganizationMixin,
    ListViewSetMixin
):
    queryset = JobApply.objects.filter(status__in=[SALARY_DECLARED, SELECTED]).annotate(
        candidates_name=Lower("applicant__user__full_name")
    )
    serializer_class = EligibleCandidateSerializer
    permission_classes = [RecruitmentPermission]
    filter_fields = ['status']
    _job = None
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        FilterMapBackend,
        OrderingFilterMap,
    ]
    filter_map = {
        'candidate_name': 'applicant__user__full_name',
    }
    ordering_fields_map = {
        'candidate_name': 'candidates_name',
    }

    @action(detail=False, url_name='extra_info', url_path='extra-info')
    def get_extra_info(self, request, *args, **kwargs):
        stat = self.get_queryset().aggregate(
            salary_declared=Count('id', filter=Q(status=SALARY_DECLARED)),
            selected=Count('id', filter=Q(status=SELECTED)),
            total=Count('id')
        )
        return Response(stat)

    def get_queryset(self):
        qs = JobApply.objects.filter(
            apply_stages__status__in=[SALARY_DECLARED, SELECTED]
        ).annotate(
            candidates_name=Lower("applicant__user__full_name")
        ).distinct()

        if self.job:
            return qs.filter(job=self.job)
        return qs

    @action(detail=True, methods=['post'], url_name='send_email', url_path='send-mail')
    def send_mail(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.data.get('confirmation_email_sent'):
            obj.send_selected_mail()
            obj.data['confirmation_email_sent'] = True
            obj.save()
        return Response()

    @action(detail=True, methods=['post'], url_name='select', url_path='select')
    def select(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status != SALARY_DECLARED:
            raise ValidationError(_('Candidate should be in salary declared state.'))

        obj.status = SELECTED
        JobApplyStage.objects.create(job_apply=obj, status=SELECTED)
        obj.save()
        return Response()

    @action(detail=True, methods=['post'], url_name='reject', url_path='reject')
    def reject(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status != SALARY_DECLARED:
            raise ValidationError(_('Candidate should be in salary declared state.'))

        obj.status = REJECTED
        JobApplyStage.objects.create(job_apply=obj, status=REJECTED)
        obj.save()
        return Response()

    @property
    def job(self):
        if not self._job:
            self._job = get_object_or_404(Job, slug=self.kwargs.get('job_slug'))
        return self._job


class RejectedCandidateViewSet(
    RecruitmentOrganizationMixin,
    ListViewSetMixin
):
    queryset = JobApply.objects.filter(status=REJECTED).annotate(
        candidates_name=Lower("applicant__user__full_name")
    )
    serializer_class = RejectedCandidateSerializer
    permission_classes = [RecruitmentPermission]
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
        FilterMapBackend,
        OrderingFilterMap,
    ]
    filter_map = {
        'candidate_name': 'applicant__user__full_name',
    }
    ordering_fields_map = {
        'candidate_name': 'candidates_name',
    }

    def get_queryset(self):
        job_slug = self.kwargs.get('job_slug')
        if job_slug:
            return super().get_queryset().filter(job__slug=job_slug)
        return super().get_queryset()

    @action(detail=False, methods=['post'], url_name='send_email', url_path='send-mail')
    def send_mail(self, request, *args, **kwargs):
        rejected_candidate = self.get_queryset().exclude(
            data__rejected_email_sent__isnull=False,
            data__rejected_email_sent=True
        )
        if not  rejected_candidate.exists():
            raise ValidationError("No employee to send email.")

        for apply in rejected_candidate:
            apply.send_rejected_mail()
            apply.data['rejected_email_sent'] = True
            apply.save()
        return Response()
