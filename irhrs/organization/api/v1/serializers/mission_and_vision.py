from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject
from irhrs.core.validators import validate_natural_number
from .common_org_serializer import OrganizationSerializerMixin
from ....models import OrganizationVision, OrganizationMission


class OrganizationVisionSerializer(OrganizationSerializerMixin):
    class Meta(OrganizationSerializerMixin.Meta):
        model = OrganizationVision
        fields = ('title', 'slug')
        read_only_fields = ('slug',)

    def validate_title(self, title):
        organization = self.context.get('organization')

        if hasattr(organization, 'vision') and not self.instance:
            raise ValidationError(
                "This organization already has a vision. "
                "Please update that if you want to change it."
            )
        if len(title.split()) < 3:
            raise ValidationError("Vision must be greater than three words")
        qs = OrganizationVision.objects.filter(
            title=title,
            organization=organization
        )
        if self.instance:
            qs = qs.exclude(title__iexact=self.instance.title)
        if qs.exists():
            raise ValidationError(
                "This organization already has vision of this title."
            )
        return title


class ChildMissionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = OrganizationMission
        fields = (
            'title', 'order_field'
        )
        read_only_fields = ('order_field',)
        extra_kwargs = {
            'order_field': {
                'required': False
            }
        }

    def validate(self, data):
        organization = self.context.get('organization')
        title = data.get('title')
        parent = data.get('parent')
        qs = organization.missions.filter(title=title, parent=parent)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                "This organization already has mission of this title."
            )
        return data


class OrganizationMissionSerializer(DynamicFieldsModelSerializer):
    title = serializers.CharField(
        required=True,
        max_length=200)
    child_missions = ChildMissionSerializer(many=True, required=False)

    class Meta(OrganizationSerializerMixin.Meta):
        model = OrganizationMission
        fields = (
            'organization', 'title', 'order_field', 'slug', 'description',
            'child_missions'
        )
        read_only_fields = ('slug', 'organization',)

    def validate(self, data):
        organization = self.context.get('organization')
        title = data.get('title')
        qs = organization.missions.filter(title__iexact=title)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                "This organization already has mission of this title."
            )
        data.update({
            'organization': organization
        })
        return data

    def validate_order_field(self, order_field):
        organization = self.context.get('organization')
        qs = organization.missions.filter(
            order_field=order_field
        )
        if self.instance:
            qs = qs.exclude(
                pk=self.instance.pk
            )
        if qs.exists():
            raise ValidationError(
                f"The mission with order field of {order_field} exists."
            )
        return order_field

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request:
            if request.method == 'POST':
                fields['order_field'] = serializers.IntegerField(
                    validators=[validate_natural_number]
                )

        return fields

    def create(self, validated_data):
        child_missions = validated_data.pop('child_missions', None)
        instance = OrganizationMission.objects.create(
            **validated_data
        )
        if child_missions:
            for index, child_mission in enumerate(child_missions):
                child_mission.update({
                    'organization': validated_data.get('organization'),
                    'parent': instance,
                    'order_field': (validated_data.get(
                        'order_field'
                    ) * 10 + index + 1) / 10
                })
                OrganizationMission.objects.create(
                    **child_mission
                )
        validated_data.update({
            'child_missions': child_missions
        })
        return DummyObject(**validated_data)

    def update(self, instance, validated_data):
        child_missions = validated_data.pop('child_missions', None)
        instance = super().update(instance, validated_data)
        instance.child_missions.all().delete()  # remove all old child.
        if child_missions:
            for index, child_mission in enumerate(child_missions):
                child_mission.update({
                    'organization': validated_data.get('organization'),
                    'parent': instance,
                    'order_field': (validated_data.get(
                        'order_field'
                    ) * 10 + index + 1) / 10
                })
                OrganizationMission.objects.create(
                    **child_mission
                )
        validated_data.update({
            'child_missions': child_missions
        })
        return DummyObject(**validated_data)

    # def update(self, instance, validated_data):
    #     child_missions = validated_data.pop('child_missions', [])
    #     for field, value in validated_data.items():
    #         setattr(instance, field, value)
    #     instance.save()
    #     for index, child_mission in enumerate(child_missions):
    #         child_mission.update({
    #             'organization': validated_data.get('organization'),
    #             'parent': instance,
    #             'order_field': (validated_data.get(
    #                 'order_field'
    #             ) * 10 + index + 1) / 10
    #         })
    #         child_slug = child_mission.get('slug', None)
    #         # delete old if created:
    #         if child_slug:
    #             OrganizationMission.objects.filter(
    #                 slug=child_slug
    #             ).update(**child_mission)
    #         else:
    #             child_mission.pop('slug', None)
    #             OrganizationMission.objects.create(
    #                 **child_mission
    #             )
    #     instance.child_missions.exclude(
    #         slug__in=[
    #             child_mission.get('slug') for child_mission in child_missions
    #             if child_mission.get('slug')
    #         ]
    #     ).delete()
    #     validated_data.update({
    #         'child_missions': child_missions
    #     })
    #     return DummyObject(**validated_data)
