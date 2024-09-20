from rest_framework import serializers

from irhrs.attendance.api.v1.serializers.attendance import TimeSheetEntryApprovalSerializer
from irhrs.attendance.constants import DECLINED, APPROVED, REQUESTED, FORWARDED
from irhrs.attendance.models import TimeSheetEntryApproval
from irhrs.attendance.models.approval import TimeSheetApproval
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class TimeSheetEntryApproveSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[APPROVED, DECLINED, FORWARDED])

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        fil = {}
        if request and self.context.get('mode') == 'supervisor':
            fil = {
                'recipient': request.user,
            }

        if self.context.get('timesheet'):
            fil['timesheet_approval'] = self.context.get('timesheet')

        fields['timesheet'] = serializers.PrimaryKeyRelatedField(
            queryset=TimeSheetEntryApproval.objects.filter(
                status__in=[REQUESTED, FORWARDED],
                **fil
            ),
            many=True
        )
        return fields


class TimeSheetApprovalSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(
        source='timesheet.timesheet_user',
        fields=('id', 'full_name', 'profile_picture', 'is_current', 'organization',)
    )
    for_date = serializers.DateField(source='timesheet.timesheet_for')
    entries = serializers.SerializerMethodField()

    class Meta:
        model = TimeSheetApproval
        fields = 'id', 'status', 'user', 'for_date', 'entries', 'created_at'

    def get_entries(self, obj):
        request = self.context.get('request', None)
        fil = {}
        if request and self.context.get('mode') == 'supervisor':
            fil = {'recipient': request.user}
        return TimeSheetEntryApprovalSerializer(
            obj.timesheet_entry_approval.filter(**fil),
            many=True
        ).data
