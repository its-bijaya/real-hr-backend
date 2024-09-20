from django.utils import timezone
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from ....models.task import TaskReminder


class TaskReminderSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TaskReminder
        fields = '__all__'
        read_only_fields = 'created_by', 'sent_on', 'task', 'status', 'extra_data'

    def validate_remind_on(self, value):
        if value < self.context.get('task').starts_at:
            raise serializers.ValidationError(
                'Should be greater than task start time')
        if value < timezone.now():
            raise serializers.ValidationError('Should be in future')
        return value

    def validate_user(self, user):
        if self.context.get('task').task_associations.filter(
                user=user
        ).exists() or self.context.get('task').created_by == user:
            return user
        raise serializers.ValidationError('User is not associated '
                                          'with this Task')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['user'] = UserThinSerializer(
                fields=('id', 'full_name', 'profile_picture'), read_only=True)
            fields['created_by'] = UserThinSerializer(
                fields=('id', 'full_name', 'profile_picture'), read_only=True)
        return fields

    def create(self, validated_data):
        validated_data.update({
            'task': self.context.get('task')
        })
        self.fields['user'] = UserThinSerializer(
            fields=('id', 'full_name', 'profile_picture'))
        self.fields['created_by'] = UserThinSerializer(
            fields=('id', 'full_name', 'profile_picture'))
        return super().create(validated_data)

    def update(self, instance: TaskReminder, validated_data):
        validated_data.update({'user': instance.user})
        self.fields['user'] = UserThinSerializer(
            fields=('id', 'full_name', 'profile_picture'))
        self.fields['created_by'] = UserThinSerializer(
            fields=('id', 'full_name', 'profile_picture'))
        return super().update(instance, validated_data)
