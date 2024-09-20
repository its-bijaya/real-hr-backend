from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework.relations import ManyRelatedField, PrimaryKeyRelatedField

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject
from irhrs.core.validators import validate_natural_number
from irhrs.organization.api.v1.serializers.division import \
    OrganizationDivisionSerializer
from irhrs.organization.api.v1.serializers.organization import OrganizationSerializer
from irhrs.organization.models import OrganizationDivision
from irhrs.users.api.v1.serializers.experience import UserExperienceSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import UserExperience
from ....models import ResultArea, CoreTask, UserResultArea
from rest_framework import serializers

User = get_user_model()

USER_FIELDS = ['id', 'full_name', 'profile_picture', 'cover_picture', 'division', 'organization']


class UserAssociationSerializer(DynamicFieldsModelSerializer):
    user_experience = UserExperienceSerializer(read_only=True)
    user = UserThinSerializer(fields=USER_FIELDS, read_only=True, source='user_experience.user')

    class Meta:
        model = UserResultArea
        fields = ('id', 'user', 'user_experience',)


class CoreTaskSerializer(DynamicFieldsModelSerializer):
    associated_users = serializers.SerializerMethodField(read_only=True)
    can_be_deleted = serializers.SerializerMethodField()
    order = serializers.IntegerField(validators=[validate_natural_number])

    class Meta:
        model = CoreTask
        fields = (
            'id', 'title', 'description', 'order', 'associated_users',
            'can_be_deleted', 'result_area'
        )
        read_only_fields = (
            'result_area',
        )

    @staticmethod
    def get_can_be_deleted(instance):
        if instance.userresultarea_set.exists():
            return False
        return True

    @staticmethod
    def get_associated_users(instance):
        return UserAssociationSerializer(instance.userresultarea_set.all(), many=True).data

    def validate(self, attrs):
        result_area = self.context.get('result_area')
        order = attrs.get('order', self.instance.order if self.instance else 1)  # default ordering is 1

        qs = CoreTask.objects.all()
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.filter(result_area=result_area, order=order).exists():
            raise ValidationError(f"The result area already has a core task of order {order}")
        return attrs

    def create(self, validated_data):
        validated_data.update({'result_area': self.context.get('result_area')})
        return super().create(validated_data)


class ResultAreaSerializer(DynamicFieldsModelSerializer):
    organization = serializers.SerializerMethodField(read_only=True)
    core_tasks = serializers.SerializerMethodField(read_only=True)
    associated_users = serializers.SerializerMethodField(read_only=True)
    division = serializers.SlugRelatedField(
        slug_field='slug', queryset=OrganizationDivision.objects.all())
    can_be_deleted = serializers.SerializerMethodField()
    can_be_edited = serializers.SerializerMethodField()

    class Meta:
        model = ResultArea
        fields = ('id', 'title', 'description', 'division', 'organization',
                  'associated_users', 'core_tasks', 'can_be_deleted', 'can_be_edited')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            if 'division' in fields:
                fields['division'] = OrganizationDivisionSerializer(fields=[
                    'name', 'slug'], context=self.context)
        return fields

    @staticmethod
    def get_can_be_edited(instance):
        return not instance.associated_users.exists()

    @staticmethod
    def get_can_be_deleted(instance):
        return not(instance.core_tasks.exists() or instance.associated_users.exists())

    @staticmethod
    def get_organization(instance):
        return OrganizationSerializer(instance.division.organization,
                                      fields=['id', 'abbreviation']).data

    @staticmethod
    def get_core_tasks(instance):
        return CoreTaskSerializer(instance.core_tasks.all(),
                                  fields=['id', 'title', 'description', 'order',
                                          'result_area', 'can_be_deleted'],
                                  many=True).data

    @staticmethod
    def get_associated_users(instance):
        return UserAssociationSerializer(instance.associated_users.all(), many=True).data

    def validate(self, attrs):
        if self.instance and not self.get_can_be_edited(self.instance):
            raise ValidationError("RA having associated with users cannot be edited")
        return attrs

    def create(self, validated_data):
        validated_data.update({
            'created_by': self.request.user
        })
        return super().create(validated_data)


class UserResultAreaSerializer(DynamicFieldsModelSerializer):
    core_tasks = ManyRelatedField(
        allow_empty=True,
        child_relation=PrimaryKeyRelatedField(allow_empty=True, queryset=CoreTask.objects.all())
    )

    class Meta:
        model = UserResultArea
        fields = ('id', 'user_experience', 'result_area', 'core_tasks', 'key_result_area',)

    def get_fields(self):
        fields = super().get_fields()
        fields['user_experience'] = serializers.PrimaryKeyRelatedField(
            queryset=UserExperience.objects.include_upcoming()
        )
        if self.request.method.upper() == 'GET':
            # fields['user'] = UserThinSerializer(fields=USER_FIELDS)
            fields['result_area'] = ResultAreaSerializer(fields=['id', 'title'])
            fields['core_tasks'] = CoreTaskSerializer(
                fields=['id', 'title', 'description'], many=True)
        return fields

    def validate(self, attrs):
        result_area = attrs.get('result_area')
        result_area_core_tasks = result_area.core_tasks.all().values_list('id', flat=True)
        core_tasks = attrs.get('core_tasks', [])
        if not core_tasks:
            UserResultArea.objects.filter(
                user_experience=attrs.get('user_experience'),
                result_area=result_area).delete()
        core_tasks_ids = [x.id for x in core_tasks]
        valid_core_tasks = all(core_task in result_area_core_tasks for core_task in core_tasks_ids)
        if not valid_core_tasks:
            raise serializers.ValidationError({
                'core_task': ['Core Task does not belongs to result area.']
            })
        return attrs

    def run_validators(self, value):
        """
        pass model unique together validation as it is modified here
        accompanying different use case.
        """

    def create(self, validated_data):
        data_copy = dict(validated_data)
        for_user_experience = validated_data.pop('user_experience')
        result_area = validated_data.pop('result_area')
        core_tasks = validated_data.pop('core_tasks', [])
        if core_tasks:
            user_result_area, created = self.Meta.model.objects.get_or_create(
                user_experience=for_user_experience, result_area=result_area)
            user_result_area.key_result_area = validated_data.get('key_result_area', False)
            user_result_area.core_tasks.clear()
            user_result_area.core_tasks.add(*core_tasks)
            user_result_area.save()
        return DummyObject(**data_copy)


class UserExperienceWithResultAreaSerializer(UserExperienceSerializer):
    result_areas = serializers.SerializerMethodField()
    upcoming = serializers.ReadOnlyField()

    class Meta(UserExperienceSerializer.Meta):
        fields = UserExperienceSerializer.Meta.fields + (
            'result_areas', 'upcoming'
        )

    def get_result_areas(self, instance):
        ctx = {'request': self.context['request']}
        return UserResultAreaSerializer(instance.user_result_areas.all(),
                                        fields=['id', 'result_area', 'core_tasks', 'key_result_area'],
                                        context=ctx, many=True).data


class UserResultAreaListSerializer(UserThinSerializer):
    experiences = serializers.SerializerMethodField()

    class Meta(UserThinSerializer.Meta):
        model = User
        fields = UserThinSerializer.Meta.fields + ['experiences']

    def get_experiences(self, instance):
        ctx = {'request': self.context['request']}
        return UserExperienceWithResultAreaSerializer(
            instance.user_experiences.all(),
            fields=['id', 'job_title', 'division', 'organization', 'result_areas',
                    'is_current', 'upcoming'], context=ctx, many=True
        ).data
