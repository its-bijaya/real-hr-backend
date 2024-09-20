from math import isnan

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from irhrs.core.constants.payroll import REQUESTED, APPROVED, FORWARDED, CONFIRMED
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import subordinates
from irhrs.core.utils.common import get_today
from irhrs.payroll.api.v1.serializers.unit_of_work_settings import OperationRateSerializer
from irhrs.payroll.models import UnitOfWorkRequest, UnitOfWorkRequestHistory
from irhrs.payroll.models.unit_of_work_settings import UserOperationRate
from irhrs.users.api.v1.serializers.thin_serializers import UserThumbnailSerializer


class UnitOfWorkRequestHistorySerializer(DynamicFieldsModelSerializer):
    action_performed_by = UserThumbnailSerializer()
    action_performed_to = UserThumbnailSerializer()
    message = serializers.ReadOnlyField(source='__str__')

    class Meta:
        model = UnitOfWorkRequestHistory
        fields = ('created_at', 'action_performed_by', 'action_performed',
                  'action_performed_to', 'message')


class UnitOfWorkRequestSerializer(DynamicFieldsModelSerializer):
    histories = UnitOfWorkRequestHistorySerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()

    class Meta:
        model = UnitOfWorkRequest
        fields = [
            'id', 'user', 'recipient', 'rate',
            'quantity', 'status', 'attachment',
            'remarks', 'created_by', 'created_at',
            'modified_at', 'histories', 'total'
        ]
        read_only_fields = ('recipient', 'id')

    @property
    def organization(self):
        return self.context.get('organization')

    @property
    def mode(self):
        return self.context['view'].mode

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method.lower() == 'get':
            if 'user' in fields:
                fields['user'] = UserThumbnailSerializer(context=self.context)
            if 'recipient' in fields:
                fields['recipient'] = UserThumbnailSerializer(context=self.context)
            if 'created_by' in fields:
                fields['created_by'] = UserThumbnailSerializer(context=self.context)
            if 'rate' in fields:
                fields['rate'] = OperationRateSerializer(
                    fields=['id', 'operation', 'operation_code', 'rate'],
                    context=self.context
                )
        return fields

    def validate_rate(self, rate):
        if not rate.operation.organization == self.organization:
            raise serializers.ValidationError(_("Rate is from different organization"))
        return rate

    def validate_user(self, user):
        if not user.detail.organization == self.organization:
            raise serializers.ValidationError(_("User is from different organization"))

        if not user.first_level_supervisor_including_bot:
            raise serializers.ValidationError(_("User has no supervisor set."))

        if self.mode == 'user' and user != self.request.user:
            raise serializers.ValidationError(_("User not matched according to mode."))

        if (
            self.mode == 'supervisor' and
            user.first_level_supervisor_including_bot != self.request.user
        ):
            raise serializers.ValidationError(_("User is not immediate subordinate."))

        return user

    def validate_status(self, status):
        if self.mode == 'supervisor' and status not in [APPROVED, FORWARDED]:
            raise serializers.ValidationError(
                _("The value should be one of `Approved`, `Forwarded`")
            )
        elif self.mode == 'hr' and status != CONFIRMED:
            raise serializers.ValidationError(
                _("The value must be Confirmed.")
            )
        return status

    def validate(self, attrs):
        status = attrs.get('status')
        quantity = attrs.get('quantity')

        if not quantity or isnan(quantity):
            raise serializers.ValidationError({
                'quantity': _("Quantity must be valid integer or float number")
            })

        if self.mode in ['hr', 'supervisor'] and not status:
            raise serializers.ValidationError({
                'status': _("This field is required")
            })

        if self.mode == 'supervisor':
            user = attrs.get('user')
            status_action_map = {
                APPROVED: 'approve',
                FORWARDED: 'forward'
            }
            if not subordinates.authority_exists(
                user, self.request.user, status_action_map[status]
            ):
                raise serializers.ValidationError(
                    f"You are not allowed to {status_action_map[status]} the request."
                )
        return attrs

    @transaction.atomic()
    def create(self, validated_data):
        validated_data['recipient'] = validated_data['user'].first_level_supervisor_including_bot
        user = validated_data.get('user')
        rate = validated_data.get('rate')

        if not UserOperationRate.objects.filter(user=user, rate=rate).exists():
            raise serializers.ValidationError(_("Cannot request unit of work for unassigned user."))

        if self.mode == 'user':
            validated_data['status'] = REQUESTED
        elif self.mode == 'supervisor':

            if validated_data.get('status') == FORWARDED:

                try:
                    # next level supervisor
                    validated_data['recipient'] = validated_data['user'].user_supervisors[1].supervisor
                except (AttributeError, IndexError):
                    raise serializers.ValidationError({
                        'non_field_errors': _(
                            "Could not create request. You do not have authority"
                            " to approve, and next level supervisor not set to forward.")
                    })

        if validated_data['status'] == CONFIRMED:
            validated_data['confirmed_on'] = get_today()

        instance = super().create(validated_data)

        UnitOfWorkRequestHistory.objects.create(
            request=instance,
            action_performed_by=self.request.user,
            action_performed_to=validated_data['recipient'],
            action_performed=instance.status,
            remark=instance.remarks
        )

        return instance
