from irhrs.core.mixins.serializers import DummySerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from rest_framework import serializers


class WorkLogOverViewSerializer(UserThinSerializer):
    total_work_logs = serializers.IntegerField()
    total_score = serializers.IntegerField()
    average_score = serializers.FloatField()
    efficiency = serializers.FloatField()
    supervisor = UserThinSerializer(source='first_level_supervisor')

    class Meta(UserThinSerializer.Meta):
        fields = UserThinSerializer.Meta.fields + ['total_work_logs',
                                                   'total_score',
                                                   'average_score',
                                                   'efficiency','supervisor']


class WorkLogScoreDistributionOverviewSerializer(DummySerializer):
    user = UserThinSerializer(fields=('id', 'full_name',), source='created_by',
                              read_only=True)
    score = serializers.IntegerField(read_only=True)
    date = serializers.DateField(read_only=True)
