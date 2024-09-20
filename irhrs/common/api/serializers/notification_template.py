import re

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField

from irhrs.common.models import NotificationTemplate
from irhrs.common.models.notification_template import NotificationTemplateContent
from irhrs.core.constants.common import (
    EMAIL_TEMPLATE_VALIDATION_MATCH, EMAIL_TYPE_STATUS
)
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer


class NotificationTemplateContentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = NotificationTemplateContent
        fields = ('id', 'content', 'status')
        extra_kwargs = {
            'template': {'write_only': True}
        }

    def validate(self, attrs):
        view = self.context.get('view')
        template = view.template if view else None
        if not template:
            raise ValidationError('No template found.')

        self._validate_content(
            attrs,
            EMAIL_TEMPLATE_VALIDATION_MATCH.get(template.type)
        )

        self._validate_status(
            attrs,
            EMAIL_TYPE_STATUS.get(template.type)
        )
        attrs['template'] = template
        return super().validate(attrs)

    @staticmethod
    def _validate_content(attrs, valid_matches):
        requested_params = [
            word.replace(
                '{', ''
            ).replace(
                '}', ''
            ).strip() for word in re.findall(
                r'\{\{.*?\}\}',
                attrs.get('content')
            )
        ]
        valid_params = [
            word.replace(
                '{', ''
            ).replace(
                '}', ''
            ) for word in valid_matches.keys()
        ]
        diff = set(requested_params) - set(valid_params)
        if diff:
            raise ValidationError(
                {
                    'content': '{{' + '}}, {{'.join(diff) + '}} is not valid for ' +
                               attrs.get('status')
                }
            )

    @staticmethod
    def _validate_status(attrs, valid_status):
        if attrs.get('status') not in valid_status:
            raise ValidationError({
                'status': f'Status must be among '
                          f'{",".join(valid_status)}.'
            })

    def create(self, validated_data):
        instance, created = NotificationTemplateContent.objects.update_or_create(
            template=validated_data.get('template'),
            status=validated_data.get('status'),
            defaults={
                'content': validated_data.get('content')
            }
        )
        return instance


class NotificationTemplateSerializer(DynamicFieldsModelSerializer):
    status = SerializerMethodField()
    hints = SerializerMethodField()
    contents = NotificationTemplateContentSerializer(
        fields=['id', 'status'],
        read_only=True, many=True
    )
    child_status_list = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NotificationTemplate
        fields = (
            'name', 'type', 'description', 'created_at', 'slug', 'status', 'hints',
            'contents', 'child_status_list'
        )
        read_only_fields = ('slug',)

    @staticmethod
    def get_status(obj):
        return EMAIL_TYPE_STATUS.get(obj.type)

    @staticmethod
    def get_hints(obj):
        return EMAIL_TEMPLATE_VALIDATION_MATCH.get(obj.type)

    @staticmethod
    def get_child_status_list(instance):
        return instance.contents.values_list('status', flat=True)

    def validate(self, attrs):
        if not self.instance and \
           NotificationTemplate.objects.filter(name=attrs.get('name')).exists():
            raise ValidationError({'name': 'Email template with this name already exists.'})
        return super().validate(attrs)
