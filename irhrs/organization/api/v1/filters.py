from django.contrib.auth import get_user_model
from django_filters.rest_framework import filters, FilterSet

from irhrs.core.constants.organization import USED, IDLE, DAMAGED, \
    ASSET_STATUS, ASSIGNED_TO_CHOICES
from irhrs.organization.models import (
    OrganizationEquipment
)
from django.db.models import Q

used_filter = OrganizationEquipment.is_currently_assigned_filter(
    called_from_equipment_model=True
)
idle_filter = Q(~Q(used_filter), is_damaged=False)

class OrganizationEquipmentFilterSet(FilterSet):
    status = filters.CharFilter(
        method='filter_status'
    )

    def filter_status(self, queryset, name, value):
        if value == IDLE:
            queryset = queryset.filter(idle_filter)
        elif value == USED:
            queryset = queryset.filter(used_filter)
        elif value == DAMAGED:
            queryset = queryset.filter(is_damaged=True)
        return queryset

    class Meta:
        model = OrganizationEquipment
        fields = ('status',)
