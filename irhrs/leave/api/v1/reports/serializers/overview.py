from rest_framework.fields import ReadOnlyField

from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class MostLeaveActionSerializer(UserThinSerializer):
    count = ReadOnlyField()

    class Meta(UserThinSerializer.Meta):
        fields = ["id", "full_name", "profile_picture", "cover_picture", 'organization', 'is_current', "job_title", "is_online", "count"]
