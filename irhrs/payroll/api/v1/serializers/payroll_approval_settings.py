from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.payroll.models import APPROVAL_PENDING, REJECTED
from irhrs.payroll.models.payroll_approval_settings import PayrollApprovalSetting
from irhrs.users.api.v1.serializers.thin_serializers import UserThumbnailSerializer

USER = get_user_model()


class PayrollApprovalSettingsSerializer(DynamicFieldsModelSerializer):
    user = UserThumbnailSerializer()

    class Meta:
        model = PayrollApprovalSetting
        fields = ('id', 'user', 'approval_level')


class PayrollApprovalSettingsCreateSerializer(DummySerializer):
    approvals = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=USER.objects.all().current()
        ),
        allow_empty=True,
        allow_null=False
    )

    @property
    def organization(self):
        return self.context['organization']

    @staticmethod
    def validate_approvals(approvals):
        if len(approvals) != len(set(approvals)):
            raise serializers.ValidationError("Duplicate users found.")
        return approvals

    def validate(self, attrs):
        if self.organization.payrolls.filter(
            status__in=[APPROVAL_PENDING, REJECTED]
        ).exists():
            raise serializers.ValidationError(
                _("A payroll is in approval process. You can not change this settings now.")
            )
        return attrs

    def create(self, validated_data):
        approvals = validated_data['approvals']
        PayrollApprovalSetting.objects.all().filter(
            organization=self.organization,
        ).delete()
        settings = []
        for approval_level, approval in enumerate(approvals, start=1):
            settings.append(PayrollApprovalSetting(
                approval_level=approval_level,
                organization=self.organization,
                user=approval
            ))
        PayrollApprovalSetting.objects.bulk_create(settings)
        return super().create(validated_data)

