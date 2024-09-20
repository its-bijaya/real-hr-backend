from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.task.constants import TASK_ATTACHMENT_MAX_UPLOAD_SIZE

from ....models.task import TaskAttachment


class TaskAttachmentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TaskAttachment
        fields = '__all__'

    def create(self, validated_data):
        validated_data.update({'task': self.context.get('task')})
        return super().create(validated_data)

    @staticmethod
    def validate_attachment(attachment):
        if attachment.size > TASK_ATTACHMENT_MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f'File Size Should not Exceed {TASK_ATTACHMENT_MAX_UPLOAD_SIZE / (1024 * 1024)} MB')
        return attachment
