from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from irhrs.common.api.serializers.common import BankSerializer
from irhrs.common.models.commons import Bank
from ....models import OrganizationBank, validate_title, validate_has_digit, \
    validate_invalid_chars
from .common_org_serializer import OrganizationSerializerMixin


class OrganizationBankSerializer(OrganizationSerializerMixin):
    email = serializers.CharField(
        max_length=200,
        validators=[UniqueValidator(queryset=OrganizationBank.objects.all(),
                                    lookup='iexact',
                                    message='This email already exists')])
    branch = serializers.CharField(
        max_length=150,
        required=True,
        validators=[validate_title])
    account_number = serializers.CharField(
        max_length=150,
        required=True,
        validators=[validate_has_digit, validate_invalid_chars])
    bank = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Bank.objects.all()
    )
    bank_name = serializers.ReadOnlyField(source='bank.name')

    class Meta(OrganizationSerializerMixin.Meta):
        model = OrganizationBank
        fields = ('organization', 'bank', 'branch', 'account_number', 'id',
                  'contacts', 'email', 'contact_person', 'created_at', 'modified_at', 'bank_name')

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('request') and self.context.get('request').method \
                == 'GET':
            fields['bank'] = serializers.SerializerMethodField()
        return fields

    def validate_account_number(self, account_number):
        organization = self.context.get('organization')
        qs = organization.banks.filter(account_number__iexact=account_number)
        if self.instance:
            qs = qs.exclude(account_number=self.instance.account_number)
        if qs.exists():
            raise ValidationError("This organization already has "
                                  "bank of this account number.")
        return account_number

    def get_bank(self, obj):
        if obj.bank:
            return BankSerializer(instance=obj.bank,
                                  fields=['name', 'slug']).data
        return {}

    def create(self, validated_data):
        contacts_data = validated_data.pop('contacts')
        validated_data.update({'contacts': {}})
        instance = super().create(validated_data)
        instance.contacts = contacts_data
        instance.save()
        return instance

    def update(self, instance, validated_data):
        contacts_data = validated_data.pop('contacts')
        updated_instance = super().update(instance, validated_data)
        updated_instance.contacts = contacts_data
        updated_instance.save()
        return updated_instance
