from rest_framework.fields import ReadOnlyField

from irhrs.common.models.user_activity import UserActivity
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class UserActivitySerializer(DynamicFieldsModelSerializer):
    actor = UserThinSerializer(read_only=True)
    message = ReadOnlyField()
    category = ReadOnlyField()
    created_at = ReadOnlyField()

    class Meta:
        model = UserActivity
        fields = ['actor', 'message', 'category', 'created_at']
