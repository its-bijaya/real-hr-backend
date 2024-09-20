from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer

from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer
from ....models import MessageToUser


class MessageToUserSerializer(DynamicFieldsModelSerializer):
    created_by = UserThinSerializer(read_only=True)

    class Meta:
        model = MessageToUser
        fields = (
            'title', 'slug', 'message', 'created_by', 'published',
            'message_from', 'created_at', 'modified_at', 'archived'
        )
        read_only_fields = ('slug',)

    def validate(self, attrs):
        attrs.update({
            'created_by': self.context.get('userdetail')
        })
        return super().validate(attrs)

    def get_fields(self):
        ret = super().get_fields()
        if self.request:
            if self.request.method == 'GET':
                ret.update({
                    'message_from': UserThinSerializer()
                })
        return ret
