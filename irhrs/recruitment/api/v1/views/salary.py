from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.db.models.functions import Lower

from irhrs.core.mixins.viewset_mixins import (
    RetrieveUpdateViewSetMixin,
    ListRetrieveUpdateViewSetMixin
)
from irhrs.recruitment.api.v1.mixins import (
    DynamicFieldViewSetMixin, HrAdminOrSelfQuerysetMixin,
    ExtraInfoApiMixin
)
from irhrs.recruitment.api.v1.permissions import RecruitmentPermission
from irhrs.recruitment.api.v1.serializers.salary import SalaryDeclarationSerializer
from irhrs.recruitment.constants import COMPLETED, DENIED, REJECTED, SELECTED, SALARY_DECLARED
from irhrs.recruitment.models import SalaryDeclaration, PENDING
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.recruitment.utils.stages import SalaryDeclarationStage


class SalaryDeclarationViewSet(
    ExtraInfoApiMixin,
    DynamicFieldViewSetMixin,
    ListRetrieveUpdateViewSetMixin,
    HrAdminOrSelfQuerysetMixin
):
    queryset = SalaryDeclaration.objects.select_related(
        'email_template',
        'job_apply__applicant__user'
    ).exclude(job_apply__status__in=[SALARY_DECLARED, SELECTED, REJECTED])
    serializer_class = SalaryDeclarationSerializer
    permission_classes = [RecruitmentPermission]
    filter_backends = (DjangoFilterBackend, FilterMapBackend, OrderingFilterMap)
    forwarded_qs = SalaryDeclaration.objects.select_related(
        'email_template',
        'job_apply__applicant__user'
    ).filter(job_apply__status__in=[SELECTED, SALARY_DECLARED]).annotate(
        candidate_name=Lower("job_apply__applicant__user__full_name")
    )
    filter_map = {
        'candidate_name': 'job_apply__applicant__user__full_name',
    }
    ordering_fields_map = {
        'candidate_name': 'candidate_name',
    }

    def get_serializer_include_fields(self):
        if self.action.lower() in ['update', 'partial_update']:
            return ['email_template', ]
        return super().get_serializer_include_fields()

    def get_queryset(self):
        qs = super().get_queryset().annotate(
            candidate_name=Lower("job_apply__applicant__user__full_name")
        )
        if self.kwargs.get('job_slug'):
            qs = qs.filter(job_apply__job__slug=self.kwargs.get('job_slug'))
        return qs

    @action(detail=True, methods=['POST'], url_name='complete', url_path='complete')
    def mark_as_complete(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.status == PENDING:
            raise ValidationError(_('Negotiation has not been verified by candidate.'))

        if obj.status == DENIED:
            raise ValidationError(_('Candidate has denied salary declaration.'))
        obj.verified = True
        obj.status = COMPLETED
        obj.save()
        return Response({'status': 'Completed'})

    @action(
        detail=False,
        methods=['post', ],
        url_path='forward',
        url_name='interview_forward',
        permission_classes=[RecruitmentPermission]
    )
    def forward(self, request, *args, **kwargs):
        """
        Takes {categories: array, score: int, assigned_to: int}
        and set post screening of those applicants who falls under
        these categories, score and assigned to none of the fields are mandatory
        """
        process = SalaryDeclarationStage(
            data=request.data,
            job=self.job,
            current_stage=SALARY_DECLARED
        )
        process.forward()
        return Response({'status': 'Forwarded'})


# For external user
class SalaryDeclarationApproveView(DynamicFieldViewSetMixin, RetrieveUpdateViewSetMixin):
    queryset = SalaryDeclaration.objects.filter(status=PENDING)
    serializer_class = SalaryDeclarationSerializer
    serializer_include_fields = [
        'status', 'candidate_remarks',
        'attachments', 'salary' ]
    permission_classes = []

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            job_apply__applicant__user__uuid=self.kwargs.get('user_id'),
            id=self.kwargs.get('declaration_id')
        )
