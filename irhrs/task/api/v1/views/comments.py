from django.http import Http404

from rest_framework import status
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import ListCreateDestroyViewSetMixin
from irhrs.permission.constants.permissions import TASK_PERMISSION
from ..serializers.comments import TaskCommentSerializer
from ....models.task import TaskComment, Task
from irhrs.task.constants import RESPONSIBLE_PERSON


class TaskCommentViewSet(ListCreateDestroyViewSetMixin):
    serializer_class = TaskCommentSerializer

    @staticmethod
    def _get_task(task_id):
        try:
            task = Task.objects.get(id=task_id)
        except (Task.DoesNotExist, ValueError):
            raise Http404
        return task

    def get_queryset(self):
        task = self._get_task(self.kwargs.get('task_id'))
        user = self.request.user
        if self.action == 'list':
            if TASK_PERMISSION.get('code') in \
                    user.get_hrs_permissions():
                return task.task_comments.all()
            responsible_persons = task.task_associations.filter(
                association=RESPONSIBLE_PERSON
            ).values_list(
                'user',
                flat=True)
            from irhrs.core.utils.subordinates import find_all_subordinates
            for person in responsible_persons:
                if person in find_all_subordinates(user.id):
                    return task.task_comments.all()
        if not (
                task.created_by == user or task.task_associations.filter(
                user=user).exists()):
            return TaskComment.objects.none()
        return task.task_comments.all()

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
        if not (
                task_obj.created_by == self.request.user or task_obj.task_associations.filter(
                user=self.request.user).exists()):
            return Response(
                {'detail': 'You are not authorized to perform this action'},
                status=status.HTTP_403_FORBIDDEN)
        if task_obj.approved:
            return Response(
                {'detail': 'Cannot create comments on approved tasks'},
                status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        task_obj = self._get_task(self.kwargs.get('task_id'))
        obj = self.get_object()
        if not (
                task_obj.created_by == self.request.user or obj.created_by == self.request.user):
            return Response(
                {'detail': 'You are not authorized to perform this action'},
                status=status.HTTP_403_FORBIDDEN)
        if task_obj.approved:
            return Response(
                {'detail': 'Cannot destroy comments from approved tasks'},
                status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)
