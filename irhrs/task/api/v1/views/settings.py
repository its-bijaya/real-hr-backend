from django.db.models import Q
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend, FilterSet

from irhrs.core.mixins.viewset_mixins import OrganizationMixin, RetrieveUpdateViewSetMixin, \
    ListCreateUpdateDestroyViewSetMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import OrderingFilterMap, SearchFilter
from irhrs.permission.constants.permissions import TASK_PERMISSION, TASK_PROJECT_PERMISSION

from irhrs.task.api.v1.permissions import TaskSettingsPermission
from irhrs.task.api.v1.serializers.settings import TaskSettingsSerializer, ProjectListSerializer, \
    ProjectCreateSerializer, ActivitySerializer, AssignEmployeeActivityToProjectSerializer, \
    UserActivitySerializer
from irhrs.task.models.settings import Project, Activity, UserActivityProject
from irhrs.task.models.settings import TaskSettings


class UserActivityProjectFilter(FilterSet):
    class Meta:
        model = UserActivityProject
        fields = ['user_id', 'activity_id']


class ProjectFilter(FilterSet):
    class Meta:
        model = Project
        fields = ['user_activity_projects__user', 'is_billable']


class TaskSettingsView(OrganizationMixin, RetrieveUpdateViewSetMixin):
    queryset = TaskSettings.objects.all()
    serializer_class = TaskSettingsSerializer
    lookup_url_kwarg = 'organization_slug'

    permission_classes = [TaskSettingsPermission]

    def get_object(self):
        return TaskSettings.get_for_organization(self.organization)


class ProjectApiViewSet(ModelViewSet):
    queryset = Project.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilterMap, SearchFilter)
    search_fields = ('name', )
    ordering_fields_map = {
        "name": "name",
        "created_by": "created_by",
        "start_date": "start_date",
        "end_date": "end_date"
    }
    filter_class = ProjectFilter
    serializer_class = ProjectListSerializer

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode not in ['hr', 'supervisor']:
            return 'user'

        return mode

    def get_queryset(self):
        if self.action == "user_activity":
            return UserActivityProject.objects.filter(project=self.kwargs.get('pk'))

        if self.mode == 'hr':
            if validate_permissions(
                self.request.user.get_hrs_permissions(),
                TASK_PERMISSION,
                TASK_PROJECT_PERMISSION
            ):
                return Project.objects.all()

        return Project.objects.filter(
            Q(user_activity_projects__user=self.request.user)
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return ProjectCreateSerializer
        return super().get_serializer_class()

    # @action(
    #     methods=["GET"], detail=True, url_path='user-activity',
    #     serializer_class=UserActivitySerializer
    # )
    # def user_activity(self, request, pk=None):
    #     if not (self.mode == 'hr' and validate_permissions(
    #             self.request.user.get_hrs_permissions(),
    #             TASK_PERMISSION,
    #             TASK_PROJECT_PERMISSION
    #     )):
    #         raise PermissionDenied
    #
    #     data = self.get_serializer(
    #         self.paginate_queryset(self.get_queryset()),
    #         many=True
    #     ).data
    #     return self.get_paginated_response(data=data)

    @action(
        methods=["POST"], detail=True, url_path="assign-employee-activity",
        serializer_class=AssignEmployeeActivityToProjectSerializer
    )
    def assign_employee_activity(self, request, pk=None):
        if not (self.mode == 'hr' and validate_permissions(
                self.request.user.get_hrs_permissions(),
                TASK_PERMISSION,
                TASK_PROJECT_PERMISSION
        )):
            raise PermissionDenied
        ser = AssignEmployeeActivityToProjectSerializer(
            data=request.data, context={'project_id': pk}
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class UserActivityViewSet(ModelViewSet):
    queryset = UserActivityProject.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilterMap, SearchFilter)
    search_fields = (
        'user__first_name', 'user__middle_name', 'user__last_name', "activity__name"
    )
    ordering_fields_map = {
        "user": ('user__first_name', 'user__middle_name', 'user__last_name'),
        "activity": "activity__name",
        "employee_rate": "employee_rate",
        "client_rate": "client_rate"
    }
    filter_class = UserActivityProjectFilter
    serializer_class = UserActivitySerializer

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode not in ['hr', 'supervisor']:
            return 'user'

        return mode

    def get_queryset(self):
        queryset = super().get_queryset().filter(project=self.kwargs.get('project_id'))
        if self.mode == 'user':
            return queryset.filter(user=self.request.user)
        if self.mode == 'hr' and not validate_permissions(
                self.request.user.get_hrs_permissions(),
                TASK_PERMISSION,
                TASK_PROJECT_PERMISSION
        ):
            raise PermissionDenied
        return queryset

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['stats'] = {
            "activity": self.filter_queryset(self.get_queryset()).values('activity').count()
        }
        return response


class ActivityApiViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilterMap, SearchFilter)
    ordering_fields_map = {
        "name": "name",
        "unit": "unit",
        "employee_rate": "employee_rate",
        "client_rate": "client_rate"
    }
    search_fields = (
        'name', 'unit'
    )
    serializer_class = ActivitySerializer

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode not in ['hr', 'supervisor']:
            return 'user'

        return mode

    def get_queryset(self):
        if self.mode == 'hr':
            if validate_permissions(
                self.request.user.get_hrs_permissions(),
                TASK_PERMISSION,
                TASK_PROJECT_PERMISSION
            ):
                return Activity.objects.all()

        return Activity.objects.filter(created_by=self.request.user)
