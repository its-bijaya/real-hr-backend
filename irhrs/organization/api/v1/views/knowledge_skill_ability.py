from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from irhrs.core.constants.common import SKILL
from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.viewset_mixins import (OrganizationMixin, OrganizationCommonsMixin)
from irhrs.organization.api.v1.permissions import (KnowledgeSkillAbilityPermission)
from irhrs.organization.api.v1.serializers.knowledge_skill_ability import \
    (KnowledgeSkillAbilitySerializer, KnowledgeSkillAbilityThinSerializer)
from irhrs.organization.models import Organization
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility


class KnowledgeSkillAbilityView(BackgroundFileImportMixin, OrganizationMixin,
                                OrganizationCommonsMixin, ModelViewSet):
    queryset = KnowledgeSkillAbility.objects.all()
    serializer_class = KnowledgeSkillAbilitySerializer
    permission_classes = [KnowledgeSkillAbilityPermission]
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    lookup_field = 'slug'
    search_fields = ['name']
    ordering_fields = ('name', 'created_at', 'modified_at')
    filter_fields = 'ksa_type',
    import_fields = [
        'NAME',
        'DESCRIPTION'
    ]
    non_mandatory_field_value = {
        'description': ''
    }

    def get_queryset(self):
        return super().get_queryset().filter(ksa_type=self.kwargs.get('ksa_type'))

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['ksa_type'] = self.kwargs.get('ksa_type')
        return context

    def get_background_task_name(self):
        return self.kwargs.get('ksa_type')

    def get_sample_file_name(self):
        return self.kwargs.get('ksa_type')

    def get_failed_url(self):
        return f'/admin/{self.organization.slug}/organization/settings' \
               f'/{self.kwargs.get("ksa_type").replace("_", "-").lower()}/?status=failed'

    def get_success_url(self):
        return f'/admin/{self.organization.slug}/organization/settings/' \
               f'{self.kwargs.get("ksa_type").replace("_", "-").lower()}/?status=success'
