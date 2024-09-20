from django.http import Http404
from rest_framework import status
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import ListCreateDestroyViewSetMixin
from irhrs.task.api.v1.serializers.reminder import TaskReminderSerializer
from irhrs.task.models import Task
from irhrs.task.models.task import TaskReminder, TaskAssociation


class TaskReminderViewSet(ListCreateDestroyViewSetMixin):
    serializer_class = TaskReminderSerializer
    queryset = TaskReminder.objects.all()

    @staticmethod
    def _get_task(task_id):
        try:
            task = Task.objects.get(id=task_id)
        except (Task.DoesNotExist, ValueError):
            raise Http404
        return task

    def get_queryset(self):
        task = self._get_task(self.kwargs.get('task_id'))
        return task.task_task_reminder.filter(created_by=self.request.user)

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
        if task_obj.created_by == self.request.user or \
                TaskAssociation.objects.filter(task=task_obj,
                                               user=self.request.user
                                               ).exists():
            if task_obj.approved:
                Response({'detail': 'Cannot set reminder on completed tasks'},
                         status=status.HTTP_400_BAD_REQUEST)
            return super().create(request, *args, **kwargs)
        return Response(
            {'detail': 'You are not authorized to perform this action'},
            status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        task_obj = self._get_task(self.kwargs.get('task_id'))
        if task_obj.approved:
            Response({'detail': 'Cannot delete reminder for completed tasks'},
                     status=status.HTTP_403_FORBIDDEN)
        obj = self.get_object()
        if obj.created_by == self.request.user or obj.user == self.request.user:
            if obj.sent_on:
                return Response(
                    {'detail': 'Reminder for the task has already been sent'},
                    status=status.HTTP_400_BAD_REQUEST)

            return super().destroy(request, *args, **kwargs)
        return Response(
            {'detail': 'You are not authorized to perform this action'},
            status=status.HTTP_403_FORBIDDEN)
