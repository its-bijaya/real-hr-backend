from django.contrib.auth import get_user_model
from django.db.models import Q, Prefetch

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend

from irhrs.core.utils.common import validate_permissions
from irhrs.permission.constants.permissions import TASK_PERMISSION, TASK_PROJECT_PERMISSION
from irhrs.task.api.v1.permissions import TaskProjectWritePermission, \
    TaskProjectPermission
from irhrs.users.models import UserExperience
from ..serializers.project import TaskProjectSerializer
from ..serializers.task import TaskSerializer
from ....models.task import TaskProject


class TaskProjectViewSet(ModelViewSet):
    """
        create:

            create a project

                {
                  "name": "First Project",
                  "members": [
                    1,2, ...........
                  ],
                  "description": "Long Description"
                }
        list:

            list all the projects
            defaults to normal user view

        retrieve:

            retrieve details of a project

        destroy:
            Delete a project , will not delete Tasks associated inside this project

    """

    http_method_names = [u'get', u'post', u'patch', u'delete']
    serializer_class = TaskProjectSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    permission_classes = [TaskProjectPermission]
    search_fields = (
        "name",
        "description",
    )

    ordering_fields = (
        'id',
        'created_at',
    )
    filter_fields = ('members',)

    def get_queryset(self):
        role = self.request.query_params.get('as', 'user')
        if role not in ['user', 'HR']:
            role = 'user'
        if role == 'HR':
            if validate_permissions(
                self.request.user.get_hrs_permissions(),
                TASK_PERMISSION,
                TASK_PROJECT_PERMISSION
            ):
                return TaskProject.objects.all()
        return TaskProject.objects.filter(
            Q(created_by=self.request.user) | Q(members__in=[self.request.user])
        ).select_related(
            'created_by', 'created_by__detail'
        ).prefetch_related(
            Prefetch('members', queryset=get_user_model().objects.select_related(
                'detail', 'detail__organization'
            ).prefetch_related(
                Prefetch('user_experiences',
                         queryset=UserExperience.objects.filter(
                             is_current=True)
                         .select_related('division'),
                         to_attr='_current_experiences'))
                     )
        ).distinct()

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.created_by == self.request.user or TASK_PERMISSION['code'] in \
                    self.request.user.get_hrs_permissions():
            return super().update(request, *args, **kwargs)
        return Response({'detail': 'You are not authorized '
                                   'to perform this action'},
                        status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.created_by == self.request.user or TASK_PERMISSION['code'] in \
                self.request.user.get_hrs_permissions():
            return super().destroy(request, *args, **kwargs)
        return Response({'detail': 'You are not authorized '
                                   'to perform this action'},
                        status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """
        Task involved in the project
        """
        instance = self.get_object()
        if not (
            validate_permissions(
                self.request.user.get_hrs_permissions(),
                TASK_PERMISSION,
                TASK_PROJECT_PERMISSION
            ),
            instance.created_by == self.request.user
            or self.request.user.taskproject_set.filter(pk=instance.id).exists()
        ):
            return Response({'detail': 'You are not authorized to perform this action'},
                            status=status.HTTP_403_FORBIDDEN)
        task_obj = instance.project_tasks.filter(
            deleted_at__isnull=True,
            recurring_rule__isnull=True
        )
        page = self.paginate_queryset(task_obj)
        if page is not None:
            serializer = TaskSerializer(page, many=True, context=self.get_serializer_context())
            resp = self.get_paginated_response(serializer.data)
            return resp
        return Response
