from django.conf import settings
from django.core.validators import FileExtensionValidator
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.validators import UniqueValidator

from irhrs.organization.models import Organization
from ...models import HRPolicyHeading, HRPolicyBody


class HRPolicyHeadingSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True,
                                  max_length=100,
                                  validators=[UniqueValidator(
                                      queryset=HRPolicyHeading.objects.all(),
                                      lookup='iexact')]
                                  )
    description = serializers.CharField(required=True)

    class Meta:
        model = HRPolicyHeading
        fields = (
            'title', 'description', 'organization',
            'status', 'order_field', 'slug',
        )
        read_only_fields = ('organization', 'slug')

    def create(self, validated_data):
        request = self.context.get('request')
        organization_slug = request.parser_context['kwargs']['organization_slug']
        organization = get_object_or_404(Organization, slug=organization_slug)
        validated_data['organization'] = organization
        return super().create(validated_data)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request and request.method == 'GET':
            fields['organization'] = serializers.SerializerMethodField(read_only=True)
        return fields

    @staticmethod
    def get_organization(instance):
        return {'name': instance.organization.name,
                'abbreviation': instance.organization.abbreviation,
                'email': instance.organization.email,
                'slug': instance.organization.slug,
                }


class HRPolicyBodySerializer(serializers.ModelSerializer):
    attachment = serializers.FileField(validators=[FileExtensionValidator(
        allowed_extensions=settings.ACCEPTED_FILE_FORMATS.get('documents'),
        message="The uploaded document is not recognized.",
        code='Invalid File Format'
    )], allow_null=True)
    title = serializers.CharField(required=True,
                                  max_length=100,
                                  validators=[UniqueValidator(
                                      queryset=HRPolicyBody.objects.all(),
                                      lookup='iexact')]
                                  )
    heading = serializers.SlugRelatedField(
        queryset=HRPolicyHeading.objects.all(),
        slug_field='slug',
        required=True,
        allow_null=False
    )
    parent = serializers.SlugRelatedField(
        required=False,
        allow_null=True,
        slug_field='slug',
        queryset=HRPolicyHeading.objects.all())

    class Meta:
        model = HRPolicyBody
        fields = (
            'heading', 'title', 'body', 'attachment', 'parent', 'order_field',
            'slug',
        )
        read_only_fields = ('slug',)

    def create(self, validated_data):
        request = self.context.get('request')
        policy_slug = request.parser_context['kwargs']['header_slug']
        policy_header = get_object_or_404(HRPolicyHeading, slug=policy_slug)
        validated_data['heading'] = policy_header
        return super().create(validated_data)

    def get_heading(self, instance):
        return {
            'title': instance.heading.title,
            'description': instance.heading.description,
            'organization_slug': instance.heading.organization.slug,
            'status': instance.heading.status,
        }

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request and request.method == 'GET':
            fields['parent'] = serializers.SerializerMethodField(read_only=True)
            fields['child'] = serializers.SerializerMethodField(read_only=True)
            fields['heading'] = serializers.SerializerMethodField(
                read_only=True)
        return fields

    def get_parent(self, instance):
        if instance.parent:
            return {
                "title": instance.parent.title,
                "parent_slug": instance.parent.slug,
            }
        else:
            return{
                "parent": None,
            }

    def get_child(self, instance):
        child_bodies = []
        for child in instance.child_bodies.all():
            child_data = {
                'title': child.title,
                'slug': child.slug
            }
            child_bodies.append(child_data)
        return child_bodies
