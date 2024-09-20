from rest_framework.fields import ReadOnlyField, SerializerMethodField, \
    BooleanField
from rest_framework.serializers import ModelSerializer

from irhrs.attendance.api.v1.serializers.workshift import WorkShiftSerializer, \
    WorkTimingSerializer
from irhrs.attendance.constants import NO_LEAVE, APPROVED, CONFIRMED, BREAK_IN, BREAK_OUT, \
     FULL_LEAVE
from irhrs.attendance.models import TimeSheet
from irhrs.attendance.models.attendance_extraheadings import AttendanceHeadingReportSetting
from irhrs.attendance.utils.attendance import humanize_interval, \
    signed_humanize_interval
from irhrs.attendance.utils.reconciliation import get_attendance_entries_for_given_timesheet, \
    get_late_in_from_timesheet, get_early_out_from_timesheet, get_total_lost_hours_from_timesheet, \
    break_in_out_lost_hour, has_unsynced_attendance_entries
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    DummySerializer
from irhrs.core.utils import nested_getattr, HumanizedDurationField
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer, UserThickSerializer


class IndividualAttendanceReportSerializer(ModelSerializer):
    timesheet_user = UserThickSerializer()
    coefficient = SerializerMethodField()
    duration = ReadOnlyField()

    class Meta:
        model = TimeSheet
        fields = (
            "id",
            "timesheet_user",
            "coefficient",
            "punch_in",
            "punch_out",
            "punch_in_category",
            "punch_out_category",
            "is_present",
            "timesheet_for",
            "duration",
            "punctuality"
        )

    def get_coefficient(self, instance):
        if not instance:
            return None
        if instance.leave_coefficient == NO_LEAVE:
            return instance.get_coefficient_display()
        return instance.get_leave_coefficient_display()


class IndividualAttendanceOverviewSerializer(DynamicFieldsModelSerializer):
    worked_hours = SerializerMethodField(read_only=True, allow_null=True)
    expected_work_hours = SerializerMethodField(read_only=True, allow_null=True)
    overtime = SerializerMethodField()
    punch_in = SerializerMethodField()
    punch_out = SerializerMethodField()
    expected_punch_in = SerializerMethodField()
    expected_punch_out = SerializerMethodField()
    coefficient = ReadOnlyField(source='get_coefficient_display')
    leave_coefficient = ReadOnlyField(source='get_leave_coefficient_display')
    punctuality = SerializerMethodField(allow_null=True)

    class Meta:
        model = TimeSheet
        fields = (
            'timesheet_for',
            'day',
            'punch_in',
            'punch_out',
            'expected_punch_in',
            'expected_punch_out',
            'worked_hours',
            'expected_work_hours',
            'overtime',
            'punctuality',
            'coefficient',
            'leave_coefficient',
            'punctuality'
        )

    @staticmethod
    def get_worked_hours(instance):
        return humanize_interval(instance.worked_hours)

    @staticmethod
    def get_expected_work_hours(instance):
        return humanize_interval(instance.expected_work_hours)

    @staticmethod
    def get_punctuality(instance):
        if instance.punctuality != None:
            return round(instance.punctuality, 2)
        return 'N/A'

    @staticmethod
    def get_overtime(instance):
        ot = nested_getattr(
            instance,
            'overtime.overtime_detail.claimed_overtime'
        )
        return humanize_interval(ot)

    @staticmethod
    def get_punch_in(instance):
        return instance.punch_in.astimezone().strftime(
            '%Y-%m-%d %I:%M:%S %p'
        ) if instance.punch_in else 'N/A'

    @staticmethod
    def get_punch_out(instance):
        return instance.punch_out.astimezone().strftime(
            '%Y-%m-%d %I:%M:%S %p'
        ) if instance.punch_out else 'N/A'

    @staticmethod
    def get_expected_punch_in(instance):
        if instance.leave_coefficient == FULL_LEAVE:
            return 'N/A'
        return instance.expected_punch_in.astimezone().strftime(
            '%Y-%m-%d %I:%M:%S %p'
        ) if instance.expected_punch_in else 'N/A'

    @staticmethod
    def get_expected_punch_out(instance):
        if instance.leave_coefficient == FULL_LEAVE:
            return 'N/A'
        return instance.expected_punch_out.astimezone().strftime(
            '%Y-%m-%d %I:%M:%S %p'
        ) if instance.expected_punch_out else 'N/A'

    @staticmethod
    def get_user(instance):
        return instance.timesheet_user.full_name

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('identify_user'):
            return {
                'user': SerializerMethodField(),
                **fields
            }
        return fields


class IndividualAttendanceOverviewExportSerializer(IndividualAttendanceOverviewSerializer):
    punch_in_time = SerializerMethodField()
    punch_out_time = SerializerMethodField()
    punch_in_date = SerializerMethodField()
    punch_out_date = SerializerMethodField()
    username = ReadOnlyField(source="timesheet_user.username")

    class Meta:
        model = TimeSheet
        fields = (
            'username',
            'timesheet_for',
            'day',
            'punch_in',
            'punch_out',
            'punch_in_time',
            'punch_out_time',
            'punch_in_date',
            'punch_out_date',
            'expected_punch_in',
            'expected_punch_out',
            'worked_hours',
            'expected_work_hours',
            'overtime',
            'punctuality',
            'coefficient',
            'leave_coefficient',
            'punctuality'
        )

    @staticmethod
    def get_punch_in_time(instance):
        return instance.punch_in.astimezone().strftime(
            '%I:%M:%S %p'
        ) if instance.punch_in else 'N/A'

    @staticmethod
    def get_punch_out_time(instance):
        return instance.punch_out.astimezone().strftime(
            '%I:%M:%S %p'
        ) if instance.punch_out else 'N/A'

    @staticmethod
    def get_punch_in_date(instance):
        return instance.punch_in.astimezone().strftime(
            '%Y-%m-%d'
        ) if instance.punch_in else 'N/A'

    @staticmethod
    def get_punch_out_date(instance):
        return instance.punch_out.astimezone().strftime(
            '%Y-%m-%d'
        ) if instance.punch_out else 'N/A'


class OvertimeDetailReportSerializer(IndividualAttendanceOverviewSerializer):
    overtime_worked = SerializerMethodField()
    overtime_claimed = SerializerMethodField()
    status = ReadOnlyField(source='overtime.claim.status')
    punch_in_delta = SerializerMethodField()
    punch_out_delta = SerializerMethodField()

    class Meta:
        model = TimeSheet
        fields = (
            'timesheet_for', 'day', 'punch_in', 'punch_out', 'expected_punch_in',
            'expected_punch_out', 'worked_hours', 'expected_work_hours',
            'overtime_worked', 'overtime_claimed', 'status', 'punch_in_delta',
            'punch_out_delta'
        )

    @staticmethod
    def get_overtime_worked(instance):
        return humanize_interval(instance.overtime_worked)

    @staticmethod
    def get_overtime_claimed(instance):
        return humanize_interval(instance.overtime_claimed)

    @staticmethod
    def get_punch_in_delta(instance):
        if not (instance.expected_punch_in and instance.punch_in) or abs((
                                                                                 instance.expected_punch_in - instance.punch_in
                                                                         ).total_seconds()) < 1:
            return ''
        if instance.expected_punch_in <= instance.punch_in:
            return '-' + humanize_interval(
                instance.expected_punch_in - instance.punch_in
            )
        return '+' + humanize_interval(
            instance.punch_in - instance.expected_punch_in
        )

    @staticmethod
    def get_punch_out_delta(instance):
        if not (instance.expected_punch_out and instance.punch_out) or abs((
                                                                                   instance.expected_punch_out - instance.punch_out
                                                                           ).total_seconds()) < 1:
            return ''
        if instance.expected_punch_out < instance.punch_out:
            return '+' + humanize_interval(
                instance.expected_punch_out - instance.punch_out
            )
        return '-' + humanize_interval(
            instance.punch_out - instance.expected_punch_out
        )


class DailyAttendanceReconciliationSerializer(IndividualAttendanceOverviewSerializer):
    logs = SerializerMethodField()
    timesheet_user = UserThickSerializer()
    employee_code = ReadOnlyField(source='timesheet_user.detail.code')
    late_in = SerializerMethodField()
    early_out = SerializerMethodField()
    total_lost_hours = SerializerMethodField()
    division_name = ReadOnlyField(source='timesheet_user.detail.division.name')
    timesheet_entries = SerializerMethodField()
    punch_in = ReadOnlyField()
    punch_out = ReadOnlyField()

    class Meta:
        model = TimeSheet
        fields = (
            'timesheet_for',
            'timesheet_user',
            'timesheet_entries',
            'day',
            'punch_in',
            'punch_out',
            'expected_punch_in',
            'expected_punch_out',
            'worked_hours',
            'expected_work_hours',
            'overtime',
            'punctuality',
            'coefficient',
            'leave_coefficient',
            'punctuality',
            'logs',
            'employee_code',
            'late_in',
            'early_out',
            'total_lost_hours',
            'division_name',
        )

    @staticmethod
    def get_logs(obj):
        logs = get_attendance_entries_for_given_timesheet(obj)
        return logs if logs else 'N/A'

    @staticmethod
    def get_timesheet_entries(obj):
        timesheet_entries = list(
            obj.timesheet_entries.exclude(
                is_deleted=True
            ).order_by('timestamp').values_list('timestamp__time', flat=True)
        )
        return [entry.replace(microsecond=0) for entry in timesheet_entries]

    @staticmethod
    def get_late_in(obj):
        return get_late_in_from_timesheet(obj, humanized=True)

    @staticmethod
    def get_early_out(obj):
        return get_early_out_from_timesheet(obj, humanized=True)

    @staticmethod
    def get_total_lost_hours(obj):
        return get_total_lost_hours_from_timesheet(obj)


class EmployeeAttendanceInsightSerializer(DailyAttendanceReconciliationSerializer):
    branch_name = ReadOnlyField(source='timesheet_user.detail.branch.name')
    work_shift = WorkShiftSerializer(fields=["id", "name"])
    punch_in_category = ReadOnlyField()
    punch_out_category = ReadOnlyField()
    break_in_count = SerializerMethodField()
    break_out_count = SerializerMethodField()
    approved_overtime = SerializerMethodField()
    confirmed_overtime = SerializerMethodField()
    break_in_out_lost_hours = SerializerMethodField()
    attendance_sync = SerializerMethodField()

    class Meta(DailyAttendanceReconciliationSerializer.Meta):
        fields = DailyAttendanceReconciliationSerializer.Meta.fields + (
            'work_shift', 'branch_name', 'punch_in_category', 'punch_out_category', 'break_in_count',
            'break_out_count', 'break_in_out_lost_hours', 'approved_overtime', 'confirmed_overtime',
            'attendance_sync'
        )

    @staticmethod
    def get_break_in_count(instance):
        return instance.timesheet_entries.filter(entry_type=BREAK_IN).count()

    @staticmethod
    def get_break_out_count(instance):
        return instance.timesheet_entries.filter(entry_type=BREAK_OUT).count()

    @staticmethod
    def get_approved_overtime(instance):
        if hasattr(instance, 'overtime'):
            over_time = instance.overtime
            if hasattr(over_time, 'claim') and over_time.claim.status == APPROVED:
                ot = nested_getattr(
                    instance,
                    'overtime.overtime_detail.claimed_overtime'
                )
                return humanize_interval(ot)
        else:
            return "N/A"

    @staticmethod
    def get_confirmed_overtime(instance):
        if hasattr(instance, 'overtime'):
            over_time = instance.overtime
            if hasattr(over_time, 'claim') and over_time.claim.status == CONFIRMED:
                ot = nested_getattr(
                    instance,
                    'overtime.overtime_detail.claimed_overtime'
                )
                return humanize_interval(ot)
        else:
            return "N/A"

    @staticmethod
    def get_break_in_out_lost_hours(instance):
        return break_in_out_lost_hour(instance)

    @staticmethod
    def get_attendance_sync(instance):
        return not has_unsynced_attendance_entries(instance)

class AttendanceHeadingReportSettingSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = AttendanceHeadingReportSetting
        fields = ('headings',)

    def create(self, validated_data):
        organization = self.context.get('organization')
        report_setting = AttendanceHeadingReportSetting.objects.filter(
            organization=organization
        ).first()

        headings = validated_data.pop('headings')

        if not report_setting:
            report_setting = AttendanceHeadingReportSetting.objects.create(
                organization=organization, headings=headings)
        else:
            report_setting.headings = headings
            report_setting.save()

        return report_setting


class IndividualAttendanceIrregularityReportSerializer(
    DynamicFieldsModelSerializer
):
    absent = BooleanField()
    late_in = BooleanField()
    early_out = BooleanField()
    lost_late_in = HumanizedDurationField()
    lost_early_out = HumanizedDurationField()
    total_lost = HumanizedDurationField()
    worked_hours = HumanizedDurationField()
    work_shift = WorkShiftSerializer(fields=["id", "name"])
    work_time = WorkTimingSerializer(
        fields=["id", "start_time", "end_time", "extends"])

    class Meta:
        model = TimeSheet
        fields = (
            'id',
            "timesheet_for",
            "absent",
            "late_in",
            "early_out",
            "punch_in",
            "punch_out",
            "lost_late_in",
            "lost_early_out",
            "total_lost",
            "work_shift",
            "work_time",
            "unpaid_break_hours",
            "worked_hours"
        )


class ComparativeOvertimeReportSerializer(DummySerializer):
    def get_fields(self):
        from irhrs.core.utils import HumanizedDurationField
        fields = dict(
            user=SerializerMethodField(),
            results=SerializerMethodField()
        )
        fields['total_overtime'] = HumanizedDurationField()
        fields['supervisor'] = UserThinSerializer(
            source='first_level_supervisor'
        )
        return fields

    @staticmethod
    def get_user(instance):
        return UserThinSerializer(instance).data

    def get_results(self, instance):
        fiscal_months = self.context.get('fiscal')
        result = list()
        for month in fiscal_months:
            mth = month.display_name.lower()
            result.append({
                'month_name': mth.title(),
                'worked': humanize_interval(
                    getattr(instance, f'worked_{mth}', None)
                ),
                'difference': signed_humanize_interval(
                    getattr(instance, f'difference_{mth}', None)
                ),
            })
        return result


class ComparativeOvertimeReportExportSerializer(
    ComparativeOvertimeReportSerializer
):
    def get_fields(self):
        from irhrs.core.utils import HumanizedDurationField
        fields = dict(
            user=ReadOnlyField(source='full_name'),
            results=SerializerMethodField()
        )
        fields['total_overtime'] = HumanizedDurationField()
        fields['supervisor'] = ReadOnlyField(
            source='first_level_supervisor.full_name'
        )
        return fields


class AttendanceGeoLocationSerializer(DynamicFieldsModelSerializer):
    timesheet_user = UserThinSerializer()
    punch_in_latitude = ReadOnlyField()
    punch_in_longitude = ReadOnlyField()
    punch_out_latitude = ReadOnlyField()
    punch_out_longitude = ReadOnlyField()
    punch_in_category = ReadOnlyField()
    punch_out_category = ReadOnlyField()

    class Meta:
        model = TimeSheet
        fields = (
            'timesheet_user',
            'punch_in',
            'punch_in_latitude',
            'punch_in_longitude',
            'punch_out',
            'punch_out_latitude',
            'punch_out_longitude',
            'punch_in_category',
            'punch_out_category',
            'timesheet_for'
        )
