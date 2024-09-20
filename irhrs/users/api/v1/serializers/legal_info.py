from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework import serializers

from irhrs.users.api.v1.serializers.user_serializer_common import UserSerializerMixin
from irhrs.users.models import UserLegalInfo

USER = get_user_model()

class UserLegalInfoSerializer(UserSerializerMixin):
    class Meta:
        model = UserLegalInfo
        fields = (
            'pan_number',
            'pf_number',
            'cit_number',
            'citizenship_number',
            'citizenship_issue_date',
            'citizenship_issue_place',
            'passport_number',
            'passport_issue_date',
            'passport_issue_place',
            'ssfid'
        )

class UserLegalInfoImportSerializer(serializers.Serializer):
    pf_number = serializers.CharField(max_length=255, required=False, allow_blank=True)
    cit_number = serializers.CharField(max_length=255, required=False, allow_blank=True)
    pan_number = serializers.CharField(max_length=255)
    citizenship_number = serializers.CharField(max_length=255)
    citizenship_issue_date = serializers.DateField(required=False, allow_null=True)
    citizenship_issue_place = serializers.CharField(max_length=255, required=False, allow_blank=True)
    passport_number = serializers.CharField(max_length=255, required=False, allow_blank=True)
    passport_issue_date = serializers.DateField(required=False, allow_null=True)
    passport_issue_place = serializers.CharField(max_length=255, required=False, allow_blank=True)
    ssfid = serializers.CharField(max_length=255, required=False, allow_blank=True)
    user = serializers.CharField(max_length=255)

    def validate(self, attrs):
        fields = super().validate(attrs)
        user = fields.pop("user")
        user = USER.objects.filter(Q(username=user) | Q(email=user)).first()
        if not user:
            raise serializers.ValidationError("username/email doesn't exists")
        fields["user_id"] = user.id
        return fields

    def create(self, validated_data):
        user_id = validated_data.get('user_id')
        UserLegalInfo.objects.filter(user_id=user_id).delete()
        instance = UserLegalInfoSerializer(
            context=self.context
        ).create(validated_data)
        return instance

