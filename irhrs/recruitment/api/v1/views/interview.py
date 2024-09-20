from django.db.models import Prefetch
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from django.db.models.functions import Lower
from irhrs.core.constants.user import REJECTED

from irhrs.recruitment.api.v1.mixins import (
    ApplicantProcessViewSetMixin, ApplicantProcessAnswerViewSetMixin
)
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.recruitment.api.v1.permissions import RecruitmentPermission
from irhrs.recruitment.api.v1.serializers.interview import (
    InterviewSerializer,
    InterViewAnswerSerializer)
from irhrs.recruitment.constants import (INTERVIEWED, SELECTED)
from irhrs.recruitment.models import (
    External,
    Interview,
    InterViewAnswer,
    JobApply)

from irhrs.recruitment.utils.stages import (
    RecruitmentProcess,
    get_stage_filters,
    get_next_stage
)

class InterviewViewSet(ApplicantProcessViewSetMixin):
    queryset = Interview.objects.filter(
        job_apply__reference_check__isnull=True
    )
    serializer_class = InterviewSerializer
    forwarded_qs = Interview.objects.filter(
        job_apply__reference_check__isnull=False
    ).annotate(
        candidate_name=Lower("job_apply__applicant__user__full_name")
    )
    no_objection_stage = INTERVIEWED
    reverse_question_answer = "interview_question_answers"
    filter_backends = (FilterMapBackend, OrderingFilterMap)
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
        return get_stage_filters(self.job, INTERVIEWED, is_null)

    def get_queryset(self):
        status = self.request.query_params.get('status')
        if status == 'Forwarded':
            return self.get_forwarded_qs()

        filters = self.get_stage_filters(is_null=True)
        qs = Interview.objects.filter(**filters).exclude(
            job_apply__status__in=[SELECTED, REJECTED]
        )
        qs = qs.select_related(
            'job_apply__job__title', 'job_apply__applicant__user'
        ).prefetch_related(
            Prefetch(
                'interview_question_answers',
                queryset=InterViewAnswer.objects.select_related(
                    'internal_interviewer',
                    'external_interviewer__user'
                )
            )
        ).filter(job_apply__salary_declarations__isnull=True).annotate(
            candidate_name=Lower("job_apply__applicant__user__full_name")
        )
        job_slug = self.kwargs.get('job_slug')
        if job_slug:
            return qs.filter(job_apply__job__slug=job_slug)
        return qs
    
    def get_forwarded_qs(self):
        filters = self.get_stage_filters(is_null=False)
        next_stage = get_next_stage(self.job, INTERVIEWED)
        qs = Interview.objects.filter(**filters)
        if next_stage in [SELECTED, REJECTED]: 
            qs = qs.filter(job_apply__status__in=[SELECTED, REJECTED])
        return qs

    def get_serializer_include_fields(self):
        if self.request.method.upper() == 'POST':
            return ['job_apply', ]
        if self.request.method.lower() in ['PUT', 'PATCH']:
            return ['scheduled_at', 'question_set', 'location', 'email_template']
        return super().get_serializer_include_fields()

    @action(
        detail=False,
        methods=['post', ],
        url_path='forward',
        url_name='interview_forward',
        permission_classes=[RecruitmentPermission]
    )
    def forward(self, request, *args, **kwargs):
        process = RecruitmentProcess(
            data=request.data,
            job=self.job,
            current_stage=INTERVIEWED
        )
        process.forward()
        return Response({'status': 'Forwarded'})

    @action(
        detail=True,
        methods=['POST'],
        url_name='rostered_set',
        url_path='set-as-rostered',
        permission_classes=[RecruitmentPermission]
    )
    def set_as_rostered(self, request, *args, **kwargs):
        obj = self.get_object()
        apply_obj = JobApply.objects.get(id=obj.job_apply.id)
        apply_obj.data['rostered'] = True
        apply_obj.save()
        return Response({'status': 'Rostered'})

    @action(
        detail=True,
        methods=['POST'],
        url_name='rostered_remove',
        url_path='remove-from-rostered',
        permission_classes=[RecruitmentPermission]
    )
    def remove_from_rostered(self, request, *args, **kwargs):
        obj = self.get_object()
        apply_obj = JobApply.objects.get(id=obj.job_apply.id)
        try:
            del apply_obj.data['rostered']
            apply_obj.save()
        except KeyError:
            raise ValidationError({
                "non_field_errors": ["Applicant is not in rostered state"]
            })
        return Response({'status': 'Remove from rostered'})


class InterViewAnswerViewSet(ApplicantProcessAnswerViewSetMixin):
    serializer_class = InterViewAnswerSerializer
    queryset = InterViewAnswer.objects.all()
    internal_user_field = 'internal_interviewer'
    external_user_field = 'external_interviewer'

    @staticmethod
    def get_user_object(uuid):
        return get_object_or_404(External, user__uuid=uuid)
