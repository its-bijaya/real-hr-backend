from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

from ....models.task import TaskComment


class TaskCommentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TaskComment
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['created_by'] = UserThinSerializer(
                read_only=True,
                fields=('id', 'profile_picture', 'full_name')
            )
        return fields

    def create(self, validated_data):
        validated_data.update({'task': self.context.get('task')})
        comment = super().create(validated_data)
        self.fields['created_by'] = UserThinSerializer(
            read_only=True,
            fields=('id', 'profile_picture', 'full_name')
        )
        return comment
