from django.db.models import Q, Prefetch
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from irhrs.core.mixins.viewset_mixins import (
    HRSModelViewSet,
    RetrieveViewSetMixin,
    CreateViewSetMixin)
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.recruitment.api.v1.mixins import RecruitmentOrganizationMixin, \
    RecruitmentPermissionMixin, DynamicFieldViewSetMixin
from irhrs.recruitment.api.v1.permissions import RecruitmentPermission
from irhrs.recruitment.api.v1.serializers.applicant import (
    ApplicantDetailSerializer,
    ApplicantReferenceSerializer,
    ApplicantWorkExperienceSerializer,
    ApplicantCVSerializer,
    ApplicantOnBoardSerializer,
)

from irhrs.recruitment.constants import SELECTED, JOB_APPLY
from irhrs.recruitment.models import (
    Applicant,
    ApplicantReference,
    ApplicantWorkExperience, JobApply, ApplicantAttachment
)


class ApplicantProfileViewSetMixin:

    applicant_id_url_kwarg = 'applicant_uuid'

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.applicant

    def get_applicant_queryset(self):
        return Applicant.objects.filter(user__is_archived=False)

    @cached_property
    def applicant(self):
        """
        :return: applicant instance for given jobseeker id
        :raise Http404: If invalid applicant id is passed
        """
        applicant_id = self.kwargs.get(self.applicant_id_url_kwarg)
        if applicant_id is not None:
            return get_object_or_404(
                self.get_applicant_queryset(),
                uuid=applicant_id
            )
        return None


class ApplicantCommonViewSetMixin(ApplicantProfileViewSetMixin):
    applicant_lookup_field = 'applicant'

    def get_queryset(self):
        return super().get_queryset().filter(
            **{
                '{}'.format(self.applicant_lookup_field): self.applicant
            }
        )

    def get_serializer_context(self):
        """
        Updates context to include Applicant instance as `applicant`
        """
        ctx = super().get_serializer_context()
        ctx["applicant"] = self.applicant
        return ctx


class ApplicantViewSet(RecruitmentOrganizationMixin, ReadOnlyModelViewSet):
    queryset = Applicant.objects.all()
    serializer_class = ApplicantDetailSerializer
    permission_classes = [RecruitmentPermission]


class ApplicantReferenceViewSet(
    RecruitmentOrganizationMixin,
    ApplicantCommonViewSetMixin,
    ReadOnlyModelViewSet
):
    queryset = ApplicantReference
    serializer_class = ApplicantReferenceSerializer
    permission_classes = [RecruitmentPermission]


class ApplicantWorkExperienceViewSet(
    RecruitmentOrganizationMixin,
    ApplicantCommonViewSetMixin,
    ReadOnlyModelViewSet
):
    queryset = ApplicantWorkExperience
    serializer_class = ApplicantWorkExperienceSerializer
    permission_classes = [RecruitmentPermission]


class ApplicantCVViewSet(
    RecruitmentPermissionMixin,
    RetrieveViewSetMixin
):
    queryset = Applicant.objects.select_related(
        'user', 'address',
        'expected_salary'
    ).prefetch_related(
        'skills', 'references',
        'work_experiences', 'educations',
        Prefetch(
            'attachments',
            queryset=ApplicantAttachment.objects.filter(
                is_archived=False,
                type=JOB_APPLY
            )
        )
    )
    serializer_class = ApplicantCVSerializer
    permission_classes = []

    def get_permission_classes(self):
        """
        :return: Override recruitment get permission classes
        """
        return self.permission_classes

    def check_permissions(self, request):
        if self.request.user.is_anonymous and not self.request.query_params.get('viewer_id'):
            self.permission_denied(request, 'Viewer Id is required for anonymous user')
        super().check_permissions(request)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_authenticated:
            if not self.is_hr_admin:  # ( or self.is_audit_user):
                user = self.request.user
                qs = qs.filter(
                    Q(applied_job__pre_screening__responsible_person=user) |
                    Q(applied_job__post_screening__responsible_person=user) |
                    Q(applied_job__pre_screening_interview__pre_screening_interview_question_answers__internal_interviewer=user) |
                    Q(applied_job__assessment__assessment_question_answers__internal_assessment_verifier=user) |
                    Q(applied_job__interview__interview_question_answers__internal_interviewer=user) |
                    Q(applied_job__reference_check__reference_check_question_answers__internal_reference_checker=user)
                )
        else:
            viewer_id = self.request.query_params.get('viewer_id')
            qs = qs.filter(
                Q(applied_job__pre_screening_interview__pre_screening_interview_question_answers__external_interviewer__user__uuid=viewer_id) |
                Q(applied_job__assessment__assessment_question_answers__external_assessment_verifier__user__uuid=viewer_id) |
                Q(applied_job__interview__interview_question_answers__external_interviewer__user__uuid=viewer_id) |
                Q(applied_job__reference_check__reference_check_question_answers__external_reference_checker__uuid=viewer_id)
            )
        return qs.distinct()


class ApplicantOnBoardViewSet(
    DynamicFieldViewSetMixin,
    RecruitmentOrganizationMixin,
    ReadOnlyModelViewSet,
):
    queryset = JobApply.objects.filter(status=SELECTED).select_related(
        'job__branch', 'job__employment_level', 'job__employment_status',
        'job__title', 'job__division', 'applicant__address'
    )
    serializer_class = ApplicantOnBoardSerializer
    permission_classes = [RecruitmentPermission]

    def get_serializer_include_fields(self):
        if self.action and self.action.lower() == 'list':
            return ['full_name_with_job', 'full_name', 'id']
        return super().get_serializer_include_fields()

    def get_queryset(self):
        return super().get_queryset().filter(
            job__organization=self.organization
        )

    @action(detail=True, methods=['post'], url_path='onboard', url_name='onboard')
    def onboard(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.data['onboard'] = True
        obj.save()
        return Response({'status': 'On Board'})
