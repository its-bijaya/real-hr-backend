from django.utils.functional import cached_property
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import \
    DisallowPatchMixin, OrganizationMixin, \
    OrganizationCommonsMixin, DateRangeParserMixin, CreateListModelMixin, ListCreateViewSetMixin
from irhrs.core.utils.common import validate_permissions, get_today
from irhrs.leave.api.v1.permissions import LeaveReadPermission, LeaveMasterSettingPermission
from irhrs.leave.api.v1.serializers.settings import MasterSettingSerializer, \
    LeaveTypeSerializer, LeaveApprovalSerializer
from irhrs.leave.constants.model_constants import IDLE, CREDIT_HOUR, TIME_OFF
from irhrs.leave.models import MasterSetting, LeaveType
from irhrs.leave.models.settings import LeaveApproval
from irhrs.leave.tasks import get_active_master_setting
from irhrs.permission.constants.permissions import LEAVE_PERMISSION, MASTER_SETTINGS_PERMISSION, \
    ASSIGN_LEAVE_PERMISSION

HOURLY_CATEGORIES = (CREDIT_HOUR, TIME_OFF)


class MasterSettingViewSet(DisallowPatchMixin,
                           OrganizationMixin,
                           OrganizationCommonsMixin,
                           ModelViewSet):
    serializer_class = MasterSettingSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('effective_from', 'effective_till', 'name',
                       'modified_at',)
    queryset = MasterSetting.objects.all()
    permission_classes = [LeaveMasterSettingPermission]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset=queryset)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.status_filter(status=status)
        return queryset

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status != IDLE:
            # do not allow update if setting is not idle
            raise MethodNotAllowed(request.method)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status != IDLE:
            # do not allow destroy if setting is not idle
            raise MethodNotAllowed(request.method)

        # while destroying for an organization, set effective till of active setting back to null
        MasterSetting.objects.filter(
            organization=self.get_organization()
        ).active().update(effective_till=None)
        return super().destroy(request, *args, **kwargs)


class LeaveTypeViewSet(
    DateRangeParserMixin, DisallowPatchMixin, OrganizationMixin, ModelViewSet
):
    serializer_class = LeaveTypeSerializer
    queryset = LeaveType.objects.all()
    filter_fields = (
        'master_setting',
    )
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter,)
    search_fields = 'name',
    ordering_fields = ('modified_at',)
    permission_classes = [LeaveReadPermission]

    def get_queryset(self):
        qs = super().get_queryset().filter(
            master_setting__organization=self.get_organization()
        )
        hourly = self.request.query_params.get('hourly')
        if hourly:
            if hourly == 'true':
                qs = qs.filter(category__in=HOURLY_CATEGORIES)
            elif hourly == 'false':
                qs = qs.exclude(category__in=HOURLY_CATEGORIES)

        active_settings = self.get_active_settings
        master_setting_filter = self.request.query_params.get('active_status')
        if master_setting_filter == 'active':
            return qs.filter(
                master_setting=get_active_master_setting(
                    organization=self.get_organization()
                )
            )
        elif master_setting_filter == 'expired':
            expired_setting = MasterSetting.objects.filter(
                organization=self.get_organization(),
                effective_till__isnull=False
            ).order_by(
                '-effective_till'
            ).expired().first()
            return qs.filter(master_setting=expired_setting)
        elif self.request.query_params.get('fiscal'):
            return qs.filter(
                master_setting__in=active_settings
            )
        return qs

    @cached_property
    def get_active_settings(self):
        if self.request.query_params.get('fiscal') and self.fiscal_year:
            return list(
                MasterSetting.objects.filter(
                    organization=self.get_organization()
                ).active_between(
                        self.fiscal_year.start_at,
                        self.fiscal_year.end_at
                )
            )
        active = get_active_master_setting(self.get_organization())
        return [active] if active else []

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        # if self.request.query_params.get('fiscal_type'):
        #     year = self.fiscal_year
        #     if not year:
        #         return qs.none()
        #     qs = qs.filter(
        #         master_setting=MasterSetting.objects.filter(
        #             organization=self.organization
        #         ).active_for_date(
        #             year.applicable_to
        #         ).order_by(
        #             '-effective_from'
        #         ).first()
        #     )
        return qs

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.master_setting.status != IDLE:
            # do not allow destroy if setting is not idle
            raise MethodNotAllowed(request.method)
        return super().destroy(request, *args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        if not validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            LEAVE_PERMISSION, MASTER_SETTINGS_PERMISSION,
            ASSIGN_LEAVE_PERMISSION
        ):
            kwargs.update({
                'fields': ('name', 'id')
            })
        return super().get_serializer(*args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.organization
        if self.request.query_params.get('fiscal'):
            if len(self.get_active_settings) > 1:
                context['merge_master_setting_name'] = True
        return context


class LeaveApprovalViewSet(
    OrganizationMixin,
    OrganizationCommonsMixin,
    ListCreateViewSetMixin
):
    serializer_class = LeaveApprovalSerializer
    permission_classes = [LeaveMasterSettingPermission]
    queryset = LeaveApproval.objects.all()

    def get_queryset(self):
        return super().get_queryset().order_by('authority_order').select_related(
            'employee', 'employee__detail', 'employee__detail__organization',
            'organization'
        )

    def create(self, request, *args, **kwargs):
        self.get_queryset().delete()
        return super().create(request, *args, **kwargs)
