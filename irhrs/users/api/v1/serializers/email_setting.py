from django.db import transaction
from django.utils.functional import cached_property
from rest_framework import serializers

from irhrs.core.constants.organization import EMAIL_TYPE_CHOICES
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.organization.api.v1.serializers.settings import (
    MODULE_WISE_EMAIL_TYPE, EMAIL_CATEGORY_MAP
)
from irhrs.users.models import UserEmailUnsubscribe


class UserEmailSettingSerializer(DummySerializer):
    email_type_display = serializers.ReadOnlyField(source='get_email_type_display')
    email_type = serializers.ReadOnlyField()
    send_email = serializers.ReadOnlyField(source='_send_email')
    allow_unsubscribe = serializers.ReadOnlyField()
    category = serializers.SerializerMethodField()

    @staticmethod
    def get_category(obj):
        return EMAIL_CATEGORY_MAP.get(obj.email_type, "")


class UserEmailGroupSettingSerializer(serializers.Serializer):
    results = serializers.SerializerMethodField()

    class Meta:
        fields = ('results', )

    @staticmethod
    def get_results(obj):
        out = dict()
        for key, items in MODULE_WISE_EMAIL_TYPE.items():
            out[key] = UserEmailSettingSerializer(
                obj.filter(email_type__in=items),
                many=True
            ).data
        return out


class UserEmailSettingUpdateSerializer(DummySerializer):
    email_type = serializers.ChoiceField(choices=EMAIL_TYPE_CHOICES)
    send_email = serializers.BooleanField()

    @cached_property
    def email_settings(self) -> dict:
        return {
            email_type: allow_unsubscribe for email_type, allow_unsubscribe in
            self.context.get('organization').email_settings.filter(
                send_email=True).values_list('email_type', 'allow_unsubscribe')
        }

    @cached_property
    def allowed_email_types(self) -> list:
        return list(self.email_settings.keys())

    def validate(self, attrs):
        email_type = attrs.get('email_type')
        send_email = attrs.get('send_email')

        if email_type not in self.allowed_email_types:
            raise serializers.ValidationError(
                {'email_type': ['Invalid email type']},
                code='invalid'
            )

        allow_unsubscribe = self.email_settings.get(email_type, False)
        if not (send_email or allow_unsubscribe):
            raise serializers.ValidationError({
                'send_email': 'You are not allowed to unsubscribe this email.'
            })

        return attrs


class UserEmailSettingBulkUpdateSerializer(DummySerializer):
    email_settings = UserEmailSettingUpdateSerializer(many=True)

    @transaction.atomic()
    def create(self, validated_data):
        user = self.context.get('user')
        for email_setting in validated_data.get('email_settings'):
            if not email_setting.get('send_email'):
                UserEmailUnsubscribe.objects.get_or_create(
                    user=user,
                    email_type=email_setting.get('email_type')
                )
            else:
                UserEmailUnsubscribe.objects.filter(
                    user=user,
                    email_type=email_setting.get('email_type')
                ).delete()
        return super().create(validated_data)
