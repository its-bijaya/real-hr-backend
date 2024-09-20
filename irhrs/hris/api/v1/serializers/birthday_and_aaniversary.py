from rest_framework.fields import ReadOnlyField

from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import User


class UpcomingBirthdaySerializer(UserThinSerializer):
    birthday = ReadOnlyField(source='next_birthday')

    class Meta:
        model = User
        fields = UserThinSerializer.Meta.fields + ['birthday']


class UpcomingAnniversarySerializer(UserThinSerializer):
    anniversary = ReadOnlyField(source='next_anniversary')

    class Meta:
        model = User
        fields = UserThinSerializer.Meta.fields + ['anniversary']
