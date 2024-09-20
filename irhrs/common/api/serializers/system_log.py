from irhrs.common.models.system_email_log import SystemEmailLog
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class SystemEmailLogSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer()

    class Meta:
        model = SystemEmailLog
        fields = (
            'user', 'subject', 'status', 'sent_address', 'text_message',
            'html_message', 'created_at', 'id'
        )

    def get_fields(self):
        require_details = self.context.get('show_details', False)
        ret = super().get_fields()
        if require_details:
            return ret
        else:
            ret.pop('html_message', None)
        return ret
