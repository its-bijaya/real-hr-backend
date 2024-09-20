from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject
from irhrs.hris.models import User
from irhrs.organization.api.v1.serializers.common_org_serializer import OrganizationSerializerMixin
from irhrs.payroll.models.unit_of_work_settings import Operation, OperationRate, OperationCode, \
    UserOperationRate
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class UniqueTitleOrganizationValidatorMixin:

    def validate_title(self, title):
        # validate title unique to organization
        qs = self.Meta.model.objects.all()
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.filter(
            title=title, organization=self.context.get('organization')
        ).exists():
            raise serializers.ValidationError(
                _("Record exists with this title for this organization")
            )
        return title


class OperationSerializer(UniqueTitleOrganizationValidatorMixin, OrganizationSerializerMixin):
    class Meta:
        model = Operation
        fields = ('id', 'title', 'description', 'created_at', 'modified_at')


class OperationCodeSerializer(UniqueTitleOrganizationValidatorMixin, OrganizationSerializerMixin):
    class Meta:
        model = OperationCode
        fields = ('id', 'title', 'description', 'created_at', 'modified_at')


class OperationRateSerializer(DynamicFieldsModelSerializer):
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = OperationRate
        fields = (
            'id', 'operation', 'operation_code', 'rate', 'created_at', 'modified_at', 'unit',
            'user_count'
        )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('operation', 'operation_code'),
                message=_("Rate already exists for this operation and code.")
            )
        ]

    def validate_operation(self, operation):
        organization = self.context.get('organization')
        if operation.organization != organization:
            raise serializers.ValidationError(
                _("Operation is from different organization")
            )
        return operation

    def validate_operation_code(self, operation_code):
        organization = self.context.get('organization')
        if operation_code.organization != organization:
            raise serializers.ValidationError(
                _("Operation Code is from different organization")
            )
        return operation_code

    def get_fields(self):
        fields = super().get_fields()

        if self.request and self.request.method.upper() == 'GET':
            fields['operation'] = OperationSerializer(fields=['id', 'title', 'description'])
            fields['operation_code'] = OperationCodeSerializer(fields=['id', 'title', 'description'])

        return fields

    def get_user_count(self, obj):
        user = User.objects.filter(user_operation_rate__rate=obj).count()
        return user


class OperationRateImportSerializer(OperationRateSerializer):
    operation = serializers.SlugRelatedField(
        queryset=Operation.objects.all(),
        slug_field='title'
    )
    operation_code = serializers.SlugRelatedField(
        queryset=OperationCode.objects.all(),
        slug_field='title'
    )


class OperationRateUserSerializer(DynamicFieldsModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = OperationRate
        fields = (
            "id",
            "user"
        )

    def get_user(self, obj):
        qs = User.objects.filter(user_operation_rate__rate=obj).order_by("first_name")
        user = UserThinSerializer(
            qs,
            many=True,
            fields=('id', 'full_name', 'profile_picture', 'job_title', 'organization', 'is_current', 'is_online')
        )
        return user.data


class UserOperationRateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    class Meta:
        model = UserOperationRate
        fields = ('user', )

    def create(self, validated_data):
        users = validated_data.get('user')
        rate = self.context.get('rate_id')
        user_operation_rate = UserOperationRate.objects.filter(
            rate=rate
        ).first()
        if not user_operation_rate:
            self.create_user_operation_rate(rate, users)
        else:
            self.update_users(rate, users)
        return DummyObject(**validated_data)

    def create_user_operation_rate(self, rate, users):
        new_user_operation_rate = list()
        organization = self.context.get('organization')
        for user in users:
            instance = User.objects.get(id=user.id)
            user_organization = getattr(instance.detail, 'organization', None)
            if user_organization != organization:
                raise serializers.ValidationError(
                    _("Cannot assign user from different organization to rate")
                )
            new_user_operation_rate.append(
                UserOperationRate(
                    rate_id=int(rate),
                    user=user
                )
            )
        if new_user_operation_rate:
            UserOperationRate.objects.bulk_create(new_user_operation_rate)

    def update_users(self, rate, users):
        UserOperationRate.objects.filter(rate_id=int(rate)).delete()
        self.create_user_operation_rate(rate, users)
