from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer


class OrganizationSerializerMixin(DynamicFieldsModelSerializer):
    class Meta:
        model = None

    def create(self, validated_data):
        organization = self.context.get('organization')
        validated_data['organization'] = organization
        return super().create(validated_data)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method == 'GET':
            if fields.get('organization'):
                fields['organization'] = serializers.SerializerMethodField(
                    read_only=True)
        return fields

    @staticmethod
    def get_organization(instance):
        return {
            'name': instance.organization.name,
            'abbreviation': instance.organization.abbreviation,
            'email': instance.organization.email,
            'slug': instance.organization.slug
        }
