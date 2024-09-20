from rest_framework import filters

# Project other app imports

# Project current app imports
from irhrs.common.api.permission import CommonPermissionMixin
from irhrs.common.api.serializers.system_log import SystemEmailLogSerializer
from irhrs.common.models.system_email_log import SystemEmailLog
from irhrs.core.mixins.viewset_mixins import ListRetrieveViewSetMixin
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.organization.api.v1.permissions import SystemEmailLogPermission
from irhrs.permission.utils.base import AuditUserPermission


class SystemEmailLogViewSet(ListRetrieveViewSetMixin):
    queryset = []
    serializer_class = SystemEmailLogSerializer
    filter_backends = (filters.SearchFilter,
                       FilterMapBackend, OrderingFilterMap)
    permission_classes = [SystemEmailLogPermission]
    search_fields = (
        'user__first_name',
        'user__middle_name',
        'user__last_name',
    )
    filter_map = {
        'start_date': 'created_at__date__gte',
        'end_date': 'created_at__date__lte',
    }
    ordering_fields_map = {
        'full_name': (
            'user__first_name',
            'user__middle_name',
            'user__last_name',
        ),
        'subject': 'subject',
        'status': 'status',
        'sent_address': 'sent_address',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
    }

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.action == 'retrieve':
            ctx.update({
                'show_details': self.require_details
            })
        return ctx

    def get_queryset(self):
        if self.require_details:
            qs = SystemEmailLog.objects.all()
        else:
            qs = SystemEmailLog.objects.defer('html_message')

        # filter queryset according to switchable permissions.
        qs = qs.filter(
            user__detail__organization__in=self.request.user.switchable_organizations_pks
        )
        return qs.select_related(
            'user',
            'user__detail',
            'user__detail__organization',
            'user__detail__division',
            'user__detail__employment_status',
            'user__detail__employment_level',
            'user__detail__job_title',
            'user__detail__branch',
        )

    @property
    def require_details(self):
        return self.request.query_params.get('show_details', False) == 'true'
