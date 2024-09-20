from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from ....models.task import TaskCheckList


class TaskChecklistSerializer(DynamicFieldsModelSerializer):
    created_by = UserThinSerializer(fields=('id', 'full_name', 'profile_picture'), read_only=True)
    completed_by = UserThinSerializer(fields=('id', 'full_name', 'profile_picture'), read_only=True)
    # Due to frontend problem of mapping the errors , title has been changed to check_list_title
    check_list_title = serializers.CharField(source='title', max_length=100)

    class Meta:
        model = TaskCheckList
        fields = [
            'id', 'check_list_title', 'created_by', 'completed_by',
            'completed_on', 'created_at', 'modified_at'
        ]
        read_only_fields = ('completed_by', 'completed_on', 'created_at', 'modified_at')

    def create(self, validated_data):
        task = self.context.get('task')
        validated_data.update({
            'task': task,
            'order': TaskCheckList.objects.filter(task=task).count() + 1
        })
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.update({'task': instance.task})
        return super().update(instance, validated_data)
