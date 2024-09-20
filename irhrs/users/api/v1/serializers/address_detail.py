from rest_framework.exceptions import ValidationError
from rest_framework import serializers

from irhrs.common.api.serializers.common import CountrySerializer, ProvinceSerializer, \
    DistrictSerializer
from irhrs.recruitment.models import Country, Province, District
from irhrs.users.api.v1.serializers.user_serializer_common import \
    UserSerializerMixin
from irhrs.users.models import UserAddress


class UserAddressSerializer(UserSerializerMixin):
    class Meta:
        model = UserAddress
        fields = ('address_type', 'street', 'city',
                  'country', 'address', 'latitude', 'longitude', 'id',
                  'user', 'province', 'district', 'postal_code')
        read_only_fields = ('user',)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        fields['country'] = serializers.PrimaryKeyRelatedField(
            queryset=Country.objects.all(), required=False, allow_null=True, source='country_ref'
        )
        fields['province'] = serializers.PrimaryKeyRelatedField(
            queryset=Province.objects.all(), required=False, allow_null=True
        )
        fields['district'] = serializers.PrimaryKeyRelatedField(
            queryset=District.objects.all(), required=False, allow_null=True
        )

        if request and request.method == 'GET':
            fields['province'] = ProvinceSerializer(fields=['id', "name"])
            fields['district'] = DistrictSerializer(fields=['id', "name"])
            fields['country'] = CountrySerializer(
                fields=['id', 'name', 'nationality'], source='country_ref'
            )
        return fields

    def validate_address_type(self, address_type):
        user = self.context.get('user')
        if user:
            qs = user.addresses.filter(address_type=address_type)
            if self.instance:
                qs = qs.exclude(address_type=self.instance.address_type)
            if qs.exists():
                raise ValidationError(
                    "This user already has this address type registered"
                )
        return address_type

    def validate(self, attrs):
        country = attrs.get('country_ref')
        province = attrs.get("province")
        district = attrs.get("district")
        if country and country.name != "Nepal" and (province or district):
            raise ValidationError("Currently province and district is not supported.")
        if country and country.name == "Nepal" and not (province and district):
            raise ValidationError("Province/district is required while selecting Nepal.")
        if province and district and not District.objects.filter(
            id=district.id, province=province
        ).exists():
            raise ValidationError({
                "district": f"{province.name} doesn't have {district.name} district."
            })
        return super().validate(attrs)


