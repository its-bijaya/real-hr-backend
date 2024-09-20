from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.users.api.v1.serializers.contact_detail import UserContactDetailSerializer
from irhrs.users.api.v1.serializers.user_serializer_common import UserSerializerMixin
from irhrs.users.models import UserInsurance, UserContactDetail


class UserInsuranceSerializer(UserSerializerMixin):
    class Meta:
        model = UserInsurance
        fields = [
            'id', 'dependent', 'policy_name', 'policy_provider',
            'policy_type', 'start_date', 'end_date', 'attachment',
            'insured_scheme', 'insured_amount', 'annual_premium'
        ]

    def get_fields(self):
        fields = super().get_fields()
        user = self.context.get('user')
        if self.request and self.request.method.lower() != 'get':
            fields['dependent'] = serializers.SlugRelatedField(
                queryset=UserContactDetail.objects.filter(
                    user=user,
                    is_dependent=True
                ),
                slug_field='slug',
                many=True,
                required=False
            )
        if self.request and self.request.method.lower() == 'get':
            fields['dependent'] = UserContactDetailSerializer(
                fields=['name', 'contact_of', 'address', 'emergency', 'number',
                        'number_type', 'email', 'slug', 'is_dependent',
                        'date_of_birth', 'attachment'],
                many=True
            )
        return fields

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if end_date < start_date:
            raise ValidationError(
                {'detail': 'End date can\'t be smaller than start date.'})
        return super().validate(attrs)
