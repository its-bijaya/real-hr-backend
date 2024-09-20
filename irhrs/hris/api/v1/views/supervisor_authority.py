from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404 as drf_get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from irhrs.core.mixins.viewset_mixins import (CreateViewSetMixin,
                                              ListRetrieveViewSetMixin, OrganizationMixin,
                                              ListViewSetMixin)
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.organization.models import Organization
from irhrs.permission.constants.permissions import (USER_PROFILE_PERMISSION,
                                                    HRIS_ASSIGN_SUPERVISOR_PERMISSION,
                                                    HRIS_PERMISSION)
from irhrs.permission.permission_classes import permission_factory
from irhrs.hris.api.v1.serializers.supervisor_authority import \
    (BulkAssignSupervisorSerializer, BulkReplaceSupervisorSerializer, UserSupervisorSerializer,
     UserSupervisorsViewSerializer, UserSupervisorDetailSerializer)
from irhrs.users.models import UserSupervisor
from irhrs.users.utils.cache_utils import recalibrate_supervisor_subordinate_relation

User = get_user_model()

UserSupervisorPermission = permission_factory.build_permission(
    "UserSupervisorPermission",
    allowed_to=[
        USER_PROFILE_PERMISSION,
        HRIS_PERMISSION,
        HRIS_ASSIGN_SUPERVISOR_PERMISSION
    ]
)


class UserSupervisorViewSet(CreateViewSetMixin):
    queryset = UserSupervisor.objects.all()
    serializer_class = UserSupervisorDetailSerializer
    permission_classes = (UserSupervisorPermission,)
    lookup_url_kwarg = 'user_id'

    def get_organization(self):
        user = self.request.user
        if not user and user.is_authenticated:
            return None
        org_slug = self.request.query_params.get('organization_slug')
        return Organization.objects.filter(
            id__in=self.request.user.switchable_organizations_pks,
            slug=org_slug
        ).first()

    @action(methods=['post'], detail=True)
    def remove(self, *args, **kwargs):
        user = drf_get_object_or_404(User, pk=kwargs.get('user_id'))
        removed_count, _ = user.user_supervisors.all().delete()
        recalibrate_supervisor_subordinate_relation()
        return Response({
            'removed_count': removed_count
        })

    @action(
        detail=False,
        methods=['post'],
        url_path='bulk-replace'
    )
    def bulk_replace(self, request):
        ser = BulkReplaceSupervisorSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(
            "Supervisor replaced sucessfully.", status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['post'],
        url_path='bulk-assign'
    )
    def bulk_assign(self, request):
        users = request.data.pop('user')
        actual_data = [{'user':user, **request.data} for user in users]
        ser = BulkAssignSupervisorSerializer(data=actual_data, context={'request': self.request}, many=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(
            "Supervisor assigned successfully.", status=status.HTTP_200_OK
        )


class UserSupervisorsList(OrganizationMixin, ListRetrieveViewSetMixin):
    queryset = User.objects.all()
    serializer_class = UserSupervisorsViewSerializer
    filter_backends = (FilterMapBackend, SearchFilter, OrderingFilter)
    search_fields = ('first_name', 'middle_name', 'last_name','username')
    ordering_fields = ('first_name',)
    filter_map = dict(division='detail__division__slug', branch='detail__branch__slug', 
                      employment_level= 'detail__employment_level__slug',
                        employment_type='detail__employment_status__slug',
                        job_title = 'detail__job_title__slug',
                        )
    permission_classes = (UserSupervisorPermission,)

    def get_queryset(self):
        fil = dict()
        if self.action == 'list':
            fil.update({
                'is_active': True,
                'user_experiences__is_current': True
            })
        queryset = super().get_queryset()
        supervisor_id = self.request.query_params.get('supervisor')

        if supervisor_id:
            supervisor = get_object_or_404(User,id=supervisor_id)
            subordinates_id = supervisor.as_supervisor.all().values_list('user',flat=True)

            if subordinates_id:
                queryset = queryset.filter(id__in=subordinates_id)

        return queryset.filter(
            detail__organization=self.organization,
            **fil
        ).select_essentials().prefetch_related(
            Prefetch(
                'supervisors',
                queryset=UserSupervisor.objects.exclude(
                    supervisor=get_system_admin()
                ),
                to_attr='user_supervisors'
            )
        ).all().order_by('first_name')


class UserAllowedPermission(ListViewSetMixin):
    serializer_class = UserSupervisorSerializer

    def list(self, request, *args, **kwargs):
        user = drf_get_object_or_404(
            User.objects.only('id'),
            pk=kwargs.get('user_id')
        )
        authority = UserSupervisor.objects.filter(
            supervisor_id=request.user.id,
            user_id=user.id
        ).only(
            'approve', 'deny', 'forward'
        ).order_by(
        ).first()
        resp = self.get_serializer(
            fields=['approve', 'deny', 'forward'],
            instance=authority
        ).data
        return Response(resp)
