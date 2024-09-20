from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.common.api.serializers.notification_template import \
    NotificationTemplateSerializer
from irhrs.common.models import NotificationTemplate
from irhrs.organization.models import NotificationTemplateMap
from .common_org_serializer import OrganizationSerializerMixin


class NotificationTemplateMapSerializer(OrganizationSerializerMixin):
    template = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=NotificationTemplate.objects.all()
    )
    active_status = serializers.ListField(
        child=serializers.CharField(max_length=32),
    )

    class Meta:
        model = NotificationTemplateMap
        fields = ('template', 'is_active', 'id', 'active_status')
        read_only_fields = ('id',)

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields.update({
                'template': NotificationTemplateSerializer(
                    fields=[
                        'name', 'slug', 'type', 'child_status_list'
                    ],
                    context=self.context
                )
            })
        return fields

    def create(self, validated_data):
        instance = super().create(validated_data)
        self.deactivate_similar_templates(instance)
        return instance

    def update(self, instance, validated_data):
        obj = super().update(instance, validated_data)
        self.deactivate_similar_templates(obj)
        return obj

    def deactivate_similar_templates(self, instance):
        if not instance.is_active:
            return
        organization = instance.organization
        self.Meta.model.objects.exclude(
            pk=instance.pk
        ).filter(
            organization=organization,
            template__type=instance.template.type
        ).update(
            is_active=False
        )

    def validate(self, attrs):
        template = attrs.get('template')
        org = self.context.get('organization')
        filter_qs = self.Meta.model.objects.filter(
            template=template,
            organization=org
        )
        if self.instance:
            filter_qs = filter_qs.exclude(pk=self.instance.pk)
        if filter_qs.exists():
            raise ValidationError(
                f'The `{template.name}` of exists for {org}'
            )
        if 'active_status' in attrs:
            self._validate_active_status(attrs.get('active_status'), template)
        return attrs

    @staticmethod
    def _validate_active_status(active_status, template):
        valid_status = set(template.contents.values_list('status', flat=True))
        set_status = set(active_status)
        invalid_choices = set_status - valid_status - {'Default'}
        if invalid_choices:
            raise ValidationError({
                'active_status': 'One or more choice(s) were invalid: {}'.format(
                    ', '.join(invalid_choices)
                )
            })
        if not set_status:
            raise ValidationError({
                'active_status': 'Active status needs to be set.'
            })
        return active_status
