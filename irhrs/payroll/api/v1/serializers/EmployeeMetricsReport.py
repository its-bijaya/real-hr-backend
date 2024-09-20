from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField

from irhrs.attendance.constants import OFFDAY
from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.attendance.utils.payroll import get_working_days_from_organization_calendar, \
    get_worked_days, get_absent_days, get_timesheet_penalty_days, get_work_duration
from irhrs.leave.utils.payroll import get_all_leave_days, get_leave_days, get_unpaid_leave_days, \
    get_paid_leave_days
from irhrs.organization.api.v1.serializers.branch import OrganizationBranchSerializer
from irhrs.organization.models import Holiday
from irhrs.payroll.models.EmployeeMetricsSetting import EmployeeMetricHeadingReportSetting
from irhrs.payroll.utils.helpers import get_days_to_be_paid
from irhrs.users.api.v1.serializers.thin_serializers import UserThickSerializer

User = get_user_model()


class EmployeeMetricsReportSerializer(UserThickSerializer):
    branch = OrganizationBranchSerializer(
        fields=['name', 'slug'],
        source='detail.branch',
        read_only=True
    )
    employment_type = ReadOnlyField(
        source='detail.employment_status.title'
    )
    total_days = serializers.SerializerMethodField()
    working_days = serializers.SerializerMethodField()
    worked_days = serializers.SerializerMethodField()
    absent_days = serializers.SerializerMethodField()
    leave_days = serializers.SerializerMethodField()
    leave_days_on_workdays = serializers.SerializerMethodField()
    unpaid_leave_days = serializers.SerializerMethodField()
    paid_days = serializers.SerializerMethodField()
    days_deduction_from_penalty = serializers.SerializerMethodField()
    holiday_count = serializers.SerializerMethodField()
    offday_count = serializers.SerializerMethodField()
    leave_paid_days = serializers.SerializerMethodField()
    worked_on_offday_holiday = serializers.SerializerMethodField()
    worked_hour = serializers.SerializerMethodField()
    total_claimed = serializers.SerializerMethodField()


    class Meta:
        model = User
        fields = UserThickSerializer.Meta.fields + ['working_days', 'branch', 'employment_type',
                                                    'total_days',  'worked_days', 'absent_days', 'leave_days',
                                                    'leave_days_on_workdays', 'unpaid_leave_days',
                                                    'paid_days', 'days_deduction_from_penalty',
                                                    'holiday_count', 'offday_count', 'leave_paid_days',
                                                    'worked_on_offday_holiday', 'worked_hour',
                                                    'total_claimed'
                                                    ]


    @property
    def from_date(self):
        return self.context.get('from_date')

    @property
    def to_date(self):
        return self.context.get('to_date')

    @property
    def include_holiday_days(self):
        return self.context.get('include_holiday_offday')

    def get_working_days(self, obj):
        return get_working_days_from_organization_calendar(
            obj,
            self.from_date,
            self.to_date,
            include_holiday_offday=self.include_holiday_days
        )

    def get_worked_days(self, obj):
        return get_worked_days(
            obj, self.from_date, self.to_date,
            include_non_working_days=self.include_holiday_days
        )

    def get_absent_days(self, obj):
        return get_absent_days(obj, self.from_date, self.to_date)

    def get_leave_days(self, obj):
        return get_all_leave_days(obj, self.from_date,
                                  self.to_date)

    def get_leave_days_on_workdays(self, obj):
        return get_leave_days(obj, self.from_date,
                              self.to_date, is_workday=True)

    def get_unpaid_leave_days(self, obj):
        return get_unpaid_leave_days(obj, self.from_date,
                                     self.to_date)

    def get_leave_paid_days(self, obj):
        return get_paid_leave_days(obj, self.from_date, self.to_date)

    def get_days_deduction_from_penalty(self, obj):
        return get_timesheet_penalty_days(obj, self.from_date, self.to_date)

    def get_paid_days(self, obj):

        return get_days_to_be_paid(
            obj,
            self.from_date,
            self.to_date,
            count_offday_holiday_as_worked=self.include_holiday_days
        )

    def get_holiday_count(self, obj):
        return Holiday.objects.filter(
            Q(organization__isnull=True) |
            Q(organization=self.context.get('organization'))).filter(
                                                    date__range=[self.from_date, self.to_date]
                                                            ).count()

    def get_offday_count(self, obj):
        return obj.timesheets.filter(
            timesheet_for__gte=self.from_date,
            timesheet_for__lte=self.to_date,
            coefficient=OFFDAY
        ).count()

    def get_worked_on_offday_holiday(self, obj):
        total_worked_days = get_worked_days(obj, self.from_date, self.to_date,
                                            include_non_working_days=True,
                                            count_offday_holiday_as_worked=True)
        worked_days_excluding_holidays_offdays = get_worked_days(obj, self.from_date, self.to_date)
        return total_worked_days - worked_days_excluding_holidays_offdays

    def get_worked_hour(self, obj):
        return humanize_interval(get_work_duration(
            obj, self.from_date,
            self.to_date
        ).total_seconds())

    def get_total_days(self, obj):
        from_date = datetime.strptime(self.from_date, '%Y-%m-%d').date()
        to_date = datetime.strptime(self.to_date, '%Y-%m-%d').date()
        return (to_date-from_date).days + 1

    @staticmethod
    def get_total_claimed(obj):
        if obj.total_confirmed:
            return humanize_interval(obj.total_confirmed.total_seconds())
        else:
            return '00:00:00'


class EmployeeMetricHeadingReportSettingSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployeeMetricHeadingReportSetting
        fields = ('headings',)

    def create(self, validated_data):
        organization = self.context.get('organization')
        report_setting = EmployeeMetricHeadingReportSetting.objects.filter(
            organization=organization
        ).first()
        if not report_setting:
            headings = validated_data.pop('headings')
            report_setting = EmployeeMetricHeadingReportSetting.objects.create(
                organization=organization, headings=headings)
            return report_setting
        return self.update(report_setting, validated_data)

    def update(self, instance, validated_data):
        headings = validated_data.pop('headings')
        instance.headings = headings
        instance.save()
        return instance
