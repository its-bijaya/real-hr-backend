from rest_framework.fields import ReadOnlyField

from irhrs.users.api.v1.serializers.thin_serializers import UserFieldThinSerializer, UserThinSerializer


class AdjustmentReportSerializer(UserFieldThinSerializer):
    supervisor = UserThinSerializer(source='first_level_supervisor')
    punch_in_frequency = ReadOnlyField(allow_null=True)
    punch_out_frequency = ReadOnlyField(allow_null=True)
    total = ReadOnlyField(allow_null=True)
