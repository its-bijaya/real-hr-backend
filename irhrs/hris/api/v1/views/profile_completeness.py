from django.contrib.auth import get_user_model
from irhrs.permission.constants.permissions.hrs_permissions import PROFILE_COMPLETENESS_REPORT_PERMISSION

from irhrs.users.models import UserDetail
from irhrs.hris.api.v1.serializers.profile_completeness import ProfileCompletenessSerializer
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin,
    OrganizationCommonsMixin,
    ListViewSetMixin,
)
from irhrs.hris.api.v1.permissions import ProfileCompletenessReportPermission
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap, \
    SearchFilter


User = get_user_model()


class ProfileCompletenessViewSet(
    OrganizationCommonsMixin,
    OrganizationMixin,
    ListViewSetMixin,
    BackgroundExcelExportMixin
):
    queryset = UserDetail.objects.all()
    serializer_class = ProfileCompletenessSerializer

    permission_classes = [ProfileCompletenessReportPermission]
    notification_permissions=[PROFILE_COMPLETENESS_REPORT_PERMISSION]

    filter_backends = [FilterMapBackend, OrderingFilterMap, SearchFilter, ]
    filter_map = {
        'user': 'user',
        'joined_date': 'joined_date',
        'job_title': 'job_title__slug',
        'divisionFilter': 'division__slug',
        'branch': 'branch__slug',
        'employmentLevel': 'employment_level__slug',
    }
    search_fields = ('user__first_name', 'user__middle_name', 'user__last_name')

    ordering_fields_map = {
        'completeness_percent': ('completeness_percent', 'joined_date', 'user__first_name',
                                 'user__middle_name', 'user__last_name'),
        'full_name': ('user__first_name', 'user__middle_name', 'user__last_name'),
        'branch': 'branch__slug',
        'division': 'division__slug',
        'employee_level': 'employment_level__slug',
    }

    export_type = "profile completeness report"
    export_fields = {
        'Full name': 'user.full_name',
        'Branch': 'branch.name',
        'Division': 'division.name',
        'Job title': 'job_title.title',
        'Employment Level': 'employment_level.title',
        'Completeness percent': 'user.profile_completeness',
    }

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        ordering = self.request.query_params.get('ordering')
        mapper = {
            "completeness_percent": False,
            "-completeness_percent": True
        }
        if ordering not in mapper.keys():
            return queryset
        queryset = sorted(
            queryset, 
            key=lambda x: x.user.profile_completeness, 
            reverse=mapper.get(ordering)
        )
        return queryset
