from django.core.validators import FileExtensionValidator
from rest_framework import serializers
from rest_framework.fields import FileField

from irhrs.organization.api.v1.serializers.common_org_serializer import OrganizationSerializerMixin
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility


class KnowledgeSkillAbilitySerializer(OrganizationSerializerMixin):
    class Meta:
        model = KnowledgeSkillAbility
        fields = ['name', 'description', 'slug']
        read_only_fields = ['slug']

    def validate(self, attrs):
        organization = self.context['organization']
        name = attrs.get('name')
        ksa_type = self.context['ksa_type']
        queryset = KnowledgeSkillAbility.objects.filter(
                organization=organization,
                name__iexact=name,
                ksa_type=ksa_type
        )
        if self.instance:
            queryset = queryset.exclude(id=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                {'name': f'Name must be unique for {ksa_type.title()}'}
            )
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data.update({
            'ksa_type': self.context.get('ksa_type')
        })
        return super().create(validated_data)


class KnowledgeSkillAbilityThinSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeSkillAbility
        fields = ['name', 'slug']


class FileImportSerializer(serializers.Serializer):
    file = FileField(write_only=True, validators=[
        FileExtensionValidator(
            allowed_extensions=['xlsx'],
            message='Not a valid file format.',
            code='Invalid Format'
        )])
