from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework import serializers

from irhrs.common.api.serializers.common import BankSerializer
from irhrs.common.models import Bank
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.models.other import UserBank
from irhrs.users.utils.notification import send_change_notification_to_user

USER = get_user_model()

class UserBankSerializer(DynamicFieldsModelSerializer):

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['bank'] = BankSerializer(context=self.context, fields=['id', 'name', 'slug'])
        return fields

    class Meta:
        model = UserBank
        fields = ('user', 'bank', 'branch', 'account_number')

    def create(self, validated_data):
        validated_data.update(dict(user=self.context.get('user')))
        instance = super().create(validated_data)
        request = self.context.get('request')
        send_notification = self.context.get('send_notification', True)
        if send_notification:
            send_change_notification_to_user(self, instance, instance.user, request.user, 'created')
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        request = self.context.get('request')
        send_notification = self.context.get('send_notification', True)
        if send_notification:
            send_change_notification_to_user(self, instance, instance.user, request.user, 'updated')
        return instance

class UserBankInfoImportSerializer(serializers.Serializer):
    user = serializers.CharField(max_length=255)
    bank = serializers.CharField(max_length=255)
    account_number = serializers.CharField(max_length=255)
    branch = serializers.CharField(max_length=255, required=False, allow_null=True)


    def validate(self, attrs):
        fields = super().validate(attrs)
        user = fields.pop("user")
        bank = fields.pop("bank")
        user = USER.objects.filter(Q(username=user) | Q(email=user)).first()
        if not user:
            raise serializers.ValidationError("username/email doesn't exists.")
        bank = Bank.objects.filter(slug=bank).first()
        if not bank:
            raise serializers.ValidationError("Bank doesn't exists.")
        fields["user_id"] = user.id
        fields["bank"] = bank
        return fields

    def create(self, validated_data):
        user_id = validated_data.get('user_id')
        UserBank.objects.filter(user_id=user_id).delete()
        ctx = self.context
        ctx["send_notification"] = False
        instance = UserBankSerializer(context=ctx).create(validated_data)
        return instance
