from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from irhrs.organization.models import (
    EquipmentAssignedTo,
)
from irhrs.organization.models import OrganizationEquipment
from irhrs.core.mixins.viewset_mixins import UserMixin
from irhrs.organization.api.v1.filters import OrganizationEquipmentFilterSet
from irhrs.organization.api.v1.serializers.asset import \
    OrganizationEquipmentSerializer, EquipmentAssignedToSerializer, \
    UserEquipmentSerializer


class UserEquipmentViewSet(UserMixin, ModelViewSet):
    """
    list:
    Lists equipment assigned to each user.
    """
    queryset = OrganizationEquipment.objects.all()
    serializer_class = UserEquipmentSerializer
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = OrganizationEquipmentFilterSet

    def get_serializer(self, *args, **kwargs):
        kwargs['fields'] = (
            'id', 'category', 'code', 'name', 'status', 'assigned_detail'
        )
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        as_hr = self.request.query_params.get('as') == 'hr'
        if not as_hr and self.request.user != self.user and not self.is_supervisor:
            self.permission_denied(self.request)
        return self.queryset.filter(assignments__user=self.user)
