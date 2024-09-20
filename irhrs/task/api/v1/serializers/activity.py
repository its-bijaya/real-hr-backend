from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

from ....models.task import TaskActivity

from .task import TaskSerializer


class TaskActivitySerializer(DynamicFieldsModelSerializer):
    created_by = UserThinSerializer(fields=('id', 'full_name', 'profile_picture'), read_only=True)
    task = TaskSerializer(fields=('id', 'title', 'description'))

    class Meta:
        model = TaskActivity
        fields = ('task',
                  'previous_value', 'previous_value_display', 'present_value',
                  'present_value_display', 'key', 'description', 'created_by',
                  'created_at')
