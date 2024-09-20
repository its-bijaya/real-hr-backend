from django.db.models import Count, Q
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter

from irhrs.core.mixins.viewset_mixins import ListRetrieveUpdateViewSetMixin, OrganizationMixin
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.export.api.v1.serializers.export import ExportSerializer
from irhrs.export.constants import PROCESSING, FAILED, QUEUED, COMPLETED
from irhrs.export.models import Export


class ExportViewSet(OrganizationMixin, ListRetrieveUpdateViewSetMixin):
    queryset = Export.objects.all()
    serializer_class = ExportSerializer
    filter_backends = (SearchFilter, FilterMapBackend, OrderingFilterMap)

    ordering = "-created_at"
    ordering_fields_map = {
        'full_name': ('user__first_name', 'user__middle_name', 'user__last_name'),
        'name': 'name',
        'export_type': 'export_type',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
        'exported_as': 'exported_as',
        'status': 'status'
    }
    filter_map = {
        'user': 'user',
        'user_organization': 'user__detail__organization__slug',
        'organization': 'organization__slug',
        'start_date': 'created_at__gte',
        'end_date': 'created_at__lte',
        'status': 'status',
    }
    search_fields = ['name', 'export_type']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            organization=self.get_organization(),
            associated_permissions__code__in=self.request.user.get_hrs_permissions(
                self.get_organization()
            ).union(
                self.request.user.get_hrs_permissions(None)
            )
        ).distinct()
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        count_data = self.get_queryset().aggregate(
            all=Count('id'),
            queued=Count('id', filter=Q(status=QUEUED)),
            processing=Count('id', filter=Q(status=PROCESSING)),
            failed=Count('id', filter=Q(status=FAILED)),
            completed=Count('id', filter=Q(status=COMPLETED)),
        )
        response.data.update({'summary': count_data})
        return response

    @action(
        methods=['POST'],
        detail=True,
        url_path='stop-process',
        queryset=Export.objects.filter(status=PROCESSING)
    )
    def stop_process(self, request, **kwargs):
        obj = self.get_object()
        obj.status = FAILED
        obj.save()
        return Response({'message': 'Process has been Failed'})
