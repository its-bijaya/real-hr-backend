from datetime import timedelta

from django.db.models import Sum, Q, Count
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import serializers

from irhrs.attendance.api.v1.serializers.overtime import TimeSheetSerializer
from irhrs.attendance.constants import WORKDAY
from irhrs.attendance.models import TimeSheetEntry, TimeSheet
from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import apply_filters
from irhrs.organization.api.v1.serializers.division import \
    OrganizationDivisionSerializer
from irhrs.organization.models import OrganizationDivision, get_user_model
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer, UserBranchThinSerializer, UserBranchThickSerializer

USER = get_user_model()


class TimeSheetEntryDetailSerializer(DynamicFieldsModelSerializer):
    date = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)
    timesheet = TimeSheetSerializer(read_only=True)

    class Meta:
        model = TimeSheetEntry
        fields = (
            'date', 'user', 'timesheet'
        )

    def get_date(self, instance):
        return instance.timesheet.timesheet_for

    def get_user(self, instance):
        return UserThinSerializer(
            instance.timesheet.timesheet_user
        ).data


class TimeSheetEntryReportSerializer(DynamicFieldsModelSerializer):
    punch_in_late_count = serializers.ReadOnlyField()
    punch_out_early_count = serializers.ReadOnlyField()
    lost_time_late = serializers.ReadOnlyField()
    lost_time_early = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    total_lost_time = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = USER
        fields = (
            'punch_in_late_count', 'punch_out_early_count', 'lost_time_late',
            'lost_time_early', 'total_lost_time', 'user'
        )

    def get_user(self, instance):
        if instance:
            return UserThinSerializer(instance).data
        return

    def get_total_lost_time(self, instance):
        if instance:
            lost_early = abs(instance.lost_time_early or timedelta(0))
            lost_late = abs(instance.lost_time_late or timedelta(0))
            return lost_early + lost_late
        return

    def get_lost_time_early(self, instance):
        return abs(instance.lost_time_early or timedelta(0))


class DepartmentLateInEarlyOutSerializer(DynamicFieldsModelSerializer):
    division = serializers.SerializerMethodField()
    male_count_late = serializers.ReadOnlyField()
    female_count_late = serializers.ReadOnlyField()
    other_count_late = serializers.ReadOnlyField()
    male_count_early = serializers.ReadOnlyField()
    female_count_early = serializers.ReadOnlyField()
    other_count_early = serializers.ReadOnlyField()
    punch_in_late_count = serializers.ReadOnlyField()
    punch_out_early_count = serializers.ReadOnlyField()
    lost_time_late = serializers.ReadOnlyField()
    lost_time_early = serializers.ReadOnlyField()

    class Meta:
        model = TimeSheet
        fields = (
            'division',
            'male_count_early', 'female_count_early', 'other_count_early',
            'male_count_late', 'female_count_late', 'other_count_late',
            'punch_in_late_count', 'punch_out_early_count', 'lost_time_late',
            'lost_time_early'
        )

    def get_division(self, instance):
        return OrganizationDivisionSerializer(
            OrganizationDivision.objects.get(
                pk=instance.get('timesheet_user__detail__division')
            )
        ).data


class DepartmentAbsentReportSerializer(DynamicFieldsModelSerializer):
    division = serializers.SerializerMethodField()
    male_count_absent = serializers.ReadOnlyField()
    female_count_absent = serializers.ReadOnlyField()
    other_count_absent = serializers.ReadOnlyField()
    lost_time = serializers.ReadOnlyField()

    class Meta:
        model = TimeSheet
        fields = (
            'division', 'male_count_absent', 'female_count_absent',
            'other_count_absent', 'lost_time'
        )

    def get_division(self, instance):
        division = OrganizationDivision.objects.filter(
            pk=instance.get('timesheet_user__detail__division')
        ).first()
        return OrganizationDivisionSerializer(
            division
        ).data if division else None


class AttendanceIrregularitiesSerializer(DynamicFieldsModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    results = serializers.SerializerMethodField()

    class Meta:
        model = USER
        fields = (
            'user', 'results'
        )

    @staticmethod
    def get_user(instance):
        return UserBranchThickSerializer(instance).data

    @staticmethod
    def get_results(instance):
        result = {
            'lost_late_in': getattr(instance, 'lost_late_in'),
            'lost_early_out': getattr(instance, 'lost_early_out'),
            'lost_absent': getattr(instance, 'lost_absent'),
            'late_in_count': getattr(instance, 'late_in_count'),
            'early_out_count': getattr(instance, 'early_out_count'),
            'absent_count': getattr(instance, 'absent_count'),
            'unpaid_break_out_count': getattr(instance, 'unpaid_break_out_count'),
            'total_unpaid_hours': getattr(instance, 'total_unpaid_hours'),
            'total_lost': getattr(instance, 'total_lost'),
            'total_worked': getattr(instance, 'total_worked')
        }
        result.update({
            'lost_late_in': abs(
                result.get('lost_late_in') or
                timezone.timedelta(0)
            ),
            'lost_early_out': abs(
                result.get('lost_early_out') or
                timezone.timedelta(0)
            )
        })
        total_lost = result.get('total_lost')
        result.update({
            'total_lost': humanize_interval(total_lost),
            'lost_late_in': humanize_interval(
                result.get('lost_late_in')
            ),
            'lost_early_out': humanize_interval(
                result.get('lost_early_out')
            ),
            'lost_absent': humanize_interval(
                result.get('lost_absent')
            ),
            'total_unpaid_hours': humanize_interval(
                result.get('total_unpaid_hours')
            ),
            'total_worked': humanize_interval(
                result.get('total_worked')
            ),
        })
        return result


class AttendanceIrregularitiesDetailSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(source='timesheet_user')
    total_lost = serializers.SerializerMethodField()

    class Meta:
        model = TimeSheet
        fields = (
            'user', 'timesheet_for', 'total_lost',
            'punch_in', 'punch_out'
        )

    def get_total_lost(self, instance):
        irregularity_type = self.context.get('irregularity_type')
        lost_late = getattr(
            instance, 'lost_late_in', None) or timezone.timedelta(seconds=0)
        lost_early = getattr(
            instance, 'lost_early_out', None) or timezone.timedelta(seconds=0)
        lost_abs = getattr(
            instance, 'lost_absent', None
        ) or timezone.timedelta(seconds=0)
        lost_unpaid_breaks = getattr(
            instance, 'unpaid_break_hours', None
        ) or timezone.timedelta(0)
        if irregularity_type in ['late_in', 'early_out']:
            lost_unpaid_breaks = timezone.timedelta(0)
        return humanize_interval(
            abs(lost_late.total_seconds())
            + abs(lost_early.total_seconds())
            + abs(lost_abs.total_seconds())
            + abs(lost_unpaid_breaks.total_seconds())
        )


class BreakOutSerializer(DynamicFieldsModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = TimeSheetEntry
        fields = (
            'user',
        )

    def get_user(self, instance):
        return UserThinSerializer(
            USER.objects.get(pk=instance.get('user')),
            many=True
        ).data
