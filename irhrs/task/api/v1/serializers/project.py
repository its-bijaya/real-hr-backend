from django.contrib.auth import get_user_model
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.task.models.task import TaskProject
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

USER = get_user_model()


class TaskProjectSerializer(DynamicFieldsModelSerializer):
    members = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=USER.objects.all()),
        required=False, write_only=True)
    created_by = UserThinSerializer(
        fields=(
        'id', 'full_name', 'profile_picture', 'cover_picture', 'division',
        'organization', 'is_current', 'job_title'),
        read_only=True)

    class Meta:
        model = TaskProject
        fields = 'id', 'name', 'created_by', 'members', 'description',

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['members'] = UserThinSerializer(many=True)
        return fields

    def create(self, validated_data):
        members = None
        if 'members' in validated_data.keys():
            members = validated_data.pop('members', None)
        validated_data.update({'created_by': self.request.user})
        project = super().create(validated_data)
        if members:
            project.members.add(*members)
            self.fields['members'] = UserThinSerializer(many=True)
        return project

    def update(self, instance, validated_data):
        if 'members' in validated_data.keys():
            members = validated_data.pop('members', None)
            if members:
                instance.members.clear()
                instance.members.add(*members)
            else:
                instance.members.clear()
            self.fields['members'] = UserThinSerializer(many=True)
        return super().update(instance, validated_data)
