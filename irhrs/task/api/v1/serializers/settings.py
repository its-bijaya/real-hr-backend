import math

from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.hris.models import User
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.task.models.settings import TaskSettings, Project, Activity, UserActivityProject


class TaskSettingsSerializer(ModelSerializer):
    class Meta:
        model = TaskSettings
        fields = ('can_assign_to_higher_employment_level', )


class ProjectListSerializer(DynamicFieldsModelSerializer):
    member_count = serializers.SerializerMethodField()
    created_by = UserThinSerializer(fields=('id', 'full_name', 'profile_picture'), read_only=True)

    class Meta:
        model = Project
        fields = (
            'id', 'name', 'description', 'start_date', 'end_date', 'is_billable', 'created_by',
            'member_count'
        )

    def get_member_count(self, obj):
        return obj.user_activity_projects.values('user').count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('name', 'description', 'start_date', 'end_date', 'is_billable')

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date and end_date and (start_date > end_date):
            raise ValidationError({
                "end_date": "End date must be greater than start date"
            })
        return attrs


class ActivitySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Activity
        fields = ('id', 'name', 'description', 'unit', 'employee_rate', 'client_rate')

    def validate(self, attrs):
        employee_rate = attrs.get('employee_rate')
        client_rate = attrs.get('client_rate')
        if math.isinf(employee_rate):
            raise ValidationError({
                "employee_rate": "Float value is too big"
            })
        if math.isinf(client_rate):
            raise ValidationError({
                "client_rate": "Float value is too big"
            })
        return attrs

    def update(self, instance, validated_data):
        if UserActivityProject.objects.filter(activity=instance).exists() and (
            instance.unit != validated_data.get('unit')
        ):
            raise ValidationError({
                "unit": "Cannot update when activity is assigned to project."
            })
        return super().update(instance, validated_data)


class UserActivitySerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(
        fields=('id', 'full_name', 'profile_picture', 'job_title'),
        read_only=True
    )
    activity = ActivitySerializer(fields=('id', 'name', 'unit'), read_only=True)

    def get_fields(self):
        fields = super().get_fields()
        if self.context['request'].method.lower() == 'put':
            fields['user'] = serializers.PrimaryKeyRelatedField(queryset=User.objects.all().current())
            fields['activity'] = serializers.PrimaryKeyRelatedField(queryset=Activity.objects.all())
        return fields

    class Meta:
        model = UserActivityProject
        fields = ('id', 'user', 'activity', 'employee_rate', 'client_rate', 'is_billable')


class AssignEmployeeActivityToProjectSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all().current(), write_only=True)
    activity = serializers.PrimaryKeyRelatedField(queryset=Activity.objects.all(), write_only=True)

    class Meta:
        model = UserActivityProject
        fields = ('user', 'activity', 'employee_rate', 'client_rate', 'is_billable')

    def validate_user(self, user):
        if not user:
            raise ValidationError({
                "user": "This field may not be null"
            })
        return user

    def validate_activity(self, activity):
        if not activity:
            raise ValidationError({
                "activity": "This field may not be null"
            })
        return activity

    def create(self, validated_data):
        project_id = self.context.get('project_id')
        if UserActivityProject.objects.filter(
            project_id=project_id, user=validated_data.get('user'),
            activity=validated_data.get('activity')
        ).exists():
            raise ValidationError("The fields user, activity, project must make a unique set.")
        validated_data.update({
            "project": Project.objects.get(id=project_id)
        })
        return super().create(validated_data)
