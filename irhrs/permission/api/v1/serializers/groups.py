from django.contrib.auth.models import Group
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThumbnailSerializer


class UserGroupSerializer(DynamicFieldsModelSerializer):
    user_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'user_count', 'user_set']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method.upper() == 'GET':
            fields['user_set'] = UserThumbnailSerializer(many=True)
        return fields
