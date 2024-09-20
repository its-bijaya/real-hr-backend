from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework import filters

from irhrs.common.models import DutyStation
from irhrs.hris.models import DutyStationAssignment
from irhrs.common.api.serializers.duty_station import DutyStationSerializer
from irhrs.hris.api.v1.serializers.duty_station_assignment import (
    DutyStationAssignmentSerializer, CurrentDutyStationAssignmentSerializer
)
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin,
    OrganizationCommonsMixin,
    ListCreateUpdateDestroyViewSetMixin)
from irhrs.common.api.permission import DutyStationPermission
from irhrs.users.models import User
from irhrs.core.mixins.viewset_mixins import (
    ListCreateUpdateDestroyViewSetMixin)
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap, \
    SearchFilter
from irhrs.core.utils.common import validate_permissions
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.permission.constants.permissions.hrs_permissions import DUTY_STATION_PERMISSION

class DutyStationViewSet(ListCreateUpdateDestroyViewSetMixin,BackgroundExcelExportMixin):
    filter_backends = [
        filters.OrderingFilter,
        SearchFilter,
        FilterMapBackend,
    ]
    search_fields = ('name',)
    ordering_fields = ['name', 'amount', 'modified_at', 'created_at']
    filter_map = {
        'is_archived': 'is_archived'
    }
    queryset = DutyStation.objects.all()
    permission_classes = [DutyStationPermission]
    serializer_class = DutyStationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["action"] = self.action
        return context

    def perform_destroy(self, instance):
        has_assignments = instance.assignments.exists()
        if has_assignments:
            message = {
                'error': f'This duty station cannot be deleted '
                f'because some users are currently assigned to it.'
            }
            raise ValidationError(message)
        instance.delete()
    
    export_type = 'Duty Station Export'

    export_fields = {
        'Duty Station Category': 'name',
        'Amount' : 'amount',
        'Description' : 'description',
        'Is Archived' : 'is_archived',
    }

    notification_permissions = [DUTY_STATION_PERMISSION]

    frontend_redirect_url = f'/commons/settings/duty-station'
