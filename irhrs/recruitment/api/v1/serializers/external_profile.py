from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.organization.api.v1.serializers.knowledge_skill_ability import KnowledgeSkillAbilitySerializer
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.recruitment.models import External, ReferenceChecker
from irhrs.recruitment.utils import validate_attachment
from irhrs.users.constants import INTERVIEWER
from irhrs.users.models.user import ExternalUser


class ExternalUserSerializer(DynamicFieldsModelSerializer):
    profile_picture = serializers.ReadOnlyField(
        source='profile_picture_thumb',
        allow_null=True
    )
    age = serializers.ReadOnlyField()
    applicant_id = serializers.SerializerMethodField()

    class Meta:
        model = ExternalUser
        fields = '__all__'
        read_only_fields = ['uuid']
        extra_kwargs = {
            'dob': {
                'required': False,
                'allow_null': True
            },
            'marital_status': {
                'required': False,
                'allow_null': True
            },
            'gender': {
                'required': False,
                'allow_null': True
            }
        }

    @staticmethod
    def get_applicant_id(instance):
        if hasattr(instance, 'applicant'):
            return instance.applicant.id
        return None


class ExternalSerializer(DynamicFieldsModelSerializer):
    full_name = serializers.ReadOnlyField(source='user.full_name')
    user = ExternalUserSerializer(
        exclude_fields=['is_archived', 'created_at', 'modified_at'])

    class Meta:
        model = External
        fields = (
            'id', 'user',
            'ksao', 'full_name',
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['ksao'] = KnowledgeSkillAbilitySerializer(
                many=True,
                fields=('name', 'slug')
            )
        if self.request and self.request.method.lower() in ['post', 'put', 'patch']:
            fields['ksao'] = serializers.SlugRelatedField(
                slug_field='slug',
                queryset=KnowledgeSkillAbility.objects.filter(
                    organization=self.context.get('organization')
                ),
                many=True
            )
            fields['user.profile_picture'] = serializers.ImageField(
                required=False,
                allow_null=True,
                validators=[
                    FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'bmp']),
                    validate_attachment
                ]
            )
        return fields

    def validate(self, attrs):
        email = attrs.get('user').get('email')
        queryset = External.objects.all()
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.filter(user__email=email).exists():
            raise serializers.ValidationError(_(
                'External with this email already exists.'
            ))

        phone_number = attrs.get('user').get('phone_number')
        if queryset.filter(user__phone_number=phone_number).exists():
            raise serializers.ValidationError(_(
                'External with this Phone Number already exists.'
            ))
        return super().validate(attrs)

    def create(self, validated_data):
        user_data = validated_data.get('user')
        ksao_data = validated_data.get('ksao')
        external_profile = ExternalUser.objects.create(**user_data)
        external = External.objects.create(user=external_profile)
        for ksao in ksao_data:
            external.ksao.add(ksao)
        return external

    def update(self, instance, validated_data):
        user_data = validated_data.get('user')
        _new_ksao_data = validated_data.get('ksao', ...)

        if user_data:
            for k, v in user_data.items():
                setattr(instance.user, k, v)
            instance.user.save()

        if _new_ksao_data is not ...:
            _old_ksao_data = instance.ksao.all().values_list('slug', flat=True)
            _deleted_ksao_data = set(_old_ksao_data).difference(set(_new_ksao_data))

            if _deleted_ksao_data:
                instance.ksao.remove(*list(instance.ksao.filter(slug__in=_deleted_ksao_data)))

            for ksao in _new_ksao_data:
                instance.ksao.add(ksao)

        return instance


class ReferenceCheckerSerializer(DynamicFieldsModelSerializer):
    full_name = serializers.ReadOnlyField(source='user.name')

    class Meta:
        model = ReferenceChecker
        fields = '__all__'
        extra_kwargs = {
            'uuid': {
                'allow_null': True,
                'required': False
            }
        }

    def get_fields(self):
        fields = super().get_fields()
        from irhrs.recruitment.api.v1.serializers.applicant import ApplicantReferenceSerializer
        fields['user'] = ApplicantReferenceSerializer(
            exclude_fields=['is_archived', 'applicant', 'created_at', 'modified_at']
        )
        return fields
