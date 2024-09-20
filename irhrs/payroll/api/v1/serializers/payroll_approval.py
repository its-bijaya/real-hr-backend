from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.payroll.models import PayrollApprovalHistory
from irhrs.users.api.v1.serializers.thin_serializers import UserThumbnailSerializer


class PayrollApprovalHistorySerializer(DynamicFieldsModelSerializer):
    message = serializers.SerializerMethodField()
    actor = UserThumbnailSerializer()

    class Meta:
        model = PayrollApprovalHistory
        fields = (
            'id', 'actor', 'action', 'message', 'created_at'
        )

    def get_message(self, instance):
        if instance.action == 'deleted':
            return f"Deleted {instance.remarks}"
        return instance.__str__()
