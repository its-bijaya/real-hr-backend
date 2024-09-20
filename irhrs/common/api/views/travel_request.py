from django.db.models import Count, Q
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from irhrs.core.mixins.viewset_mixins import ModeFilterQuerysetMixin
from irhrs.attendance.api.v1.serializers.travel_attendance import TravelAttendanceRequestSerializer
from irhrs.attendance.constants import APPROVED, REQUESTED
from irhrs.attendance.models.travel_attendance import TravelAttendanceRequest
from irhrs.core.utils.filters import FilterMapBackend, NullsAlwaysLastOrderingFilter
from irhrs.permission.constants.permissions.attendance import ATTENDANCE_TRAVEL_PERMISSION


class TravelAttendanceRequestStatsViewSet(ModeFilterQuerysetMixin, GenericViewSet):
    queryset = TravelAttendanceRequest.objects.all()
    serializer_class = TravelAttendanceRequestSerializer
    filter_backends = (
        FilterMapBackend,
        SearchFilter,
        NullsAlwaysLastOrderingFilter
    )
    search_fields = (
        'user__first_name', 'user__middle_name', 'user__last_name'
    )
    filter_map = {
        'status': 'status'
    }
    ordering_fields_map = {
        'full_name': ('user__first_name', 'user__middle_name', 'user__last_name'),
        'start': 'start',
        'end': 'end',
        'balance': 'balance',
        'status': 'status',
        'created_at': 'created_at',
    }
    statistics_field = 'status'
    permission_to_check = ATTENDANCE_TRAVEL_PERMISSION
    user_definition = 'user'

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ["supervisor", "hr"]:
            return mode
        return "user"

    def get_queryset(self):
        qs = super().get_queryset()
        if self.mode == "supervisor":
            qs = qs.filter(recipient=self.request.user)
        return qs

    @action(
        methods=['GET'],
        detail=False,
    )
    def stats(self, *args, **kwargs):
        return Response(
            TravelAttendanceRequest.objects.aggregate(
                pending=Count('id', filter=Q(status=REQUESTED)),
                approved=Count('id', filter=Q(status=APPROVED))
            )
        )
