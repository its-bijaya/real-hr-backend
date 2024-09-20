from django.db import transaction
from django.db.models import Prefetch, Q
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from django.db.models.functions import Lower
from irhrs.core.constants.user import REJECTED

from irhrs.core.mixins.viewset_mixins import (
    ListViewSetMixin
)
from irhrs.recruitment.api.v1.mixins import (
    HrAdminOrSelfQuerysetMixin,
    ApplicantProcessAnswerViewSetMixin, ApplicantProcessViewSetMixin
)
from irhrs.recruitment.api.v1.permissions import RecruitmentPermission
from irhrs.recruitment.api.v1.serializers.external_profile import ReferenceCheckerSerializer
from irhrs.recruitment.api.v1.serializers.interview import (
    ReferenceCheckSerializer,
    ReferenceCheckAnswerSerializer
)
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.recruitment.constants import (
    REFERENCE_VERIFIED,
    SALARY_DECLARED,
    SELECTED
)
from irhrs.recruitment.models import (
    ReferenceCheck,
    ReferenceCheckAnswer,
    ReferenceChecker,
)
from irhrs.recruitment.utils.stages import get_next_stage, get_stage_filters
from irhrs.recruitment.utils.util import raise_exception_if_job_apply_is_not_in_completed_step

from irhrs.recruitment.utils.stages import (
    ReferenceCheckStage
)

class ReferenceCheckViewSet(ApplicantProcessViewSetMixin):
    queryset = ReferenceCheck.objects.filter(
        job_apply__salary_declarations__isnull=True
    ).annotate(
        candidate_name=Lower("job_apply__applicant__user__full_name")
    ).exclude(
        job_apply__status__in=[
            REFERENCE_VERIFIED,
            SALARY_DECLARED,
            SELECTED,
            REJECTED
        ]
    )

    serializer_class = ReferenceCheckSerializer
    forwarded_qs = ReferenceCheck.objects.filter(
        job_apply__salary_declarations__isnull=False
    )

    no_objection_stage = SELECTED
    reverse_question_answer = "reference_check_question_answers"
    filter_backends = (FilterMapBackend, OrderingFilterMap)
    filter_map = {
        'candidate_name': 'job_apply__applicant__user__full_name',
        'scheduled_at': 'scheduled_at',
        'score': 'score'
    }
    ordering_fields_map = {
        'candidate_name': 'job_apply__applicant__user__full_name',
        'scheduled_at': 'scheduled_at',
        'score': 'score'
    }

    def get_stage_filters(self, is_null):
        return get_stage_filters(self.job, REFERENCE_VERIFIED, is_null)

    def get_queryset(self):
        status = self.request.query_params.get('status')
        if status == 'Forwarded':
            return self.get_forwarded_qs()

        qs = super().get_queryset().select_related(
            'job_apply__job__title', 'job_apply__applicant__user',
            'email_template'
        ).prefetch_related(
            Prefetch(
                'reference_check_question_answers',
                queryset=ReferenceCheckAnswer.objects.select_related(
                    'internal_reference_checker',
                    'external_reference_checker__user'
                )
            )
        ).annotate(
            candidate_name=Lower("job_apply__applicant__user__full_name")
        )
        job_slug = self.kwargs.get('job_slug')
        if job_slug:
            return qs.filter(job_apply__job__slug=job_slug)
        return qs

    def get_forwarded_qs(self):
        filters = self.get_stage_filters(is_null=False)
        qs = ReferenceCheck.objects.filter(**filters)
        next_stage = get_next_stage(self.job, REFERENCE_VERIFIED)
        if next_stage in [SELECTED, REJECTED]:
            qs = qs.filter(job_apply__status__in=[SELECTED, REJECTED])
        return qs


    @action(
        detail=False,
        methods=['post', ],
        url_path='forward',
        url_name='salary_declaration_forward',
    )
    def forward(self, request, *args, **kwargs):
        """
        Takes {categories: array, score: int}
        """
        raise_exception_if_job_apply_is_not_in_completed_step(ReferenceCheck, self.job)
        process = ReferenceCheckStage(
            data=request.data,
            job=self.job,
            current_stage=REFERENCE_VERIFIED
        )
        process.forward()
        return Response({'status': 'Forwarded'})


class ReferenceCheckAnswerViewSet(ApplicantProcessAnswerViewSetMixin):
    serializer_class = ReferenceCheckAnswerSerializer
    queryset = ReferenceCheckAnswer.objects.all()
    internal_user_field = 'internal_reference_checker'
    external_user_field = 'external_reference_checker'

    @staticmethod
    def get_user_object(uuid):
        return get_object_or_404(ReferenceChecker, uuid=uuid)


class ReferenceCheckerViewSet(HrAdminOrSelfQuerysetMixin, ListViewSetMixin):
    queryset = ReferenceChecker.objects.all()
    serializer_class = ReferenceCheckerSerializer
    filter_backends = (SearchFilter, )
    search_fields = ['user__name']
    permission_classes = [RecruitmentPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.kwargs.get('applicant_id'):
            qs = qs.filter(user__applicant=self.kwargs.get('applicant_id'))
        return qs
