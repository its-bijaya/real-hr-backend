from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.users.models import User
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import get_today, get_yesterday
from irhrs.common.models import DutyStation
from irhrs.hris.models import DutyStationAssignment

User = get_user_model()
USER_FIELDS = ['id', 'full_name', 'profile_picture', 'cover_picture',
               'division', 'organization', 'job_title']

class DutyStationCommonMixin:
    def validate(self, attrs, *args):
        error_messages = dict()
        from_date = attrs.get('from_date')
        to_date = attrs.get('to_date', None)
        user = attrs.get('user')
        if to_date and from_date >= to_date:
            error_messages['start_date'] = 'to_date` must be greater than `from_date`.'

        previous_assignments = DutyStationAssignment.objects.filter(
            user = user,
            organization = self.context["organization"]
        ).exclude(duty_station__is_archived=True)
        has_prev_to_date_null = previous_assignments.filter(
            to_date__isnull=True
        ).exists()
        if self.context and self.context["action"] == "create":
            if has_prev_to_date_null and not to_date:
                error_messages['non_field_error'] =  (
                        "This user has `to_date` set to null in a previous "
                        "duty station assignment. Please change that before "
                        "assigning a new duty station."
                    )
                raise ValidationError(
                    error_messages
                )
        if previous_assignments:
            if to_date:
                overlapping_assignments = previous_assignments.filter(
                    Q(
                        Q(
                            Q(to_date=None) &
                            Q(
                                from_date__lte=get_today()
                            )
                        ) |
                        Q(
                            ~Q(to_date=None) &
                            Q(
                                from_date__lte=to_date,
                                to_date__gte=from_date
                            )
                        )
                    ),
                )
            else:
                overlapping_assignments = previous_assignments.filter(
                    Q(
                        Q(
                            Q(to_date=None) &
                            Q(
                                from_date__lte=get_today()
                            )
                        ) |
                        Q(
                            ~Q(to_date=None) &
                            Q(
                                from_date__lte=get_today(),
                                to_date__gte=from_date
                            )
                        )
                    ),
                )
            if self.context and self.context["action"] in \
               ["update", "partial_update"]:
                overlapping_assignments = overlapping_assignments.exclude(
                    id=self.instance.id
                )
            if overlapping_assignments.exists():
                error_messages['non_field_error'] = (
                    (
                        "This user has previous duty "
                        "station assignments in the provided date range."
                    )
                )
        if error_messages.keys():
            raise ValidationError(
                error_messages
            )
        return attrs

    def create(self, validated_data):
        organization = self.context["organization"]
        validated_data.update({"organization": organization})
        duty_station_assignment = DutyStationAssignment.objects.create(**validated_data)
        return duty_station_assignment

    def update(self, instance, validated_data):
        validated_data["organization"] = self.context["organization"]
        return super().update(instance, validated_data)


class DutyStationAssignmentSerializer(DutyStationCommonMixin, DynamicFieldsModelSerializer):
    duty_station_name = serializers.SerializerMethodField()
    user_detail = UserThinSerializer(fields=USER_FIELDS, read_only=True, source='user')

    class Meta:
        model = DutyStationAssignment
        fields = [
            'id','duty_station', 'user', 'from_date',
            'to_date', 'duty_station_name', 'user_detail'
        ]
        read_only_fields = ('user_detail',)
        extra_kwargs = {'to_date': {'required': True}}

    @staticmethod
    def get_duty_station_name(obj):
        return obj.duty_station.name


class DutyStationImportSerializer(DutyStationCommonMixin, serializers.Serializer):
    user = serializers.CharField(max_length=255)
    duty_station = serializers.CharField(max_length=255)
    from_date = serializers.DateField(required=False, allow_null=True)
    to_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        user = attrs.pop("user")
        duty_station_slug = attrs.pop("duty_station")
        from_date = attrs.get("from_date")
        if not from_date:
            raise serializers.ValidationError("From date doesn't exists")
        
        user = User.objects.filter(Q(username=user) | Q(email=user)).first()
        if not user:
            raise serializers.ValidationError("username/email doesn't exists")
        attrs["user"] = user

        duty_station = DutyStation.objects.filter(slug=duty_station_slug).first()
        if not duty_station:
            raise serializers.ValidationError("Duty Station doesn't exists")
        attrs["duty_station"] = duty_station

        return super().validate(attrs)


class CurrentDutyStationAssignmentSerializer(serializers.ModelSerializer):
    # current_duty_station = serializers.SerializerMethodField()
    duty_station = serializers.SerializerMethodField()
    duty_station_assignment_id = serializers.ReadOnlyField()
    user_detail = UserThinSerializer(fields=USER_FIELDS, read_only=True, source='*')
    user = serializers.SerializerMethodField()
    from_date = serializers.ReadOnlyField()
    to_date = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            'user_detail',
            'duty_station',
            'duty_station_assignment_id',
            'from_date',
            'to_date',
            'user'
        )

    @staticmethod
    def get_user(obj):
        return obj.id

    @staticmethod
    def get_duty_station(obj):
        duty_station = {
            "id": getattr(obj, 'duty_station_id', None),
            "name": getattr(obj, 'duty_station_name', None)
        }
        return duty_station
