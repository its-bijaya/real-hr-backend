from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from irhrs.attendance.models.timesheet_report_settings import TimeSheetRegistrationReportSettings
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.leave.models import LeaveType

PRIMARY_LEGEND_NAME_CHOICES = [
    'offday',
    'absent',
    'holiday',
    'time_registered',
    'credit_hour_consumed',
]


class HeadersSerializer(DummySerializer):
    report_title = serializers.CharField()
    full_name = serializers.CharField()
    employee_code = serializers.CharField()
    employment_type = serializers.CharField()
    division = serializers.CharField()
    job_title = serializers.CharField()
    branch = serializers.CharField()
    contract_start = serializers.CharField()
    contract_end = serializers.CharField()
    bio_user_id = serializers.CharField()
    proportionate_rate = serializers.CharField()


class PrimaryLegendItemSerializer(DummySerializer):
    letter = serializers.CharField()
    color = serializers.CharField()
    text = serializers.CharField()
    name = serializers.ChoiceField(choices=PRIMARY_LEGEND_NAME_CHOICES)


class LeaveLegendItemSerializer(DummySerializer):
    letter = serializers.CharField()
    color = serializers.CharField()
    text = serializers.CharField()
    leave_type_id = serializers.IntegerField()

    def validate_leave_type_id(self, leave_type_id):
        if not LeaveType.objects.filter(
            id=leave_type_id,
            master_setting__organization=self.context['organization'],
        ).exists():
            raise serializers.ValidationError(_(f"Leave type with pk {leave_type_id}"
                                                f"does not exist"))
        return leave_type_id


class TimeSheetRegistrationReportSettingsSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = TimeSheetRegistrationReportSettings
        fields = (
            'headers',
            'primary_legend',
            'leave_legend',
            'selected_leave_types',
            'approval_required',
            'fiscal_year_category',
            'worked_hours_ceil_limit',
            'created_at',
            'modified_at'
        )

    @staticmethod
    def validate_headers(header_data):
        ser = HeadersSerializer(data=header_data)
        ser.is_valid(raise_exception=True)
        return header_data

    @staticmethod
    def validate_primary_legend(primary_legend):
        ser = PrimaryLegendItemSerializer(data=primary_legend, many=True)
        ser.is_valid(raise_exception=True)
        return primary_legend

    def validate_leave_legend(self, leave_legend):
        ser = LeaveLegendItemSerializer(data=leave_legend, many=True, context=self.context)
        ser.is_valid(raise_exception=True)
        return leave_legend

    def validate_selected_leave_types(self, selected_leave_types):
        if len(selected_leave_types) != 2:
            raise serializers.ValidationError(_("Please select two leave types"))
        if any(
            map(lambda lt: lt.master_setting.organization != self.context['organization'], selected_leave_types)
        ):
            raise serializers.ValidationError(_('Not all leave types are from this organization'))
        return selected_leave_types

    def update(self, instance, validated_data):
        validated_data["organization"] = self.context["organization"]
        selected_leave_types = validated_data.pop('selected_leave_types', [])

        instance = super().update(instance, validated_data)

        instance.selected_leave_types.set(selected_leave_types)
        return instance

