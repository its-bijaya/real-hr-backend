from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ModelViewSet

from irhrs.core.utils.common import validate_permissions
from irhrs.organization.api.v1.permissions import (OrganizationSettingsWritePermission,
                                                   OrganizationSettingsWriteOnlyPermission,
                                                   OrganizationEthicsPermission)
from irhrs.permission.constants.permissions import ORGANIZATION_PERMISSION, \
    ORGANIZATION_SETTINGS_VIEW_PERMISSION, \
    ORGANIZATION_SETTINGS_PERMISSION, ORGANIZATION_ETHICS_PERMISSION
from ....models import OrganizationEthics
from ..serializers.ethics import OrganizationEthicsSerializer

from irhrs.core.mixins.viewset_mixins import ParentFilterMixin, \
    OrganizationMixin, OrganizationCommonsMixin


class OrganizationEthicsViewSet(ParentFilterMixin, OrganizationCommonsMixin,
                                OrganizationMixin, ModelViewSet):
    """
    list:
    Lists organization ethics for the selected organization.

    filters

        {
            "is_parent": true/false
        }

    create:
    Create new organization ethics for the given organization.

    retrieve:
    Get organization ethics of the organization.

    delete:
    Deletes the selected organization ethics of the organization.

    update:
    Updates the selected organization ethics details for the given organization.

    """
    queryset = OrganizationEthics.objects.all()
    serializer_class = OrganizationEthicsSerializer
    lookup_field = 'slug'
    ordering_fields = (
        'title', 'moral', 'created_at', 'modified_at', 'parent__title', 'published',
        'is_archived'
    )
    search_fields = ('title', 'moral')
    filter_fields = (
        'moral', 'is_archived', 'published'
    )
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    permission_classes = [OrganizationEthicsPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        if validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            ORGANIZATION_PERMISSION,
            ORGANIZATION_SETTINGS_VIEW_PERMISSION,
            ORGANIZATION_SETTINGS_PERMISSION,
            ORGANIZATION_ETHICS_PERMISSION
        ):
            return qs
        return qs.filter(
            is_archived=False,
            published=True
        )
