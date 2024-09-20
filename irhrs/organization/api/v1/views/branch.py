from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.viewset_mixins import (OrganizationMixin,
                                              OrganizationCommonsMixin, HRSOrderingFilter,
                                              ValidateUsedData)
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.common_utils import nested_get
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.organization.api.v1.permissions import OrganizationBranchPermission
from irhrs.organization.api.v1.serializers.branch import OrganizationBranchSerializer
from irhrs.organization.do_not_compile import OrganizationBranchImportSerializer
from irhrs.organization.models import OrganizationBranch
from irhrs.permission.constants.permissions import (ORGANIZATION_PERMISSION,
                                                    ORGANIZATION_SETTINGS_PERMISSION,
                                                    BRANCH_PERMISSION)
from irhrs.permission.constants.permissions.dynamic_permissions import HAS_PERMISSION_FROM_METHOD
from irhrs.recruitment.models import Country, Province
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer
from irhrs.users.models.experience import UserExperience


class OrganizationBranchViewSet(
    HRSOrderingFilter, OrganizationCommonsMixin,
    OrganizationMixin, BackgroundFileImportMixin, \
    ValidateUsedData, ModelViewSet, BackgroundExcelExportMixin
):
    queryset = OrganizationBranch.objects.select_related(
        'organization', 'branch_manager', 'branch_manager__detail'
    )
    serializer_class = OrganizationBranchSerializer
    import_serializer_class = OrganizationBranchImportSerializer
    lookup_field = 'slug'
    search_fields = ('name', 'code',)
    ordering_fields_map = {
        'title': 'name',
        'phone': 'contacts',
        'branch_manager': ('branch_manager__first_name',
                           'branch_manager__middle_name',
                           'branch_manager__first_name',),
        'email': 'email',
        'address': 'address',
        'modified_at': 'modified_at',
        'code': 'code'
    }
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filter_fields = ('is_archived', )
    permission_classes = [OrganizationBranchPermission]
    permissions_description_for_notification = [
        ORGANIZATION_PERMISSION,
        ORGANIZATION_SETTINGS_PERMISSION,
        BRANCH_PERMISSION,
    ]
    ordering = '-modified_at'
    related_names = [
        'userdetails', 'user_experiences', 'holiday_branch', 'meeting_rooms',
        'equipments', 'preemployment_set', 'jobs'
    ]
    related_methods = ['delete']
    # field for used for file import
    import_fields = [
        'Branch Name',
        'Description',
        'Geographical Region',
        'Phone Number',
        'Email',
        'Branch Code',
        'Branch Manager',
        'Country',
        'Province',
        "Mailing Address",
        "Address"
    ]
    values = [
        'Kathmandu',
        '',
        '',
        '',
        '',
        '12',
        '',
        '',
        '',
        '',
        "Kathmandu"
    ]
    model_fields_map = {
        'Branch Name': 'name',
        'Description': 'description',
        'Geographical Region': 'region',
        'Phone Number': 'contacts',
        'Email': 'email',
        'Branch Code': 'code',
        'Branch Manager': 'branch_manager',
        'Country': 'country_ref',
        'Province': 'province',
        "Mailing Address": 'mailing_address',
        "Address": 'address'
    }
    background_task_name = 'branch'
    sample_file_name = 'branch'
    non_mandatory_field_value = {
        'region': '',
        'mailing_address': '',
        'email': '',
        'description': ''
    }
    slug_field_for_sample = 'name'
    export_description = "Organization Branch Export"
    export_type = "Organization Branch Export"
    export_fields = {
        "Branch name": "name",
        "Branch Code": "code",
        "Phone": "phone",
        "Province": "province.name",
        "Branch Head": "branch_manager.full_name",
        "Address": "address",
    }
    notification_permissions = [ORGANIZATION_PERMISSION, ORGANIZATION_SETTINGS_PERMISSION, \
                                BRANCH_PERMISSION,HAS_PERMISSION_FROM_METHOD]

    @staticmethod
    def prepare_export_object(obj, **kwargs):
        setattr(obj, 'phone', nested_get(obj.contacts,'Phone'))
        return obj

    def get_frontend_redirect_url(self):
        return f'/admin/{self.organization.slug}/organizations/settings/branch'


    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        try:
            total_branch_employees = 0
            for result in response.data['results']:
                branch_employees_count = UserExperience. \
                    objects.filter(is_current=True,
                                   branch__is_archived=False,
                                   branch__slug=result['slug']
                                   ).count()
                total_branch_employees += branch_employees_count
                result.update({
                    'active_branch_employees': branch_employees_count
                })
            response.data.update({
                "statistics": {
                    "total_branch": self.get_organization().branches.count(),
                }
            })
        except AttributeError:
            return response
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        associated = UserExperience.objects.filter(branch__slug=
                                                   response.data['slug'],
                                                   branch__is_archived=False,
                                                   is_current=True)
        user_data = UserThinSerializer(
            instance=[assoc.user for assoc in associated],
            many=True).data
        response.data.update({
            'branch_users': user_data
        })
        return response

    def get_serializer(self, *args, **kwargs):
        if not validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            ORGANIZATION_SETTINGS_PERMISSION,
            ORGANIZATION_PERMISSION,
            BRANCH_PERMISSION
        ):
            kwargs.update({
                'fields': ['name', 'slug']
            })
        return super().get_serializer(*args, **kwargs)

    def has_user_permission(self):
        if self.request.method.upper() == 'GET':
            return True
        return False

    def get_queryset_fields_map(self):
        return {
            'country_ref': Country.objects.all(),
            'province': Province.objects.all(),
        }

    def get_failed_url(self):
        return f'/admin/{self.organization.slug}/organization/settings/branch/?status=failed'

    def get_success_url(self):
        return f'/admin/{self.organization.slug}/organization/settings/branch/?status=success'
