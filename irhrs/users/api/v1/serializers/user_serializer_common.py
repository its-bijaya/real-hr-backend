from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.utils.notification import send_change_notification_to_user
from .thin_serializers import UserThinSerializer


class UserSerializerMixin(DynamicFieldsModelSerializer):
    def create(self, validated_data):
        user = self.context.get('user')
        validated_data.update({
            'user': user
        })
        instance = super().create(validated_data)

        # send_notification disable feature
        if self.context.get('send_notification', True):
            send_change_notification_to_user(
                self=self,
                instance=instance,
                user=instance.user,
                actor=self.request.user,
                action='created'
            )
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if self.context.get('send_notification', True):
            send_change_notification_to_user(
                self=self,
                instance=instance,
                user=instance.user,
                actor=self.request.user,
                action='updated'
            )
        return instance

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            if 'user' in fields:
                fields['user'] = UserThinSerializer(read_only=True)
        return fields
