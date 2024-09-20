from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from irhrs.core.validators import validate_phone_number
from irhrs.users.api.v1.serializers.user_serializer_common import \
    UserSerializerMixin
from irhrs.users.models import UserContactDetail
from irhrs.core.constants.user import CHILDREN, DEPENDENT_DOCUMENT_TYPES


class UserContactDetailSerializer(UserSerializerMixin):
    slug = serializers.ReadOnlyField()
    number = serializers.CharField(
        max_length=25,
        allow_blank=True,
        validators=[validate_phone_number, UniqueValidator(
            queryset=UserContactDetail.objects.all(),
            lookup='iexact',
            message="Contact number cannot be duplicated"
        )])
    number_type = serializers.CharField(
        max_length=10,
        allow_blank=True
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        validators=[UniqueValidator(
            queryset=UserContactDetail.objects.all(),
            lookup='iexact',
            message="Email cannot be duplicated"
        )]
    )
    occupation = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )
    dependent_id_type = serializers.ChoiceField(
        choices=DEPENDENT_DOCUMENT_TYPES,
        required=False,
        allow_null=True
    )
    dependent_id_number = serializers.CharField(max_length=50, default='')

    class Meta:
        model = UserContactDetail
        fields = (
            'name', 'contact_of', 'address', 'emergency', 'number',
            'number_type', 'email', 'slug', 'user', 'is_dependent',
            'date_of_birth', 'attachment', 'occupation',
            'dependent_id_type', 'dependent_id_number'
        )
        read_only_fields = ('user', 'slug')

    def validate(self, data):
        contact_of = data.get('contact_of')
        number = data.get('number')
        emergency = data.get('emergency')
        number_type = data.get('number_type')
        dependent_id_number = data.get('dependent_id_number')
        dependent_id_type = data.get('dependent_id_type')
        is_dependent = data.get('is_dependent')
        if is_dependent and not (dependent_id_number and dependent_id_type):
            raise serializers.ValidationError("Provide both document type and document number.")

        if not is_dependent and (dependent_id_number or dependent_id_type):
            raise serializers.ValidationError("Cannot set id number or type when dependent is false.")

        if number_type and not number:
            raise serializers.ValidationError(
                {"number": "Number must not be empty when Number Type is provided."})
        if number and not number_type:
            raise serializers.ValidationError(
                {"number_type": "Number Type must not be empty when Number is provided."})

        if not (number or (contact_of == CHILDREN and not emergency)):
            raise serializers.ValidationError({"number": "Number must not be empty."})

        return data

