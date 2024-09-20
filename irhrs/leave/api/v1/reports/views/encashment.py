from rest_framework.decorators import action
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import ListRetrieveUpdateViewSetMixin, OrganizationMixin, \
    OrganizationCommonsMixin, GetStatisticsMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.leave.api.v1.reports.serializers.encashment import LeaveEncashmentSerializer, \
    LeaveEncashmentBulkActionSerializer, LeaveEncashmentHistorySerializer
from irhrs.leave.models.account import LeaveEncashment
from irhrs.permission.constants.permissions import LEAVE_REPORT_PERMISSION
from irhrs.permission.permission_classes import FullyDynamicPermission


class LeaveEncashmentViewSet(
    OrganizationCommonsMixin,
    OrganizationMixin,
    GetStatisticsMixin,
    ListRetrieveUpdateViewSetMixin,
):
    organization_field = 'user__detail__organization'
    serializer_class = LeaveEncashmentSerializer
    queryset = LeaveEncashment.objects.all().select_related(
        'user',
        'user__detail',
        'user__detail__organization',
        'user__detail__job_title',
        'account__rule__leave_type'
    )

    filter_backends = (FilterMapBackend, OrderingFilterMap)
    filter_map = {
        'user': 'user',
        'leave_type': 'account__rule__leave_type',
        'status': 'status',
        'start': 'created_at__date__gte',
        'end': 'created_at__date__lte'
    }

    ordering_fields_map = {
        'full_name': ('user__first_name', 'user__middle_name', 'user__last_name'),
        'leave_type': 'account__rule__leave_type__name',
        'balance': 'balance',
        'status': 'status',
        'created_at': 'created_at',
        'modified_at': 'modified_at'
    }
    statistics_field = "status"

    permission_classes = [FullyDynamicPermission]

    @property
    def mode(self):
        if self.request.query_params.get('as') == 'hr':
            return 'hr'
        return 'user'

    def has_user_permission(self):
        if self.mode == 'hr' and not validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            LEAVE_REPORT_PERMISSION
        ):
            return False

        # allow read-only to normal user
        return self.request.method.upper() == 'GET' or self.mode == 'hr'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.mode != 'hr':
            return queryset.filter(user=self.request.user)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['stats'] = self.statistics
        return response

    @action(methods=['POST'], detail=False, serializer_class=LeaveEncashmentBulkActionSerializer,
            url_path='bulk-action')
    def bulk_action(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "detail": "Successfully updated"
        })

    @action(methods=['GET'], detail=True, serializer_class=LeaveEncashmentHistorySerializer,
            filter_map={}, ordering_fields_map={})
    def histories(self, request, **kwargs):
        encashment = self.get_object()

        def get_qs():
            return encashment.history.all()

        self.get_queryset = get_qs
        return super().list(request, **kwargs)
