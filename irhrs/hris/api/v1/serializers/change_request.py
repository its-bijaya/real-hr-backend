from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.constants.user import PENDING
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models.change_request import ChangeRequestDetails, \
    ChangeRequest


class ChangeRequestDetailsSerializer(ModelSerializer):
    change_field = SerializerMethodField()

    class Meta:
        model = ChangeRequestDetails
        fields = [
            "new",
            "new_value_display",
            "old",
            "old_value_display",
            "change_field",
            "is_filefield"
        ]

    def get_change_field(self, instance):
        return instance.change_field.replace("_", " ").title()


class ChangeRequestSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(read_only=True)
    details = SerializerMethodField()
    remarks = serializers.CharField(max_length=200)

    class Meta:
        model = ChangeRequest
        fields = [
            "id", "user", "status", "remarks", "created_at",
            "category", "action", "details",
        ]

    def get_details(self, instance):
        # Ignore user field from change request detail
        return ChangeRequestDetailsSerializer(instance.details.all().exclude(
            change_field__in=["user", "uploaded_by"]
        ), many=True, context=self.context).data


class ChangeRequestUpdateSerializer(DynamicFieldsModelSerializer):
    remarks = serializers.CharField(max_length=200)

    def validate(self, attrs):
        if self.instance and self.instance.status != PENDING:
            raise ValidationError("Can not act on already acted change "
                                  "request.")
        return attrs

    class Meta:
        model = ChangeRequest
        fields = ('remarks',)
