import types

from django.db.models import Count, Q
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import ListCreateViewSetMixin
from irhrs.core.utils.organization import get_switchable_users
from irhrs.organization.models import Organization
from irhrs.permission.api.v1.serializers.organization import OrganizationCreateSerializer, \
    OrganizationUserSerializer, OrganizationPermissionSerializer
from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.constants.permissions import AUTH_PERMISSION
from irhrs.permission.models.hrs_permisssion import OrganizationGroup, HRSPermission
from irhrs.permission.permission_classes import permission_factory


class OrganizationCreateViewSet(ListCreateViewSetMixin):
    lookup_field = 'slug'
    serializer_class = OrganizationCreateSerializer
    queryset = Organization.objects.all()
    filter_backends = [SearchFilter]
    search_fields = ['name', 'abbreviation']
    permission_classes = [permission_factory.build_permission(
        'PortalPermission',
        allowed_to=[AUTH_PERMISSION]
    )]

    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            admin_count=Count(
                'users',
                filter=Q(users__can_switch=True),
                distinct=True
            )
        )
        return queryset.distinct()

    def get_object(self):
        if self.kwargs.get('slug').lower() == "common":
            return None
        return super().get_object()

    @action(
        detail=True,
        methods=['GET'],
        url_path='admins',
        serializer_class=OrganizationUserSerializer
    )
    def manage_admins(self, request, *args, **kwargs):
        organization = self.get_object()
        organization_admins = get_switchable_users(organization)
        serializer = OrganizationUserSerializer(
            {
                'user_count': organization_admins.count(),
                'users': organization_admins.select_related(
                    'detail', 'detail__job_title'
                ),
                'organization': organization
            },
            context=self.get_serializer_context()
        )
        response = serializer.data
        return Response(response)

    @manage_admins.mapping.post
    def manage_admins_create(self, request, *args, **kwargs):
        def get_serializer_context(s):
            # pulling these data from super class, as can not call super() from
            # nested function in when extension is generated
            return {
                'request': s.request,
                'format': s.format_kwarg,
                'view': s,
                'organization': s.get_object()
            }

        self.get_serializer_context = types.MethodType(get_serializer_context, self)
        return super().create(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['GET'],
        url_path=r'group/(?P<group_id>\d+)',
        serializer_class=OrganizationPermissionSerializer
    )
    def retrieve_permission(self, request, *args, **kwargs):
        organization = self.get_object()
        permission = OrganizationGroup.objects.filter(
            organization=organization,
            group_id=self.kwargs.get('group_id')
        ).first()
        if permission:
            ser = OrganizationPermissionSerializer(
                permission,
                context=self.get_serializer_context()
            )
            return Response(ser.data)
        return Response({"detail": "Not found."})

    @action(
        detail=True,
        methods=['POST'],
        url_path=r'group',
        serializer_class=OrganizationPermissionSerializer
    )
    def create_permissions(self, request, *args, **kwargs):
        def get_serializer_context(s):
            # pulling these data from super class, as can not call super() from
            # nested function in when extension is generated
            return {
                'request': s.request,
                'format': s.format_kwarg,
                'view': s,
                'organization': s.get_object()
            }
        self.get_serializer_context = types.MethodType(get_serializer_context, self)
        return super().create(request, *args, **kwargs)

    @create_permissions.mapping.get
    def list_permissions(self, request, *args, **kwargs):
        self.search_fields = list()
        organization = self.get_object()
        fil = {}
        if not organization:
            fil['organization__isnull'] = True
        else:
            fil['organization'] = organization

        def get_queryset(s):
            return OrganizationGroup.objects.filter(
                **fil
            ).exclude(
                group__name=ADMIN
            ).annotate(
                permissions_count=Count('permissions')
            )

        self.search_fields = ['group__name']

        self.get_queryset = types.MethodType(get_queryset, self)

        response = super().list(request, *args, **kwargs)
        response.data['total_permissions'] = HRSPermission.objects.filter(
            organization_specific=True if organization else False
        ).count()
        return response

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list_permissions':
            kwargs.update({
                'exclude_fields': ['permissions']
            })
        return super().get_serializer(*args, **kwargs)
