from rest_framework.filters import SearchFilter, OrderingFilter

from irhrs.core.mixins.viewset_mixins import (
    HRSModelViewSet,
    OrganizationMixin)
from irhrs.recruitment.api.v1.permissions import RecruitmentPermission
from irhrs.recruitment.api.v1.serializers.external_profile import ExternalSerializer
from irhrs.recruitment.models import (
    External)


class ExternalViewSet(OrganizationMixin, HRSModelViewSet):
    queryset = External.objects.prefetch_related('ksao')
    serializer_class = ExternalSerializer
    permission_classes = [RecruitmentPermission]
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ('user__full_name', )
    ordering_fields = ('user__full_name',)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.organization
        return context
