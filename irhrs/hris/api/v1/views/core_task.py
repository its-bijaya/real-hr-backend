from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjValidationError
from django.db.models import Prefetch
from django.http import Http404
from django.utils.functional import cached_property
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import (
    CreateRetrieveUpdateDestroyViewSetMixin,
    CreateViewSetMixin, ListRetrieveViewSetMixin, OrganizationMixin)
from irhrs.core.utils.filters import NullsAlwaysLastOrderingFilter, \
    FilterMapBackend
from irhrs.hris.api.v1.permissions import HRISPermission
from irhrs.organization.models import Organization
from irhrs.permission.constants.permissions import CORE_TASK_RELATED_PERMISSIONS, ASSIGN_CORE_TASK_PERMISSION
from irhrs.permission.permission_classes import permission_factory
from irhrs.task.api.v1.permissions import TaskResultAreaAndCoreTaskPermission
from irhrs.users.models import UserExperience
from ..serializers.core_task import ResultAreaSerializer, CoreTaskSerializer, \
    UserResultAreaListSerializer, UserResultAreaSerializer
from ....models import ResultArea, CoreTask, UserResultArea

USER = get_user_model()


class ResultAreaViewSet(OrganizationMixin, ModelViewSet):
    serializer_class = ResultAreaSerializer
    queryset = ResultArea.objects.all().select_related('division')
    filter_backends = (FilterMapBackend, SearchFilter, OrderingFilter,)
    filter_map = dict(division='division__slug',)
    search_fields = ('title',)
    ordering_fields = ('title', 'created', 'updated')
    permission_classes = [TaskResultAreaAndCoreTaskPermission]

    def get_queryset(self):
        return super().get_queryset() \
            .filter(
            division__organization=self.get_organization()) \
            .prefetch_related('core_tasks',
                              Prefetch('associated_users',
                                       queryset=UserResultArea.objects.all()))

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.core_tasks.exists() or instance.associated_users.exists():
            return Response(
                {'detail': 'RA having associated core tasks or result areas assigned cannot be deleted'},
                status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CoreTaskViewSet(OrganizationMixin, CreateRetrieveUpdateDestroyViewSetMixin):
    serializer_class = CoreTaskSerializer
    queryset = CoreTask.objects.all().select_related('result_area')
    permission_classes = [TaskResultAreaAndCoreTaskPermission]

    def get_queryset(self):
        return super().get_queryset().filter(result_area=self.result_area)

    def dispatch(self, *args, **kwargs):
        _ = self.result_area
        return super().dispatch(*args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.userresultarea_set.exists():
            return Response({
                'detail': 'CoreTask associated with ResultArea cannot be deleted'},
                status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({'result_area': self.result_area})
        return ctx

    @cached_property
    def result_area(self):
        result_area_id = self.kwargs.get('result_area_id')
        if result_area_id:
            try:
                return ResultArea.objects.get(id=result_area_id, division__organization=self.get_organization())
            except (TypeError, ValueError, DjValidationError, ResultArea.DoesNotExist):
                raise Http404
        return None


class UserCoreTaskListRetrieveViewSet(ListRetrieveViewSetMixin):
    """
    ViewSet to list the users with their assigned experiences and attached
    result areas.
    """
    queryset = USER.objects.all().current().order_by('first_name')
    serializer_class = UserResultAreaListSerializer
    filter_backends = (
        FilterMapBackend,
        NullsAlwaysLastOrderingFilter,
        SearchFilter
    )

    filter_map = {
        'division': 'detail__division__slug'
    }
    search_fields = (
        'first_name', 'middle_name', 'last_name'
    )
    ordering_fields_map = {
        'full_name': (
            'first_name', 'middle_name', 'last_name'
        ),
    }

    def get_queryset(self):
        return super().get_queryset().filter(
            detail__organization__slug=self.kwargs['organization_slug']
        ).select_related(
            'detail', 'detail__organization', 'detail__division',
            'detail__job_title', 'detail__employment_level',
            'detail__employment_status'
        ).prefetch_related(
            Prefetch(
                'user_experiences',
                queryset=UserExperience.objects.select_related(
                    'organization', 'job_title'
                ).prefetch_related(
                    Prefetch(
                        'user_result_areas',
                        queryset=UserResultArea.objects.order_by(
                            'result_area__title'
                        ).prefetch_related(
                            Prefetch(
                                'core_tasks',
                                queryset=CoreTask.objects.order_by(
                                    'order'
                                )
                            )
                        )
                    )
                )
            )
        )


class UserAssignCoreTaskViewSet(CreateViewSetMixin):
    queryset = UserResultArea.objects.all()
    serializer_class = UserResultAreaSerializer
    permission_classes = [permission_factory.build_permission(
        "CoreTaskAssignPermission",
        allowed_to=[
            CORE_TASK_RELATED_PERMISSIONS,
            ASSIGN_CORE_TASK_PERMISSION
        ]
    )]

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def get_organization(self):
        user = self.request.user
        if not user and user.is_authenticated:
            return None
        org_slug = self.request.query_params.get('organization_slug')
        return Organization.objects.filter(
            id__in=self.request.user.switchable_organizations_pks,
            slug=org_slug
        ).first()
