from rest_framework import serializers

from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import UserDetail

USER_FIELDS = ['id', 'full_name', 'profile_picture', 'cover_picture',
               'division', 'organization', 'job_title', 'employee_level',
               ''
               ]


class ProfileCompletenessSerializer(serializers.ModelSerializer):
    user_detail = UserThinSerializer(
        fields=USER_FIELDS,
        read_only=True,
        source='user'
    )
    branch = serializers.ReadOnlyField(source="user.detail.branch.name")
    joined_date = serializers.ReadOnlyField(source="user.detail.joined_date")
    completeness_percent= serializers.ReadOnlyField(source="user.profile_completeness")                 

    class Meta:
        model = UserDetail
        fields = [
            'id', 'user_detail', 'branch', 'joined_date', 'completeness_percent'
        ]
