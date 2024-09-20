from django.utils.functional import cached_property
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.common.api.serializers.id_card import IdCardSampleSerializer
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import get_complete_url
from ....models import IdCardTemplate, IdCard


class IdCardTemplateSerializer(DynamicFieldsModelSerializer):
    org_name = serializers.ReadOnlyField(source="organization.name")

    class Meta:
        model = IdCardTemplate
        exclude = ('organization',)

    def create(self, validated_data):
        organization = self.context.get('organization')
        return IdCardTemplate.objects.create(organization=organization, **validated_data)

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method == 'GET':
            fields['sample'] = IdCardSampleSerializer(fields=['id', 'name', 'content'], context=self.context)
        return fields


def get_user_details(user, send_representation=False):
    self_contact = user.self_contacts.first()
    phone_number = getattr(self_contact, 'number', None)
    address = user.addresses.order_by('-address_type').first()  # temporary/permanent order
    citizenship_number = nested_getattr(user, 'legal_info.citizenship_number')

    profile_picture = None
    if user.profile_picture:
        profile_picture = get_complete_url(
            user.profile_picture, att_type='media'
        ) if send_representation else user.profile_picture

    return {
        'full_name': user.full_name,
        'employee_code': user.detail.code if user.detail.code else '',
        'employment_level': user.detail.employment_level.title if user.detail.employment_level else '',
        'division': user.detail.division.name if user.detail.division else '',
        'user_email': user.email,
        'phone_no': phone_number,
        'citizenship_number': citizenship_number,
        'address': getattr(address, 'address', None),
        'signature': user.signature_url if send_representation else user.signature,
        'profile_picture': profile_picture
    }


class IdCardSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = IdCard
        fields = '__all__'
        read_only_fields = (
            'full_name',
            'employee_code',
            'employment_level',
            'division',
            'user_email',
            'phone_no',
            'address',
            'citizenship_number',
            'signature'
        )
        extra_kwargs = {
            'profile_picture': {
                'allow_null': True,
            }
        }

    def validate_user(self, user):
        organization = self.context.get('organization')
        if not user.detail.organization == organization:
            raise ValidationError("User not found for this organization.")
        return user

    def validate_template(self, template):
        organization = self.context.get('organization')
        if not template.organization == organization:
            raise ValidationError("Template not found for this organization.")
        return template

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('request').method == 'GET':
            fields.update({'template': IdCardTemplateSerializer(exclude_fields=['created_at', 'modified_at',
                                                                                'created_by', 'modified_by'],
                                                                context=self.context)})
        return fields

    def create(self, validated_data):
        """
        Create and return a new `IdCard` instance, given the validated data.
        """
        user = validated_data.get('user')

        data = get_user_details(user)
        new_profile_picture = validated_data.pop('profile_picture', None)
        data['profile_picture'] = new_profile_picture or data['profile_picture']

        return IdCard.objects.create(
            **data,
            **validated_data
        )
