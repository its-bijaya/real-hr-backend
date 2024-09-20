from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import HRSModelViewSet
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.permission.constants.permissions import OVERALL_RECRUITMENT_PERMISSION
from irhrs.permission.permission_classes import permission_factory
from irhrs.recruitment.api.v1.mixins import RecruitmentOrganizationMixin
from irhrs.recruitment.api.v1.permissions import RecruitmentPermission
from irhrs.recruitment.api.v1.serializers.common import TemplateSerializer
from irhrs.recruitment.constants import (
    NO_OBJECTION_LETTER_PARAMS, SHORTLIST_MEMORANDUM_PARAMS,
    INTERVIEW_MEMORANDUM_PARAMS, SALARY_DECLARATION_LETTER_PARAMS,
    EMPLOYMENT_AGREEMENT_PARAMS, CANDIDATE_LETTER_PARAMS, EXTERNAL_USER_LETTER_PARAMS
)
from irhrs.recruitment.models import Template


class TemplateAPIViewSet(RecruitmentOrganizationMixin, HRSModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [permission_factory.build_permission(
        'TemplateAPIViewSet',
        limit_write_to=[OVERALL_RECRUITMENT_PERMISSION]
    )]
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, FilterMapBackend
    )
    filter_map = {
        'type': 'type'
    }
    lookup_field = 'slug'
    ordering_fields = (
        'title', 'modified_at', 'type',
    )

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.organization)

    def get_permission_classes(self):
        if self.is_supervisor and self.request.method in SAFE_METHODS:
            return self.permission_classes
        else:
            return [RecruitmentPermission, ]

    @property
    def is_supervisor(self):
        return bool(self.request.user.subordinates_pks)

    @action(detail=False)
    def hints(self, request, **kwargs):
        hints = {
            'candidate_letter': CANDIDATE_LETTER_PARAMS,
            'external_user_letter': EXTERNAL_USER_LETTER_PARAMS,
            'no_objection_letter': NO_OBJECTION_LETTER_PARAMS,
            'salary_declaration_letter': SALARY_DECLARATION_LETTER_PARAMS,
            'shortlist_memorandum': SHORTLIST_MEMORANDUM_PARAMS,
            'interview_memorandum': INTERVIEW_MEMORANDUM_PARAMS,
            'employment_agreement': EMPLOYMENT_AGREEMENT_PARAMS
        }
        return Response(hints.get(
            self.request.query_params.get('template_type')
        ))

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context
