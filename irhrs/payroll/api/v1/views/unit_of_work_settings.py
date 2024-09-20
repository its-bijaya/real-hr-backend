from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.viewset_mixins import OrganizationCommonsMixin, OrganizationMixin, \
    CreateViewSetMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.core.utils.subordinates import authority_exists
from irhrs.hris.models import User
from irhrs.payroll.api.permissions import UnitOfWorkSettingPermission
from irhrs.payroll.api.v1.serializers.unit_of_work_settings import OperationSerializer, \
    OperationCodeSerializer, OperationRateSerializer, OperationRateImportSerializer, \
    UserOperationRateSerializer, OperationRateUserSerializer
from irhrs.payroll.models.unit_of_work_settings import Operation, OperationCode, OperationRate, \
    UserOperationRate
from irhrs.permission.constants.permissions import ALL_PAYROLL_PERMISSIONS, \
    UNIT_OF_WORK_SETTINGS_PERMISSION, PAYROLL_SETTINGS_PERMISSION


class OperationOperationCodeMixin:
    permission_classes = [UnitOfWorkSettingPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ('title',)
    ordering = '-modified_at'
    ordering_fields = (
        'title',
        'created_at',
        'modified_at'
    )

    import_fields = [
        'TITLE',
        'DESCRIPTION',
    ]
    non_mandatory_field_value = {
        'description': ''
    }


class OperationViewSet(
    OperationOperationCodeMixin,
    BackgroundFileImportMixin,
    OrganizationCommonsMixin,
    OrganizationMixin,
    ModelViewSet,
):
    serializer_class = OperationSerializer
    queryset = Operation.objects.all()
    background_task_name = 'operation'

    def get_queryset(self):
        mode = self.request.query_params.get('as')
        user = self.request.query_params.get('user')
        queryset = super().get_queryset()
        if mode == 'hr':
            validate = validate_permissions(
                self.request.user.get_hrs_permissions(self.organization),
                ALL_PAYROLL_PERMISSIONS,
                PAYROLL_SETTINGS_PERMISSION,
                UNIT_OF_WORK_SETTINGS_PERMISSION
            )
            if not validate:
                raise PermissionDenied
            if user:
                queryset = queryset.filter(rates__user_operation_rate__user_id=int(user))

        elif mode == 'supervisor':
            supervisor = self.request.user
            if user:
                user_supervisors = User.objects.get(id=int(user)).user_supervisors
                supervisors = [user_supervisor.supervisor for user_supervisor in user_supervisors]
                approve_authority = authority_exists(int(user), supervisor, 'approve')
                if supervisor not in supervisors or not approve_authority:
                    raise PermissionDenied
                queryset = queryset.filter(rates__user_operation_rate__user_id=user)

        else:
            queryset = queryset.filter(
                rates__user_operation_rate__user=self.request.user
            )
        return queryset

    def get_success_url(self):
        return f'/admin/{self.organization.slug}/payroll/settings/unit-of-work/operation'

    def get_failed_url(self):
        return f'/admin/{self.organization.slug}/payroll/settings/' \
               'unit-of-work/operation?status=failed'


class OperationCodeViewSet(
    OperationOperationCodeMixin,
    BackgroundFileImportMixin,
    OrganizationCommonsMixin,
    OrganizationMixin,
    ModelViewSet
):
    serializer_class = OperationCodeSerializer
    queryset = OperationCode.objects.all()
    background_task_name = 'operation code'

    def get_success_url(self):
        return f'/admin/{self.organization.slug}/payroll/settings/unit-of-work/code'

    def get_failed_url(self):
        return f'/admin/{self.organization.slug}/payroll/settings/unit-of-work/code?status=failed'


class OperationRateViewSet(
    BackgroundFileImportMixin,
    OrganizationMixin,
    OrganizationCommonsMixin,
    ModelViewSet
):
    permission_classes = [UnitOfWorkSettingPermission]
    serializer_class = OperationRateSerializer
    import_serializer_class = OperationRateImportSerializer
    import_fields = [
        'OPERATION',
        'OPERATION_CODE',
        'RATE'
    ]
    filter_backends = (FilterMapBackend, OrderingFilterMap)

    filter_map = {
        'operation_id': 'operation',
        'operation_search': ('operation__title', 'icontains'),
        'operation_code_id': 'operation_code',
        'operation_code_search': ('operation_code__title', 'icontains')
    }

    ordering_fields_map = {
        'operation': 'operation__title',
        'operation_code': 'operation_code__title',
        'rate': 'rate',
        'created_at': 'created_at',
        'modified_at': 'modified_at'
    }

    slug_field_for_sample = 'title'
    background_task_name = 'operation rate'

    def get_success_url(self):
        return f'/admin/{self.organization.slug}/payroll/settings/unit-of-work/rate'

    def get_failed_url(self):
        return f'/admin/{self.organization.slug}/payroll/settings/unit-of-work/rate?status=failed'

    def get_queryset(self):
        mode = self.request.query_params.get('as')
        user = self.request.query_params.get('user')
        queryset = OperationRate.objects.all()
        if mode == 'hr':
            validate = validate_permissions(
                self.request.user.get_hrs_permissions(self.organization),
                ALL_PAYROLL_PERMISSIONS,
                PAYROLL_SETTINGS_PERMISSION,
                UNIT_OF_WORK_SETTINGS_PERMISSION
            )
            if not validate:
                raise PermissionDenied
            if user:
                queryset = queryset.filter(user_operation_rate__user_id=user)

        elif mode == 'supervisor':
            supervisor = self.request.user
            if user:
                user_supervisors = User.objects.get(id=int(user)).user_supervisors
                supervisors = [user_supervisor.supervisor for user_supervisor in user_supervisors]
                approve_authority = authority_exists(int(user), supervisor, 'approve')
                if supervisor not in supervisors and approve_authority:
                    raise PermissionDenied
                queryset = queryset.filter(user_operation_rate__user_id=user)

        else:
            queryset = queryset.filter(
                user_operation_rate__user=self.request.user
            )
        return queryset.filter(
            operation__organization=self.get_organization()
        ).select_related('operation', 'operation_code')

    def get_queryset_fields_map(self):
        return {
            'operation': Operation.objects.filter(organization=self.organization),
            'operation_code': OperationCode.objects.filter(organization=self.organization)
        }

    @action(
        detail=True, methods=['GET'], serializer_class=OperationRateUserSerializer, url_path='users'
    )
    def users(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)


class UserOperationRateViewSet(OrganizationMixin, CreateViewSetMixin):
    permission_classes = [UnitOfWorkSettingPermission]
    serializer_class = UserOperationRateSerializer
    queryset = UserOperationRate.objects.all()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['rate_id'] = self.kwargs.get('operation_rate_id')
        ctx['organization'] = self.get_organization()
        return ctx


