from rest_framework import serializers

from irhrs.leave.models import LeaveAccount


class EmployeeProfileLeaveSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    category = serializers.ReadOnlyField(source='rule.leave_type.category')
    consumed_balance = serializers.FloatField()
    # remaining_balance = serializers.SerializerMethodField()

    class Meta:
        model = LeaveAccount
        fields = [
            'type',
            'consumed_balance',
            'usable_balance',
            'category'
        ]

    def get_type(self, obj):
        return str(obj.rule.leave_type)
