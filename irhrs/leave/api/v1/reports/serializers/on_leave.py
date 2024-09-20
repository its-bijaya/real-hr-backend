from django.contrib.auth import get_user_model
from rest_framework import serializers


from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer

User = get_user_model()


class OnLeaveSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()
    user_object = None

    def get_user(self, instance):
        return UserThinSerializer(
            instance.user
        ).data
