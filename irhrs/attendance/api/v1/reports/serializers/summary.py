from irhrs.attendance.api.v1.serializers.workshift import WorkShiftSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class UserAttendanceSummarySerializer(UserThinSerializer):
    work_shift = WorkShiftSerializer(fields=["id", "name"], source="attendance_setting.work_shift", read_only=True)

    class Meta(UserThinSerializer.Meta):
        fields = UserThinSerializer.Meta.fields + ['work_shift']
