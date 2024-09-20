from django.contrib.auth import get_user_model
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject
from irhrs.hris.models.email_setting import EmailSetting
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

User = get_user_model()


class EmailSettingSerializer(DynamicFieldsModelSerializer):
    leave = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
    profile_picture = serializers.ReadOnlyField(
        source='profile_picture_thumb', allow_null=True
    )
    cover_picture = serializers.ReadOnlyField(
        source='cover_picture_thumb', allow_null=True
    )

    class Meta:
        model = User
        fields = ['id', 'full_name', 'profile_picture', 'cover_picture', 'job_title', 'is_online',
                  'leave']

    @staticmethod
    def get_leave(obj):
        return obj.email_setting.first().leave

    @staticmethod
    def get_job_title(obj):
        detail = obj.detail if hasattr(obj, 'detail') else None
        return detail.job_title.title if detail and detail.job_title else 'Job Title N/A'


class EmailSettingPostSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = EmailSetting
        fields = ['user', 'leave']

    def get_fields(self):
        fields = super().get_fields()
        fields['user'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.filter(
                detail__organization=self.context.get('organization')
            ).current(),
            many=True
        )
        return fields

    def create(self, validated_data):
        leave = validated_data.get('leave')
        users = validated_data.get('user')
        _ = EmailSetting.objects.filter(user__in=users).update(leave=leave)
        return DummyObject(**validated_data)
