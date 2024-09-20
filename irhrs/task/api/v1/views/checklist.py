from django.http import Http404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.permission.constants.permissions import TASK_PERMISSION
from ..serializers.checklist import TaskChecklistSerializer
from ....constants import IN_PROGRESS, RESPONSIBLE_PERSON

from ....models.task import TaskCheckList, Task


class TaskChecklistViewSet(ModelViewSet):
    serializer_class = TaskChecklistSerializer

    @staticmethod
    def _get_task(task_id):
        try:
            task = Task.objects.get(id=task_id)
        except (Task.DoesNotExist, ValueError):
            raise Http404
        return task

    def get_queryset(self):
        task = self._get_task(self.kwargs.get('task_id'))
        if self.action == 'list':
            if TASK_PERMISSION.get('code') in \
                    self.request.user.get_hrs_permissions():
                return task.task_checklists.all()
        if not (task.created_by == self.request.user or
                task.task_associations.filter(
                    user=self.request.user).exists()):
            return TaskCheckList.objects.none()
        return task.task_checklists.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # temp :HACK
        try:
            task = self._get_task(self.kwargs.get('task_id'))
        except Exception as e:
            task = None
        context['task'] = task
        return context

    def create(self, request, *args, **kwargs):
        task_obj = self._get_task(self.kwargs.get('task_id'))
        if not task_obj.created_by == self.request.user:
            return Response(
                {'detail': 'You are not authorized to perform this action'},
                status=status.HTTP_403_FORBIDDEN)
        if task_obj.approved:
            return Response(
                {'detail': 'Cannot create checklists on completed tasks'},
                status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        task_obj = self._get_task(self.kwargs.get('task_id'))
        if not task_obj.created_by == self.request.user:
            return Response(
                {'detail': 'You are not authorized to perform this action'},
                status=status.HTTP_403_FORBIDDEN)
        if task_obj.approved:
            return Response(
                {'detail': 'Cannot update checklists from completed tasks'},
                status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        task_obj = self._get_task(self.kwargs.get('task_id'))
        if not task_obj.created_by == self.request.user:
            return Response(
                {'detail': 'You are not authorized to perform this action'},
                status=status.HTTP_403_FORBIDDEN)
        if task_obj.approved:
            return Response(
                {'detail': 'Cannot Delete checklists from completed tasks'},
                status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object()
        if instance.completed_on:
            return Response(
                {'detail': 'Cannot Delete checklists after completion'},
                status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=True, methods=['post'])
    def check(self, request, task_id, pk=None):
        task_obj = self._get_task(self.kwargs.get('task_id'))
        # INFO : AS for REQUIREMENT , checklists can only be completed by Responsible Person
        # if not (task_obj.created_by == self.request.user or task_obj.task_associations.filter(
        #         user=self.request.user, association=RESPONSIBLE_PERSON).exists()):
        if not task_obj.task_associations.filter(
                user=self.request.user,
                association=RESPONSIBLE_PERSON).exists():
            return Response(
                {'detail': 'You are not authorized to perform this action'},
                status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        if task_obj.approved:
            return Response({
                'detail': 'Cannot check/uncheck checklists of '
                          'completed tasks'},
                status=status.HTTP_400_BAD_REQUEST)
        if task_obj.status != IN_PROGRESS:
            return Response({
                'detail': 'Can check/uncheck checklists '
                          'for In Progress tasks only'},
                status=status.HTTP_400_BAD_REQUEST)
        instance.completed_by = self.request.user if not instance.completed_by else None
        instance.completed_on = timezone.now() if not instance.completed_on else None
        instance.save()
        ser = TaskChecklistSerializer(instance)
        return Response(ser.data)
