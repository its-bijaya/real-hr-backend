from django.utils import timezone
from rest_framework.fields import SerializerMethodField, ReadOnlyField, \
    DateField
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.validators import validate_future_date_or_today
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer
from irhrs.users.models import UserExperience


class UserContractStatusSerializer(ModelSerializer):
    user = UserThinSerializer()
    supervisor = UserThinSerializer(
        source='user.first_level_supervisor')
    employment_level = ReadOnlyField(source='employment_level.title')
    status = SerializerMethodField()
    deadline = ReadOnlyField()
    employment_status = SerializerMethodField()

    class Meta:
        model = UserExperience
        fields = [
            'id', 'user', 'supervisor', 'employment_level',
            'start_date', 'end_date', 'status', 'deadline',
            'employment_status'
        ]

    def get_status(self, instance):
        if instance.end_date:
            days_delta = (instance.end_date - timezone.now().date()).days
            safe_days = self.context.get('safe_days', 30)
            critical_days = self.context.get('critical_days', 15)

            if days_delta < 0:
                return "Expired"
            elif days_delta <= critical_days:
                return "Critical"
            elif days_delta > safe_days:
                return "Safe"
            else:
                return "Medium"
        else:
            return "N/A"

    @staticmethod
    def get_employment_status(instance):
        return getattr(instance.employment_status, 'title', 'Status N/A')


class ContractRenewSerializer(DummySerializer):
    end_date = DateField(validators=[validate_future_date_or_today])

    def validate(self, attrs):
        end_date = attrs.get('end_date')
        overlapping_dates = UserExperience.objects.filter(
            user = self.context["user"]
        ).filter(
            end_date__gte = end_date,
        )
        if overlapping_dates:
            raise serializers.ValidationError({
                'end_date': 'Contract already exists until the given date.'
            })

        return attrs
