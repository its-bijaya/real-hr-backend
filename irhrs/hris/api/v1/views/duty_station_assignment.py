from django.db.models import (
    Case, When, IntegerField, Value, BooleanField, Subquery,
    DateField, Q, OuterRef, F, Max, FilteredRelation)
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from irhrs.common.models.duty_station import DutyStation
from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin

from irhrs.core.utils.common import get_today
from irhrs.hris.models import DutyStationAssignment
from irhrs.hris.api.v1.serializers.duty_station_assignment import (
    DutyStationAssignmentSerializer, CurrentDutyStationAssignmentSerializer, DutyStationImportSerializer
)
from irhrs.hris.utils.utils import filter_duty_station_assignment
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin,
    OrganizationCommonsMixin,
    ListViewSetMixin,
    ListCreateUpdateDestroyViewSetMixin)
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.users.models import User
from irhrs.hris.api.v1.permissions import AssignUnassignDutyStationPermission
from irhrs.core.mixins.viewset_mixins import (
    ListCreateUpdateDestroyViewSetMixin,
    OrganizationCommonsMixin,
    DisallowPatchMixin
)
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap, \
    SearchFilter
from irhrs.organization.models import FiscalYear
from irhrs.permission.constants.permissions import ASSIGN_UNASSIGN_DUTY_STATION_PERMISSION



class DutyStationAssignmentViewSet(
        OrganizationMixin,
        OrganizationCommonsMixin,
        BackgroundFileImportMixin,
        DisallowPatchMixin,
        ListCreateUpdateDestroyViewSetMixin,
        BackgroundExcelExportMixin,
):
    queryset = DutyStationAssignment.objects.exclude(
        duty_station__is_archived=True,
    )
    serializer_class = DutyStationAssignmentSerializer
    import_serializer_class = DutyStationImportSerializer
    permission_classes = [AssignUnassignDutyStationPermission]
    filter_backends = [FilterMapBackend, OrderingFilterMap, SearchFilter,]
    search_fields = (
        'user__first_name','user__middle_name','user__last_name', 'user__username',
    )
    filter_map = {
        'user': 'user',
        'duty_station': 'duty_station',
    }
    ordering_fields_map = {
        'from_date': 'from_date',
        'to_date': 'to_date',
        'full_name': ('user__first_name', 'user__middle_name', 'user__last_name')
    }
    ordering = 'from_date'

    import_fields = [
        "User",
        "Duty Station",
        "From Date",
        "To Date"
    ]
    values = [
        "info@example.com",
        "Bhaktapur",
        "2023-05-25",
        "2023-05-25",
    ]
    background_task_name = 'duty_station'
    sample_file_name = 'duty-station-import'

    def get_queryset(self):
        qs = super().get_queryset()
        fiscal_year_id = self.request.query_params.get('fiscal_year', None)
        if fiscal_year_id:
            fiscal_year = FiscalYear.objects.filter(id=fiscal_year_id).first()
            return filter_duty_station_assignment(qs, fiscal_year) if fiscal_year else qs.none()
        return qs

    # def get_serializer_class(self):
    #     pass

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["action"] = self.action
        return context

    def get_success_url(self):
        success_url = f'/admin/{self.organization.slug}/hris/settings/duty-station/'
        return success_url

    def get_failed_url(self):
        failed_url = f'/admin/{self.organization.slug}/hris/settings/duty-station/?status=failed'
        return failed_url

    def get_queryset_fields_map(self):
        return {
            'duty_station': DutyStation.objects.filter(is_archived=False).values_list('slug'),
        }

    export_type = "Duty Station Report"

    export_fields = {
        'Employee Name' : 'user.full_name',
        'Username': 'user.username',
        'Duty Station Category': 'duty_station.name',
        'From Date': 'from_date',
        'To Date' : 'to_date',
    }

    notification_permissions = [ASSIGN_UNASSIGN_DUTY_STATION_PERMISSION]

    def get_frontend_redirect_url(self):
        return f'/admin/{self.organization.slug}/hris/settings/duty-station'

class CurrentDutyStationAssignmentViewSet(
        OrganizationMixin,
        ListViewSetMixin,
        BackgroundExcelExportMixin,
):
    queryset = User.objects.all()
    serializer_class = CurrentDutyStationAssignmentSerializer
    permission_classes = [AssignUnassignDutyStationPermission]
    filter_backends = [FilterMapBackend, SearchFilter,OrderingFilterMap]
    search_fields = ('username','first_name', 'last_name', 'middle_name')
    filter_map = {
        'user': 'id',
        'dutyStation': 'assigned_duty_stations__duty_station__name'
    }
    ordering_fields_map = {
        'from_date': 'current_duty_station__from_date',
        'to_date': 'current_duty_station__to_date',
        'full_name': ('first_name', 'middle_name', 'last_name')
    }
    export_type = "Current Duty Station Report"
    export_fields = {
        'Employee Name' : 'full_name',
        'Username': 'username',
        'Duty Station Category': 'duty_station_name',
        'From Date': 'from_date',
        'To Date' : 'to_date',
    }

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            detail__organization=self.organization
        ).filter(
            assigned_duty_stations__isnull=False
        ).annotate(
            current_duty_station = FilteredRelation(
                'assigned_duty_stations',
                condition=Q(
                    Q(
                        Q(assigned_duty_stations__to_date=None) &
                        Q(
                            assigned_duty_stations__from_date__lte=get_today()
                        )
                    ) |
                    Q(
                        ~Q(assigned_duty_stations__to_date=None) &
                        Q(
                            assigned_duty_stations__from_date__lte=get_today(),
                            assigned_duty_stations__to_date__gte=get_today()
                        )
                    ),
                )
            )
        ).annotate(
            duty_station_name = F('current_duty_station__duty_station__name'),
            duty_station_id = F('current_duty_station__duty_station__id'),
            duty_station_assignment_id = F('current_duty_station__id'),
            from_date = F('current_duty_station__from_date'),
            to_date = F('current_duty_station__to_date'),
        ).distinct()
        return queryset


    notification_permissions = [ASSIGN_UNASSIGN_DUTY_STATION_PERMISSION]

    def get_frontend_redirect_url(self):
        return f'/admin/{self.organization.slug}/hris/settings/duty-station'
