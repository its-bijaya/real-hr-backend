from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from irhrs.common.api.serializers.common import ProvinceSerializer, CountrySerializer
from irhrs.recruitment.models import Province, Country
from .common_org_serializer import OrganizationSerializerMixin
from ....models import OrganizationBranch


class OrganizationBranchSerializer(OrganizationSerializerMixin):
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        max_length=200,
        validators=[UniqueValidator(queryset=OrganizationBranch.objects.all(),
                                    lookup='iexact',
                                    message='This email already exists')])
    code = serializers.CharField(
        required=True,
        max_length=15,
        validators=[UniqueValidator(queryset=OrganizationBranch.objects.all(),
                                    lookup='iexact',
                                    message='This code already exists')])

    class Meta(OrganizationSerializerMixin.Meta):
        model = OrganizationBranch
        fields = ('id','organization', 'name', 'description', 'contacts',
                  'branch_manager', 'slug', 'email', 'address', 'code', 'province', 'country',
                  'is_archived', 'mailing_address', 'created_at', 'modified_at', 'region')
        read_only_fields = ('slug',)
        extra_kwargs = {
            'branch_manager': {
                'required': False,
                'allow_null': True
            },
        }

    def validate(self, attrs):
        country = attrs.get('country_ref')
        province = attrs.get('province')
        description = attrs.get('description')
        if len(description) > 600:
            raise ValidationError({
                "description": "Ensure this field has no more than 600 characters."
            })
        nepal = Country.objects.filter(name="Nepal").first()
        if nepal and country == nepal and not (
            province and Province.objects.filter(id=province.id).exists()
        ):
            raise ValidationError({
                "province": "Please select valid province."
            })
        if nepal and province and country != nepal:
            raise ValidationError({
                "province": "Province not available for selected country."
            })

        return attrs

    def validate_name(self, name):
        organization = self.context.get('organization')
        qs = organization.branches.filter(name=name)
        if self.instance:
            qs = qs.exclude(name=self.instance.name)
        if qs.exists():
            raise ValidationError("This organization already has "
                                  "branch of this name.")
        return name

    def get_fields(self):
        from irhrs.users.api.v1.serializers.thin_serializers import \
            UserThinSerializer
        fields = super().get_fields()
        request = self.context.get('request')
        fields['country'] = serializers.PrimaryKeyRelatedField(
            queryset=Country.objects.all(), required=False, allow_null=True, source='country_ref'
        )
        fields['province'] = serializers.PrimaryKeyRelatedField(
            queryset=Province.objects.all(), required=False, allow_null=True
        )

        if request and request.method == 'GET':
            fields['branch_manager'] = UserThinSerializer(
                read_only=True, allow_null=True)
            fields['province'] = ProvinceSerializer(fields=['id', "name"])
            fields['country'] = CountrySerializer(
                fields=['id', 'name', 'nationality'], source='country_ref'
            )
        return fields

    def create(self, validated_data):
        validated_data.update({'organization': self.context.get(
            'organization')})
        instance = self.Meta.model.objects.create(
            **validated_data
        )
        return instance

    def update(self, instance, validated_data):
        contacts_data = validated_data.pop('contacts')
        updated_instance = super().update(instance, validated_data)
        updated_instance.contacts = contacts_data
        updated_instance.save()
        return updated_instance


class OrganizationBranchImportSerializer(OrganizationBranchSerializer):

    def get_fields(self):
        fields = super().get_fields()
        fields['country_ref'] = serializers.SlugRelatedField(
            queryset=Country.objects.all(), slug_field="name"
        )
        fields['province'] = serializers.SlugRelatedField(
            queryset=Province.objects.all(), required=False, allow_null=True, slug_field="name"
        )
        fields['contacts'] = serializers.CharField(
            max_length=255
        )
        return fields

    def validate(self, attrs):
        contacts = attrs.get('contacts')
        attrs["contacts"] = {
            'Phone': contacts
        }
        return super().validate(attrs)
