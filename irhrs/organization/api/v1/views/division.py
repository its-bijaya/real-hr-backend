from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.viewset_mixins import (OrganizationMixin,
                                              OrganizationCommonsMixin, HRSOrderingFilter,
                                              ValidateUsedData)
from irhrs.organization.api.v1.permissions import OrganizationDivisionPermission
from ..serializers.division import OrganizationDivisionSerializer
from ....models import OrganizationDivision

User = get_user_model()


class OrganizationDivisionViewSet(
    BackgroundFileImportMixin, HRSOrderingFilter,
    OrganizationCommonsMixin, ValidateUsedData, OrganizationMixin, ModelViewSet
):
    """
    list:
    Lists organization divisions/departments for the selected organization.

    create:
    Create new divisions/departments for the given organization.

    retrieve:
    Get divisions/departments detail of the organization.

    delete:
    Deletes the selected divisions/departments of the organization.

    update:
    Updates the selected divisions/departments details for the given
    organization.

    """
    queryset = OrganizationDivision.objects.select_related(
        'organization', 'head', 'head__detail'
    ).prefetch_related('division_child')
    lookup_field = 'slug'
    ordering_fields_map = {
        'name': 'name',
        'parent': 'parent__name',
        'head': ('head__first_name', 'head__middle_name', 'head__last_name'),
        'modified_at': 'modified_at'
    }
    search_fields = ('name',)
    serializer_class = OrganizationDivisionSerializer
    filter_backends = (SearchFilter, DjangoFilterBackend,)
    filter_fields = ('is_archived', )
    permission_classes = [OrganizationDivisionPermission]
    ordering = '-modified_at'
    import_fields = [
        'NAME',
        'DESCRIPTION',
        'EMAIL',
        'STRATEGIES',
        'PARENT',
        'EXTENSION NUMBER',
        'ACTION PLANS'
    ]
    values = [
        '* Division 1 (required field)',
        '* Description is required field',
        'division@xyz.com',
        'Strategies for division.',
        '',
        '123',
        'Action Plans for division.',
    ]
    background_task_name = 'organization_division'
    sample_file_name = 'organization_division'
    non_mandatory_field_value = {
        'email': '',
        'strategies': '',
        'extension_number': '',
        'action_plans': ''
    }
    related_names = [
        'userdetails', 'user_experiences', 'division_child', 'holiday_division',
        'equipments', 'division_posts', 'preemployment_set', 'division_result_areas', 'jobs'
    ]
    related_methods = ['delete']

    def get_queryset_fields_map(self):
        return {
            'parent': self.get_queryset()
        }

    def get_failed_url(self):
        return f'/admin/{self.organization.slug}/organization/settings/division/?status=failed'

    def get_success_url(self):
        return f'/admin/{self.organization.slug}/organization/settings/division/?status=success'
