from rest_framework import serializers

from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class HierarchyChartSerializer(serializers.Serializer):
    user = UserThinSerializer(read_only=True,
                              fields=['id',
                                      'full_name',
                                      'profile_picture',
                                      'cover_picture',
                                      'job_title',
                                      'employee_level',
                                      'organization',
                                      'is_current',                                    
                                      'is_online']
                              )

    relationship = serializers.CharField(read_only=True)
