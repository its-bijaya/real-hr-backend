from django.db import transaction
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.core.utils.common import DummyObject, get_today
from irhrs.leave.api.v1.serializers.settings import LeaveTypeSerializer
from irhrs.leave.constants.model_constants import APPROVED, DENIED, GENERATED
from irhrs.leave.models.account import LeaveEncashment, LeaveEncashmentHistory
from irhrs.users.api.v1.serializers.thin_serializers import UserThumbnailSerializer


class LeaveEncashmentSerializer(DynamicFieldsModelSerializer):
    leave_type = LeaveTypeSerializer(
        fields=['id', 'name', 'category'], source='account.rule.leave_type',
        read_only=True
    )
    user = UserThumbnailSerializer(read_only=True)
    remarks = serializers.CharField(max_length=255, write_only=True)

    class Meta:
        model = LeaveEncashment
        fields = (
            'id',
            'user',
            'leave_type',
            'balance',
            'status',
            'source',
            'created_at',
            'modified_at',
            'remarks'
        )
        read_only_fields = ('id', 'status', 'created_at', 'modified_at')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['balance'] = serializers.ReadOnlyField(source='balance_display')
        return fields

    def validate(self, attrs):
        if self.instance and self.instance.status != GENERATED:
            raise serializers.ValidationError(
                "Can only update balance of encashment with `Generated` status"
            )
        return attrs

    def update(self, instance, validated_data):
        previous_balance = instance.balance
        remarks = validated_data.pop('remarks', '')
        instance = super().update(instance, validated_data)
        new_balance = instance.balance

        LeaveEncashmentHistory.objects.create(
            actor=self.request.user,
            encashment=instance,
            action="Updated",
            previous_balance=previous_balance,
            new_balance=new_balance,
            remarks=remarks
        )

        return instance


class LeaveEncashmentActionSerializer(DummySerializer):
    remarks = serializers.CharField(max_length=255, write_only=True)
    status = serializers.ChoiceField(choices=(
        APPROVED, DENIED
    ))
    id = serializers.PrimaryKeyRelatedField(queryset=LeaveEncashment.objects.all())

    def validate_id(self, encashment):
        organization = self.context.get('organization')
        if encashment.user.detail.organization != organization:
            raise serializers.ValidationError({"id": ["Encashment from different organization"]})

        if encashment.status != GENERATED:
            raise serializers.ValidationError(
                {"id": [f"Can not act on {encashment.status} encashments."]}
            )
        return encashment


class LeaveEncashmentBulkActionSerializer(DummySerializer):
    actions = LeaveEncashmentActionSerializer(many=True, write_only=True)

    @property
    def request(self):
        return self.context.get('request')

    @transaction.atomic
    def create(self, validated_data):
        actions = validated_data.get('actions', [])
        for action in actions:
            encashment = action['id']
            encashment.status = action['status']

            if action['status'] == APPROVED:
                encashment.approved_on = get_today(with_time=True)

            encashment.save()

            LeaveEncashmentHistory.objects.create(
                encashment=encashment,
                actor=self.request.user,
                action=encashment.status,
                previous_balance=encashment.balance,
                new_balance=encashment.balance,
                remarks=action['remarks']
            )
        return DummyObject(actions=actions)


class LeaveEncashmentHistorySerializer(DynamicFieldsModelSerializer):
    message = serializers.ReadOnlyField(source='__str__')
    actor = UserThumbnailSerializer()
    previous_balance = serializers.ReadOnlyField(source='previous_balance_display')
    new_balance = serializers.ReadOnlyField(source='new_balance_display')

    class Meta:
        model = LeaveEncashmentHistory
        fields = (
            "id",
            "actor",
            "action",
            "previous_balance",
            "new_balance",
            "remarks",
            "message",
            "created_at"
        )
