from django_q.tasks import async_task
from rest_framework import serializers

from irhrs.attendance.api.v1.serializers.adjustment import \
    AttendanceAdjustmentDetailSerializer
from irhrs.attendance.constants import REQUESTED, TIME_OFF, WORKDAY, NO_LEAVE, OFFDAY, \
    HOLIDAY
from irhrs.attendance.tasks.timesheets import timesheet_regenerate_broker
from irhrs.core.utils.common import DummyObject
from irhrs.core.validators import validate_past_date
from irhrs.leave.api.v1.serializers.leave_request import LeaveSheetSerializer
from irhrs.leave.utils.leave_request import leave_request_for_timesheet
from .timesheet import TimeSheetSerializer


class AttendanceCalenderSerializer(TimeSheetSerializer):
    start = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    adjustments = serializers.SerializerMethodField()
    className = serializers.SerializerMethodField()
    leave_details = serializers.SerializerMethodField()

    class Meta(TimeSheetSerializer.Meta):
        fields = TimeSheetSerializer.Meta.fields + (
            'start', 'title', 'adjustments', 'className', 'leave_details'
        )

    def get_leave_details(self, timesheet):
        leaves_that_day = leave_request_for_timesheet(
            timesheet, requested_only=False
        )
        return LeaveSheetSerializer(
            leaves_that_day, many=True,
            context=self.context
        ).data

    def get_title(self, obj):
        if hasattr(obj, 'adj_requests'):
            adj_exists = bool(obj.adj_requests)
        else:
            adj_exists = obj.adjustment_requests.exists()
        adjustment_flag = '[A]'
        title = obj.get_pretty_name

        if obj.leave_coefficient == NO_LEAVE and obj.hour_off_coefficient:
            leave_data = self.get_leave_details(obj)[:2]
            title = ", ".join(leave.get("leave_type", "") for leave in leave_data)
            if len(leave_data) > 2:
                title += "..."

        if adj_exists:
            title = adjustment_flag + ' ' + title
        if leave_request_for_timesheet(obj):
            title = '[LR] ' + title
        return title

    @staticmethod
    def get_className(obj):
        def _get_class_color(obj):
            if obj.leave_coefficient != NO_LEAVE:
                return 'purple'
            elif obj.coefficient == WORKDAY:
                if 'absent' in obj.get_pretty_name.lower():
                    return 'red'
                if 'n/a' in obj.get_pretty_name.lower() or 'missing' in obj.get_pretty_name.lower():
                    return 'red lighten-2'
                return 'green'
            elif obj.coefficient == OFFDAY:
                return 'grey'
            elif obj.coefficient == HOLIDAY:
                return 'blue'

        color = _get_class_color(obj)
        _base_class = 'pa-1 px-2 text-xs-center font-weight-bold '
        return _base_class + color if color else _base_class + ' orange'

    @staticmethod
    def get_adjustments(obj):
        if hasattr(obj, 'adj_requests'):
            adj_data = obj.adj_requests
        else:
            adj_data = obj.adjustment_requests.filter(status=REQUESTED)
        _fields = ('id',
                   'timestamp',
                   'category',
                   'action',
                   'description',
                   'created_at',)
        return AttendanceAdjustmentDetailSerializer(instance=adj_data,
                                                    many=True,
                                                    fields=_fields).data

    @staticmethod
    def get_start(obj):
        if obj.work_time:
            return str(obj.timesheet_for) + "T" + str(obj.work_time.start_time)
        return str(obj.timesheet_for) + "T00:00:00"


class AttendanceCalendarRegenerateSerializer(serializers.Serializer):
    start_date = serializers.DateField(
        required=True,
        allow_null=False,
        validators=[validate_past_date]
    )
    end_date = serializers.DateField(
        required=True,
        allow_null=False,
    )

    def validate(self, attrs):
        start_date = attrs['start_date']
        end_date = attrs['end_date']
        if start_date > end_date:
            raise serializers.ValidationError({
                'start_date': 'The end date must be greater than start date.'
            })
        return super().validate(attrs)

    def create(self, validated_data):
        user = self.context.get('user')
        async_task(
            timesheet_regenerate_broker,
            user,
            validated_data['start_date'],
            validated_data['end_date'],
            notify='true'
        )
        return DummyObject(**validated_data)

    def update(self, instance, validated_data): ...
