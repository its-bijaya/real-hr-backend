from rest_framework import serializers

from irhrs.attendance.api.v1.serializers.workshift import WorkShiftSerializer, WorkTimingSerializer
from irhrs.attendance.models import TimeSheet, TimeSheetEntry
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.leave.constants.model_constants import APPROVED, CREDIT_HOUR, TIME_OFF
from irhrs.leave.models.request import LeaveSheet
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class TimeSheetEntriesSerializer(DynamicFieldsModelSerializer):
    entry_method = serializers.ReadOnlyField(source='get_entry_method_display')

    class Meta:
        model = TimeSheetEntry
        fields = (
            'id', 'timestamp', 'entry_method', 'category', 'remark_category', 'remarks',
            'entry_type', 'is_deleted')
        read_only_fields = ('id', 'is_deleted',)


class TimeSheetSerializer(DynamicFieldsModelSerializer):
    entries = serializers.SerializerMethodField()
    work_shift = WorkShiftSerializer(read_only=True, fields=(
        "id",
        "name",
        "start_time_grace",
        "end_time_grace",
    ))
    work_time = WorkTimingSerializer(read_only=True)
    coefficient = serializers.ReadOnlyField(source='get_coefficient_display')

    class Meta:
        model = TimeSheet
        fields = (
            'id', 'work_shift', 'work_time', 'timesheet_for', 'coefficient', 'punch_in',
            'punch_out', 'punch_in_delta', 'hour_off_coefficient',
            'punch_out_delta', 'is_present', 'entries', 'leave_coefficient', 'working_remotely')

    def get_entries(self, obj):
        objects = obj.timesheet_entries.all().order_by('timestamp')
        return TimeSheetEntriesSerializer(instance=objects, many=True, fields=(
            'id', 'timestamp', 'entry_method', 'category', 'remark_category', 'remarks',
            'entry_type', 'is_deleted')).data


class TimeSheetForNoticeboardSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(
        source='timesheet_user',
        fields=['id', 'full_name', 'profile_picture',
                "cover_picture", "is_online", 'is_current', 'organization', ]
    )
    leave_info = serializers.SerializerMethodField()
    # hour_off_info = serializers.ReadOnlyField(source='get_hour_off_coefficient_display')

    class Meta:
        model = TimeSheet
        fields = ['user', 'leave_info']

    @staticmethod
    def get_leave_info(timesheet):
        tags = list()
        date = timesheet.timesheet_for
        user = timesheet.timesheet_user
        leaves = LeaveSheet.objects.filter(
            request__user=user,
            leave_for=date,
            request__status=APPROVED,
        ).exclude(
            request__is_deleted=True
        ).select_related(
            'request',
            'request__leave_rule',
            'request__leave_rule__leave_type'
        ).order_by('start')
        for leave in leaves:
            if leave.request.leave_rule.leave_type.category in [TIME_OFF, CREDIT_HOUR]:
                tags.append(
                    "{} - {}".format(
                        leave.start.astimezone().time(),
                        leave.end.astimezone().time(),
                    )
                )
            else:
                tags.append(leave.request.get_part_of_day_display())
        return tags
