from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.validators import validate_title
from ...models import Skill


class SkillSerializer(DynamicFieldsModelSerializer):
    slug = serializers.ReadOnlyField()
    name = serializers.CharField(
        required=True,
        max_length=100,
        validators=[validate_title,
                    UniqueValidator(queryset=Skill.objects.all(),
                                    lookup='iexact')])

    class Meta:
        model = Skill
        fields = ('slug', 'description', 'name',)

    def create(self, validated_data):
        name = validated_data['name']
        validated_data.update({'name': name.title()})
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if self.partial:
            if validated_data.get('name'):
                validated_data.update({'name': validated_data['name'].title()})
        else:
            validated_data.update({'name': validated_data['name'].title()})
        return super().update(instance, validated_data)


class SkillHelperSerializer(SkillSerializer):
    name = serializers.CharField(required=True, max_length=100)
    description = serializers.CharField(allow_null=True, required=False,
                                        allow_blank=True,
                                        max_length=600)
