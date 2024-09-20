from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import UserKSAO
from irhrs.users.utils.notification import send_change_notification_to_user


class UserKSAOSerializer(DynamicFieldsModelSerializer):
    ksa_type = serializers.ReadOnlyField(source='ksa.ksa_type')
    ksa = serializers.ReadOnlyField(source='ksa.name')
    slug = serializers.ReadOnlyField(source='ksa.slug')

    class Meta:
        model = UserKSAO
        fields = (
            'ksa', 'is_key', 'ksa_type', 'slug'
        )

    def __init__(self, instance=None, *args, **kwargs):
        self.ksa_type = kwargs.pop('ksa_type', None)
        super().__init__(instance, *args, **kwargs)

    def get_fields(self):
        description = self.context.get('description', False)
        fields = super().get_fields()
        org = self.context.get('organization')
        if self.request and self.request.method in ['POST', 'PUT', 'PATCH']:
            qs = KnowledgeSkillAbility.objects.filter(
                    organization=org
                )
            if self.ksa_type:
                qs = qs.filter(ksa_type=self.ksa_type)
            fields['ksa'] = serializers.SlugRelatedField(
                queryset=qs,
                slug_field='slug'
            )
        if description:
            fields['description'] = serializers.ReadOnlyField(
                source='ksa.description'
            )
        return fields

    def validate(self, attrs):
        ksa = attrs.get('ksa')
        user = attrs.get('user')
        qs = UserKSAO.objects.filter(ksa=ksa, user=user)
        if self.instance:
            qs = qs.exclude(id=self.instance.pk)
        if qs.exists():
            raise ValidationError(_(
                f'This {ksa.get_ksa_type_display()} for this user already exists.'
            ))
        return super().validate(attrs)


class UserKSAOListSerializer(DummySerializer):
    user = serializers.SerializerMethodField()
    knowledge = serializers.ReadOnlyField()
    skill = serializers.ReadOnlyField()
    ability = serializers.ReadOnlyField()
    other_attributes = serializers.ReadOnlyField()

    class Meta:
        model = get_user_model()
        fields = (
            'user', 'knowledge', 'skill', 'ability', 'other_attributes'
        )

    def get_user(self, instance):
        return UserThinSerializer(
            instance=instance,
            context=self.context
        ).data


class UserKSAOCreateSerializer(DummySerializer):
    ksao = UserKSAOSerializer(many=True)

    def get_fields(self):
        fields = super().get_fields()
        fields['users'] = serializers.PrimaryKeyRelatedField(
            queryset=get_user_model().objects.filter(
                detail__organization=self.context.get('organization')
            ).current(),
            many=True,
            required=True,
            allow_empty=False
        )
        return fields

    def create(self, validated_data):
        users = validated_data.get('users')
        ksao = validated_data.get('ksao')
        for user in users:
            for datum in ksao:
                UserKSAO.objects.update_or_create(
                    user=user,
                    ksa=datum.get('ksa'),
                    defaults=dict(
                        is_key=datum.get('is_key')
                    )
                )
            request = self.context.get('request')
            if request:
                send_change_notification_to_user(self, user, user, request.user, 'created')
        return super().create(validated_data)


class IndividualUserKSAOCreateSerializer(DummySerializer):
    ksao = UserKSAOSerializer(many=True)

    def create(self, validated_data):
        user = self.context.get('user')
        ksao = validated_data.get('ksao')
        ksao_type = self.context.get('ksa_type')
        if ksao_type:
            base_values = user.assigned_ksao.filter(
                ksa__ksa_type=ksao_type
            ).values_list('ksa_id', flat=True)
        else:
            base_values = user.assigned_ksao.values_list('ksa_id', flat=True)
        remove_ksaos = set(base_values) - set(map(
            lambda dat: dat.get('ksa').id, ksao
        ))
        UserKSAO.objects.filter(
            user=user,
            ksa_id__in=remove_ksaos
        ).delete()
        for datum in ksao:
            UserKSAO.objects.update_or_create(
                user=user,
                ksa=datum.get('ksa'),
                defaults=dict(
                    is_key=datum.get('is_key')
                )
            )
        instance = super().create(validated_data)
        request = self.context.get('request')
        send_change_notification_to_user(self, user, user, request.user, 'updated')
        return instance
