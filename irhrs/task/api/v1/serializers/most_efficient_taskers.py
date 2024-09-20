from django.contrib.auth import get_user_model
from rest_framework import serializers

from irhrs.core.mixins.serializers import DummySerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

USER = get_user_model()


class MostEfficientTaskers(DummySerializer):
    user = serializers.SerializerMethodField()
    total_efficiency = serializers.FloatField()

    @staticmethod
    def get_user(obj):
        user = USER.objects.get(id=obj['user'])
        return UserThinSerializer(instance=user,
                                  fields=('id', 'full_name', 'profile_picture',
                                          'cover_picture', 'division', 'organization', 'is_current',
                                          'job_title')).data
