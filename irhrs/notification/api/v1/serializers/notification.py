from rest_framework.fields import DateTimeField

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    DummySerializer
from irhrs.core.validators import validate_future_datetime
from irhrs.notification.models.notification import OrganizationNotification
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from ....models import Notification


class NotificationSerializer(DynamicFieldsModelSerializer):
    actor = UserThinSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = ["id", "actor", "read", "text", "sticky",
                  "notify_on", "can_be_reminded", "url",
                  "is_interactive", "interactive_type", "interactive_data"]


class NotificationReminderSerializer(DummySerializer):
    remind_at = DateTimeField(validators=[validate_future_datetime],
                              required=True)


class OrganizationNotificationSerializer(DynamicFieldsModelSerializer):
    actor = UserThinSerializer(
        read_only=True,
        allow_null=True
    )
    # modified_by = UserThinSerializer(
    #     read_only=True,
    #     allow_null=True
    # )

    class Meta:
        model = OrganizationNotification
        fields = (
            'actor',  # 'modified_by',
            'created_at',  # 'modified_at',
            'text', 'url', 'label', 'is_resolved', 'id',
            "is_interactive", "interactive_type", "interactive_data"
        )
