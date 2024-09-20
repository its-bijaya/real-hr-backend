from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import (OrganizationMixin,
                                              OrganizationCommonsMixin, RetrieveUpdateViewSetMixin)
from irhrs.organization.api.v1.permissions import (MissionAndVisionPermission)
from ..serializers.mission_and_vision import (OrganizationMissionSerializer,
                                              OrganizationVisionSerializer)
from ....models import OrganizationMission, OrganizationVision


class OrganizationMissionViewSet(OrganizationCommonsMixin, OrganizationMixin,
                                 ModelViewSet):
    """
    list:
    Lists organization mission for the selected organization.

    create:
    Create new organization mission for the given organization.

    retrieve:
    Get organization mission detail for the organization.

    delete:
    Deletes the selected organization mission for an organization.

    update:
    Updates the selected organization mission details for the given organization

    """
    queryset = OrganizationMission.objects.filter(parent__isnull=True)
    serializer_class = OrganizationMissionSerializer
    lookup_field = 'slug'
    search_fields = ('title',)
    ordering_fields = ('order_field', 'title')
    filter_backends = (SearchFilter, OrderingFilter)
    permission_classes = [MissionAndVisionPermission]

    def get_queryset(self):
        return super().get_queryset().prefetch_related('child_missions')


class OrganizationVisionViewSet(OrganizationCommonsMixin, OrganizationMixin,
                                RetrieveUpdateViewSetMixin):
    """
    list:
    Lists organization vision for the selected organization.

    create:
    Create new organization vision for the given organization.

    retrieve:
    Get organization vision detail for the organization.

    delete:
    Deletes the selected organization vision for an organization.

    update:
    Updates the selected organization vision details for the given organization.

    """
    queryset = OrganizationVision.objects.all()
    serializer_class = OrganizationVisionSerializer
    permission_classes = [MissionAndVisionPermission]

    def get_object(self):
        return self.get_queryset().first()
