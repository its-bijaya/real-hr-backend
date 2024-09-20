from django.contrib.auth import get_user_model
from django.db.models import Q

from irhrs.core.constants.organization import GLOBAL
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.validators import validate_fiscal_year_months_amount
from irhrs.organization.models import FiscalYear
from irhrs.payroll.api.v1.serializers.payroll import RebateSettingSerializer
from irhrs.payroll.models.user_voluntary_rebate_requests import UserVoluntaryRebateAction, \
    UserVoluntaryRebateDocument, CREATED
from irhrs.payroll.models import (
    UserVoluntaryRebate,
    UserVoluntaryRebateAction,
    CREATE_REQUEST, RebateSetting
)
from irhrs.payroll.utils.generate import \
    raise_validation_error_if_payroll_in_generated_or_processing_state
from irhrs.payroll.utils.user_voluntary_rebate import get_ordered_fiscal_months_amount, \
    validated_fiscal_months_amount, archive_old_rebate_entry

from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

User = get_user_model()

class UserVoluntaryRebateDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVoluntaryRebateDocument
        fields = ('file', 'file_name')


class RequestUserVoluntaryRebateCreateSerializer(serializers.ModelSerializer):
    documents = UserVoluntaryRebateDocumentSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField()
    class Meta:
        model = UserVoluntaryRebate
        fields = (
            'id',
            'title',
            'rebate',
            'description',
            'fiscal_year',
            'duration_unit',
            'amount',
            'status',
            'documents'
        )

    def get_status(self, obj):
        return CREATE_REQUEST

    def validate(self, attrs):
        attrs = super().validate(attrs)
        rebate_amount = attrs.get('rebate').amount
        amount = attrs.get('amount')
        fiscal_year = attrs.get("fiscal_year")
        if attrs.get('duration_unit') == "Monthly":
            data = self.context.get('request').data
            organization = self.context.get('organization')
            fiscal_months_amount = validated_fiscal_months_amount(
                organization, rebate_amount, data, fiscal_year.id)
            attrs["fiscal_months_amount"] = fiscal_months_amount
            attrs["amount"] = round(sum(map(float, fiscal_months_amount.values())), 2)
        elif rebate_amount != 0 and rebate_amount < attrs.get('amount'):
            raise ValidationError("Rebate amount limit exceeded.")
        elif amount <= 0:
            raise ValidationError("Amount should be greater than Zero.")
        attrs['amount'] = round(amount, 2)
        return attrs

    def create(self, validated_data):
        instance = UserVoluntaryRebate.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        return instance


class UserVoluntaryRebateCreateSerializer(serializers.ModelSerializer):
    documents = UserVoluntaryRebateDocumentSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField()
    class Meta:
        model = UserVoluntaryRebate
        fields = (
            'id',
            'title',
            'rebate',
            'description',
            'user',
            'fiscal_year',
            'duration_unit',
            'amount',
            'status',
            'documents'
        )

    def get_status(self, obj):
        return CREATE_REQUEST

    def validate(self, attrs):
        attrs = super().validate(attrs)
        rebate_amount = attrs.get('rebate').amount
        amount = attrs.get('amount')
        fiscal_year = attrs.get("fiscal_year")
        organization = self.context.get('organization')
        raise_validation_error_if_payroll_in_generated_or_processing_state(organization)
        if attrs.get('duration_unit') == "Monthly":
            data = self.context.get('request').data
            fiscal_months_amount = validated_fiscal_months_amount(
                organization, rebate_amount, data, fiscal_year.id)
            attrs["fiscal_months_amount"] = fiscal_months_amount
            attrs["amount"] = round(sum(map(float, fiscal_months_amount.values())), 2)
            return attrs
        elif rebate_amount and rebate_amount != 0 and rebate_amount < attrs.get('amount'):
            raise ValidationError("Rebate amount limit exceeded.")
        elif amount<= 0:
            raise ValidationError("Amount should be greater than Zero.")
        attrs['amount'] = round(amount, 2)
        return attrs


class UserVoluntaryRebateImportSerializer(serializers.Serializer):
    user = serializers.CharField(max_length=255)
    rebate_type = serializers.CharField(max_length=255)
    title = serializers.CharField(max_length=255)
    fiscal_year = serializers.CharField(max_length=255)
    amount = serializers.FloatField(min_value=0)
    description = serializers.CharField(max_length=600)
    remarks = serializers.CharField(max_length=600)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = attrs.pop("user")
        organization = self.context.get('organization')
        user = User.objects.filter(Q(username=user) | Q(email=user),
                                   detail__organization=organization).first()
        if not user:
            raise serializers.ValidationError("username/email doesn't exists")
        attrs["user"] = user
        rebate_type = attrs.pop('rebate_type')
        rebate = RebateSetting.objects.filter(title=rebate_type, organization=organization).first()
        if not rebate:
            raise serializers.ValidationError("Rebate Type doesn't exists")
        attrs["rebate_type"] = rebate
        rebate_amount = rebate.amount
        amount = attrs.get('amount')
        fiscal_year_name = attrs.pop("fiscal_year")
        fiscal_year = FiscalYear.objects.filter(name=fiscal_year_name, organization=organization,
                                                category=GLOBAL).first()
        if not fiscal_year:
            raise serializers.ValidationError("Fiscal Year doesn't exists")
        attrs['fiscal_year'] = fiscal_year
        raise_validation_error_if_payroll_in_generated_or_processing_state(organization)
        if rebate_amount and rebate_amount != 0 and rebate_amount < attrs.get('amount'):
            raise ValidationError("Rebate amount limit exceeded.")
        elif amount <= 0:
            raise ValidationError("Amount should be greater than Zero.")
        attrs['amount'] = round(amount, 2)
        return attrs

    def create(self, validated_data):
        rebate_type = validated_data.pop('rebate_type')
        rebate_duration = rebate_type.duration_type
        remarks = validated_data.pop('remarks', "")
        rebate = UserVoluntaryRebate.objects.create(**validated_data, rebate=rebate_type,
                                                    duration_unit=rebate_duration)
        archive_old_rebate_entry(rebate)
        return UserVoluntaryRebateAction.objects.create(user_voluntary_rebate=rebate, action=CREATED,
                                                        remarks=remarks)

class UserVoluntaryRebateListSerializer(DynamicFieldsModelSerializer):
    remarks = serializers.CharField(required=True, write_only=True)
    documents = UserVoluntaryRebateDocumentSerializer(many=True)
    fiscal_year_name = serializers.ReadOnlyField(source="fiscal_year.name")
    rebate = RebateSettingSerializer()
    user = UserThinSerializer(
        fields=(
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'organization', 'is_current',
        )
    )

    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.status

    class Meta:
        model = UserVoluntaryRebate
        fields = (
            'id',
            'user',
            'title',
            'rebate',
            'description',
            'fiscal_year',
            'fiscal_year_name',
            'duration_unit',
            'amount',
            'status',
            'documents',
            'remarks',
            'fiscal_months_amount'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == "get":
            fields["fiscal_months_amount"] = serializers.SerializerMethodField()
        return fields

    def get_fiscal_months_amount(self, obj):
        return get_ordered_fiscal_months_amount(
            self.context.get('organization'), obj.fiscal_months_amount)


class RequestUserVoluntaryRebateListSerializer(DynamicFieldsModelSerializer):
    documents = UserVoluntaryRebateDocumentSerializer(many=True)
    status = serializers.SerializerMethodField()
    fiscal_year_name = serializers.ReadOnlyField(source="fiscal_year.name")
    rebate = RebateSettingSerializer()

    def get_status(self, obj):
        return obj.status

    class Meta:
        model = UserVoluntaryRebate
        fields = (
            'id',
            'title',
            'rebate',
            'description',
            'fiscal_year',
            'fiscal_year_name',
            'duration_unit',
            'amount',
            'status',
            'documents',
            'fiscal_months_amount'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == "get":
            fields["fiscal_months_amount"] = serializers.SerializerMethodField()
        return fields

    def get_fiscal_months_amount(self, obj):
        return get_ordered_fiscal_months_amount(
            self.context.get('organization'), obj.fiscal_months_amount)


class RebateActionHistorySerializer(serializers.ModelSerializer):

    created_by = UserThinSerializer(
        fields=(
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'organization', 'is_current',
        )
    )

    status = serializers.ReadOnlyField(source='action')
    class Meta:
        model = UserVoluntaryRebateAction
        fields = [
            'created_by',
            'remarks',
            'created_at',
            'status'
        ]


class UserVoluntaryRebateActionRemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVoluntaryRebateAction
        fields = ('remarks', )

