from django.http import Http404
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import ListCreateDestroyViewSetMixin
from irhrs.task.constants import TASK_ATTACHMENT_MAX_UPLOAD_SIZE, PENDING
from ....models.task import TaskAttachment, Task
from ..serializers.attachment import TaskAttachmentSerializer


class TaskAttachmentViewSet(ListCreateDestroyViewSetMixin):
    serializer_class = TaskAttachmentSerializer
    queryset = TaskAttachment.objects.all()
    parser_classes = (MultiPartParser, FormParser,)

    @staticmethod
    def _get_task(task_id):
        try:
            task = Task.objects.get(id=task_id)
        except (Task.DoesNotExist, ValueError):
            raise Http404
        return task

    def get_queryset(self):
        task = self._get_task(self.kwargs.get('task_id'))
        if not (task.created_by == self.request.user or
                task.task_associations.filter(
                    user=self.request.user).exists()
        ):
            return TaskAttachment.objects.none()
        return task.task_attachments.all()

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
        if not (task_obj.created_by == self.request.user or
                task_obj.task_associations.filter(
                    user=self.request.user).exists()
        ):
            return Response({'detail': 'You are not authorized to perform this action'},
                            status=status.HTTP_403_FORBIDDEN)
        if task_obj.approved:
            return Response({'detail': 'Cannot create attachments on approved tasks'},
                            status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        task_obj = self._get_task(self.kwargs.get('task_id'))
        if task_obj.approved:
            return Response({'detail': 'Cannot delete attachments on approved tasks'},
                            status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object()
        if instance.created_by != self.request.user:
            return Response({'detail': 'You are not authorized to perform this action'},
                            status=status.HTTP_403_FORBIDDEN)
        if task_obj.created_by == instance.created_by:  # this means creator of task uploaded the attachment
            if task_obj.status != PENDING:
                return Response({'detail': 'Can only delete attachment when Task Status is Pending'},
                                status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


TaskAttachmentViewSet.__doc__ = """
        create:

                Create Attachments for Task
                Max Size : {} MB

        """.format(TASK_ATTACHMENT_MAX_UPLOAD_SIZE / (1024 * 1024))
