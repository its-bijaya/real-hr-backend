import logging
import os
from base64 import b64encode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField
from rest_framework.serializers import Serializer

from irhrs.core.constants.user import MALE, FEMALE, OTHER
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject, get_complete_url
from irhrs.core.validators import validate_username
from irhrs.organization.models import Organization, UserOrganization
from irhrs.users.utils import send_activation_mail, send_logged_out_signal

User = get_user_model()
logger = logging.getLogger(__name__)


class UserSerializer(DynamicFieldsModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    cover_picture = serializers.ImageField(required=False)
    signature = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ['id',
                  'email',
                  'first_name',
                  'middle_name',
                  'last_name',
                  'name',
                  'username',
                  'profile_completeness',
                  'profile_picture',
                  'cover_picture',
                  'signature',
                  'profile_picture_thumb',
                  'cover_picture_thumb',
                  'is_online', 'last_online',
                  'is_audit_user'
                  ]
        read_only_fields = (
            'id', 'profile_picture_thumb', 'cover_picture_thumb', 'is_online', 'last_online',
        )

    def get_name(self, instance):
        middle_name = f' {instance.middle_name} ' if instance.middle_name else ''
        last_name = f' {instance.last_name}' if instance.last_name else ''
        return {
            'full': f"{instance.first_name}{middle_name}{last_name}",
            'partial': f"{instance.first_name}{last_name}"
        }

    def create(self, validated_data):
        organization = validated_data.pop('organization', None)
        validated_data.update({'password': self.generate_random_password()})
        user = User.objects.create_user(**validated_data)

        if organization:
            UserOrganization.objects.create(
                user=user, organization=organization)
        return user

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request and request.method == 'GET':
            fields['organization'] = SerializerMethodField()
            fields['profile_picture'] = SerializerMethodField()
            fields['cover_picture'] = SerializerMethodField()
        elif request and request.method == 'POST':
            fields['organization'] = SlugRelatedField(
                queryset=Organization.objects.all(),
                slug_field='slug',
                write_only=True,
                required=False)

        return fields

    def validate_email(self, email):
        qs = User.objects.all()

        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.filter(email__iexact=email).exists():
            raise ValidationError("User with this email already exists")
        return email

    def validate_username(self, username):
        qs = User.objects.all()
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.filter(username__iexact=username).exists():
            raise ValidationError("User with this username already exists")
        # throws validation error message if someone's email is similar to someone's username
        if qs.filter(email__iexact=username).exists():
            raise ValidationError("User with this email already exists")
        if username:
            username = validate_username(username)
        return username

    @staticmethod
    def get_profile_picture(instance):
        if instance.email == settings.SYSTEM_BOT_EMAIL:
            return get_complete_url(url='logos/real-hr-leaf.png', att_type='static')
        gender = instance.detail.gender
        img = {
            MALE: 'images/default/male.png',
            FEMALE: 'images/default/female.png',
            OTHER: 'images/default/other.png'
        }
        if instance.profile_picture:
            return get_complete_url(instance.profile_picture.url)
        return get_complete_url(url=img.get(gender), att_type='static')

    @staticmethod
    def get_cover_picture(instance):
        cover_picture = instance.cover_picture
        cover = 'images/default/cover.png'
        if cover_picture.__class__.__name__ == 'ImageFieldFile':
            return get_complete_url(url=instance.cover_picture.url)
        return get_complete_url(url=cover, att_type='static')

    @staticmethod
    def get_organization(instance):
        return [
            {'name': org.organization.name, 'slug': org.organization.slug}
            for org in getattr(instance, 'user_organizations',  # from prefetch
                               instance.organization.all())
        ]

    @staticmethod
    def generate_random_password():
        return b64encode(os.urandom(12)).decode('utf-8')


class NestableUserSerializer(UserSerializer):
    """
    Same as UserSerializer but removes unique validator from email
    because it creates issues during update in nested situation
    """

    class Meta(UserSerializer.Meta):
        extra_kwargs = {
            'email': {
                'validators': []
            },
            'username': {
                'validators': []
            }
        }

    # remove validation for Nested Serializer
    # This validation is handled in other ways
    def validate_email(self, email):
        return email

    @staticmethod
    def validate_last_name(last_name):
        if not last_name:
            raise ValidationError(
                'Last name may not be empty.'
            )
        return last_name


class PasswordChangeSerializer(Serializer):
    """
    Serializer used for password change
    """
    user = PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    old_password = CharField(max_length=128, write_only=True,
                             style={'input_type': 'password'})
    password = CharField(max_length=128, write_only=True,
                         style={'input_type': 'password'})
    repeat_password = CharField(max_length=128, write_only=True,
                                style={'input_type': 'password'})
    status = CharField(read_only=True)

    def validate_password(self, password):
        """validate password using django's password validator"""
        validate_password(password)
        return password

    def validate(self, attrs):

        # match password and repeat password
        password = attrs['password']
        repeat_password = attrs['repeat_password']
        if password != repeat_password:
            raise ValidationError({
                'repeat_password': ['Passwords did not match']})
        self._validate_old_password(attrs)

        return attrs

    def create(self, validated_data):
        user = validated_data.get('user')
        user.set_password(validated_data['password'])
        user.save()
        send_logged_out_signal(user)
        return DummyObject(user=user, status="Successfully changed password")

    def update(self, instance, validated_data):
        pass

    @staticmethod
    def _validate_old_password(attrs):
        user = attrs['user']
        old_password = attrs['old_password']

        if not user.check_password(old_password):
            raise ValidationError({'old_password': ['Incorrect Old Password']})


class PasswordSetSerializer(PasswordChangeSerializer):

    def get_fields(self):
        fields = super().get_fields()
        fields.pop('old_password', None)
        return fields

    @staticmethod
    def _validate_old_password(attrs):
        """We don't have old password here"""
        pass


class AccountActivationSerializer(Serializer):
    users = PrimaryKeyRelatedField(queryset=User.objects.all(), many=True,
                                   write_only=True)
    status = CharField(read_only=True,
                       default='Successfully sent activation links')

    def create(self, validated_data):
        for user in validated_data['users']:
            send_activation_mail(self.context['request'], user)

        return DummyObject(**validated_data)

    def update(self, instance, validated_data):
        return instance
