from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import DisallowPatchMixin
from irhrs.organization.models import Organization
from ..permissions import AttendancePermission, AttendanceSourcePermission
from ..serializers.source import AttendanceSourceSerializer
from ....constants import (
    DONT_SYNC, DIRSYNC, ADMS, SYNC_SUCCESS
)
from ....models import AttendanceSource
from ....utils.connection_test import (
    adms_connection_test, dirsync_connection_test
)


class AttendanceSourceViewSet(DisallowPatchMixin, ModelViewSet):
    queryset = AttendanceSource.objects.all()
    serializer_class = AttendanceSourceSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = (
        "name",
    )

    ordering_fields = (
        'id',
        'name',
        'last_activity',
    )
    permission_classes = [AttendanceSourcePermission]

    def get_organization(self):
        return get_object_or_404(
            Organization.objects.filter(
                id__in=self.request.user.switchable_organizations_pks
            ),
            slug=self.request.query_params.get('organization_slug')
        )

    def get_queryset(self):
        return super().get_queryset().annotate(
            total_sync=Count(
                'entry_cache',
                filter=Q(
                    entry_cache__reason=SYNC_SUCCESS,
                    # currently only sync status is updated so, modified_at will be sync time
                    entry_cache__modified_at__date=timezone.now().date()
                ),
                distinct=True
            )
        )


class ConnectionTest(APIView):
    permission_classes = [AttendancePermission]

    def post(self, request):
        serializer = AttendanceSourceSerializer(
            data=request.data,
            fields=('sync_method', 'ip', 'port', 'timezone')
        )
        if serializer.is_valid(raise_exception=True):
            if 'sync_method' in serializer.data.keys():
                sync_method = serializer.data['sync_method']
                if sync_method == ADMS:
                    try:
                        connection_status = adms_connection_test()
                        return_data = {
                            'status': connection_status,
                            'using': ADMS
                        }
                    except:
                        return_data = {
                            'status': False,
                            'using': ADMS
                        }
                elif sync_method == DIRSYNC:
                    data = {
                        'ip': serializer.data['ip'] or ''
                    }
                    if serializer.data['port']:
                        data.update({'port': serializer.data['port']})
                    connection_status = dirsync_connection_test(**data)
                    return_data = {
                        'status': connection_status,
                        'using': DIRSYNC
                    }
                else:
                    return_data = {
                        'status': False,
                        'using': DONT_SYNC
                    }
                return Response(return_data, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Sync Method is Required'
                },
                    status=status.HTTP_403_FORBIDDEN
                )

        return Response({'status': False, 'message': 'Invalid Request Data'})

    def get_organization(self):
        return get_object_or_404(
            Organization.objects.filter(
                id__in=self.request.user.switchable_organizations_pks
            ),
            slug=self.request.query_params.get('organization_slug')
        )
