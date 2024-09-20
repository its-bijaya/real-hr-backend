from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import UserDetail


class ReportSerializer(ModelSerializer):
    user = UserThinSerializer()
    yos = SerializerMethodField()

    class Meta:
        model = UserDetail
        fields = ('user', 'yos')

    def get_yos(self, obj):
        return obj.duration.days // 365
