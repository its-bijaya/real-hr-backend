from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ....models import OrganizationEthics
from .common_org_serializer import OrganizationSerializerMixin


class OrganizationEthicsSerializer(OrganizationSerializerMixin):
    parent = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=OrganizationEthics.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta(OrganizationSerializerMixin.Meta):
        model = OrganizationEthics
        fields = ('organization', 'title', 'description', 'parent', 'moral',
                  'published', 'slug', 'is_archived', 'created_at', 'modified_at',
                  'attachment', 'is_downloadable', 'document_text')
        read_only_fields = ('slug',)

    def validate_title(self, title):
        organization = self.context.get('organization')
        qs = organization.ethics.filter(title=title)
        if self.instance:
            qs = qs.exclude(title=self.instance.title)
        if qs.exists():
            raise ValidationError("This organization already has "
                                  "ethics of this title.")
        return title

    def validate(self, attrs):
        is_downloadable = attrs.get('is_downloadble')
        attachment = attrs.get('attachment')
        if self.request.method.lower() == 'patch' and not is_downloadable:
            attachment = None
        return attrs

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request and request.method == 'GET':
            fields['child_ethics'] = serializers.SerializerMethodField(
                read_only=True)
            fields['parent'] = serializers.SerializerMethodField(
                read_only=True)
        return fields

    @staticmethod
    def get_parent(instance):
        if instance.parent:
            return {
                "title": instance.parent.title,
                "slug": instance.parent.slug
            }
        return None

    @staticmethod
    def get_child_ethics(instance):
        child_ethics = []
        for child in instance.child_ethics.all():
            child_data = {
                'title': child.title,
                'slug': child.slug
            }
            child_ethics.append(child_data)
        return child_ethics
