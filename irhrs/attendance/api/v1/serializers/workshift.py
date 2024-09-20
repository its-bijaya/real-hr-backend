from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField

from irhrs.attendance.models import WorkShift, WorkDay, WorkShiftLegend
from irhrs.attendance.models.workshift import WorkTiming
from irhrs.attendance.utils.attendance import find_conflicting_work_days, create_work_days, \
    has_work_day_changed
from irhrs.attendance.validation_error_messages import AT_LEAST_ONE_REQUIRED, \
    START_TIME_MUST_BE_GREATER, REPEATING_DAYS, CONFLICTING_WORK_DAYS, AT_LEAST_ONE_DAY_REQUIRED
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    DummySerializer
from irhrs.core.utils.common import get_today, get_tomorrow, validate_used_data, DummyObject

User = get_user_model()


class WorkTimingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = WorkTiming
        fields = ("id", "start_time", "end_time", "working_minutes", "extends",)
        read_only_fields = ("id", "working_minutes",)

    def validate(self, attrs):
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        extends = attrs.get("extends")
        if start_time > end_time and not extends:
            raise ValidationError(START_TIME_MUST_BE_GREATER)
        return attrs


class WorkDaySerializer(DynamicFieldsModelSerializer):
    timings = WorkTimingSerializer(
        many=True,
        allow_null=False
    )

    class Meta:
        model = WorkDay
        fields = (
            "day",
            "applicable_from",
            "applicable_to",
            "timings"
        )
        read_only_fields = ("applicable_from", "applicable_to")

    # We'll not use the serializer to crate or update so no changes
    # only validate it here

    def validate_timings(self, work_timings):
        if not work_timings:
            raise ValidationError(AT_LEAST_ONE_REQUIRED)
        return work_timings

    def create(self, validated_data):
        validated_data.pop('work_timings', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('work_timings', None)
        return super().update(instance, validated_data)


class WorkShiftSerializer(DynamicFieldsModelSerializer):
    work_days = WorkDaySerializer(
        many=True,
        allow_null=False
    )
    is_expiring = SerializerMethodField()
    is_active = SerializerMethodField()

    class Meta:
        model = WorkShift
        fields = (
            "id",
            "is_active",
            "name",
            "start_time_grace",
            "end_time_grace",
            "work_days",
            "is_default",
            "is_expiring",
            "description"
        )

    def get_is_expiring(self, instance):
        return not instance.individual_shifts.filter(
            applicable_to__isnull=True
        ).exists()

    def validate_work_days(self, work_days):
        if not work_days:
            return []
            # raise ValidationError(AT_LEAST_ONE_DAY_REQUIRED)

        # repeating work days
        days = []
        for work_day in work_days:
            if work_day.get('day') in days:
                raise ValidationError(REPEATING_DAYS)
            else:
                days.append(work_day.get('day'))

        # find conflicting workdays
        if find_conflicting_work_days(work_days):
            raise ValidationError(CONFLICTING_WORK_DAYS)
        return work_days

    def create(self, validated_data):
        work_days_data = validated_data.pop('work_days', None)
        validated_data.update({
            'organization': self.context.get('organization')
        })

        work_shift = super().create(validated_data)
        create_work_days(work_days_data, work_shift)

        return work_shift

    def update(self, instance, validated_data):
        work_days_data = validated_data.pop('work_days', None)

        today = get_today()
        tomorrow = get_tomorrow()

        # delete settings which are not applied yet, there is no need to keep
        # their log
        instance.work_days.filter(applicable_from__gt=today).delete()

        not_changed = list()
        new = list()

        for work_day_data in work_days_data:
            try:
                work_day = instance.work_days.applicable().get(
                    day=work_day_data.get('day')
                )
            except WorkDay.DoesNotExist:
                work_day = None

            if work_day:
                is_changed = has_work_day_changed(work_day, work_day_data)
                if is_changed:
                    work_day_data.update({'applicable_from': tomorrow})
                    new.append(work_day_data)
                else:
                    not_changed.append(work_day.id)
            else:
                work_day_data.update({'applicable_from': tomorrow})
                new.append(work_day_data)

        instance.work_days.applicable().exclude(id__in=not_changed).update(
            applicable_to=today
        )
        create_work_days(new, work_shift=instance)

        return super().update(instance, validated_data)

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        self.update_regular_shift(instance)
        return instance

    def update_regular_shift(self, instance):
        organization = self.context.get('organization')
        if instance.is_default:
            # if current instance is regular set previous regular
            # to not regular
            WorkShift.objects.exclude(id=instance.id).filter(
                organization=organization,
                is_default=True
            ).update(is_default=False)

    def get_fields(self):
        fields = super().get_fields()

        if self.request and self.request.method.upper() == 'GET':
            if fields.get('work_days'):
                fields['work_days'] = SerializerMethodField()

        return fields

    def get_work_days(self, instance):
        return WorkDaySerializer(
            instance.work_days.applicable(), many=True
        ).data

    def validate(self, attrs):
        organization = self.context.get('organization')
        name = attrs.get('name')
        if organization and name:
            qs = WorkShift.objects.filter(
                organization=organization,
                name__iexact=name
            )
            if self.instance:
                qs = qs.exclude(
                    pk=self.instance.pk
                )
            if qs.exists():
                raise ValidationError({
                    'name':
                        'The organization already has a work shift of this name'
                })
        return attrs

    def get_is_active(self, obj):
        return validate_used_data(
            obj,
            related_names=[
                'old_change_types',
                'new_change_types',
                'individual_shifts',
                'timesheets'
            ]
        )


class UserWorkTimingSerializer(DummySerializer):
    shift = WorkShiftSerializer(fields=["id", "name"], allow_null=True)
    timing = WorkTimingSerializer(allow_null=True, exclude_fields=["working_minutes"])
    timesheet_for = serializers.DateField(allow_null=True)
    start_datetime = serializers.DateTimeField(allow_null=True)
    end_datetime = serializers.DateTimeField(allow_null=True)


class WorkShiftLegendSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = WorkShiftLegend
        fields = ("id", "legend_text", "legend_color", "shift")

    def get_shift(self, instance):
        return {"id": instance.shift.id, "name": instance.shift.name}

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method == 'GET':
            fields.update({
                "shift": serializers.SerializerMethodField()
            })
        else:
            fields.update({
                "shift": serializers.PrimaryKeyRelatedField(
                    queryset=WorkShift.objects.filter(
                        organization=self.context.get('organization'))
                )
            })
        return fields

    def create(self, validated_data):
        work_shift_legend = validated_data['shift'].work_shift_legend
        work_shift_legend.legend_text = validated_data['legend_text']
        work_shift_legend.legend_color = validated_data['legend_color']
        work_shift_legend.save()
        return DummyObject(**validated_data)
