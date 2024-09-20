import copy
import functools

from rest_framework import serializers

from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer, \
    UserFieldThinSerializer, UserThickSerializer
from irhrs.attendance.api.v1.serializers.calendar import \
    AttendanceCalenderSerializer


class MonthlyAttendanceReportSerializer(UserThickSerializer):
    total_workday = serializers.IntegerField()
    total_offday = serializers.IntegerField()
    total_holiday = serializers.IntegerField()
    day_breakdown = serializers.SerializerMethodField()

    class Meta(UserThickSerializer.Meta):
        fields = UserThickSerializer.Meta.fields + [
            'total_workday',
            'total_offday',
            'total_holiday',
            'day_breakdown'
        ]

    def get_day_breakdown(self, obj):
        _initial = copy.deepcopy(self.context['report_days'])
        for sheet in obj._timesheets:
            if sheet.timesheet_for.__str__() not in _initial.keys():
                continue
            _initial[sheet.timesheet_for.__str__()]['results'].append(
                AttendanceCalenderSerializer(instance=sheet,
                                             fields=(
                                                 'title',
                                                 'work_time',
                                                 'punch_in',
                                                 'punch_out',
                                                 'coefficient',
                                                 'leave_coefficient'
                                             )).data
            )
        return _initial


class MonthlyAttendanceExportSerializer(UserFieldThinSerializer):
    total_workday = serializers.IntegerField()
    total_offday = serializers.IntegerField()
    total_holiday = serializers.IntegerField()

    def __init__(self, *args, **kwargs):
        # cache function call for day breakdown
        self.day_breakdown = functools.lru_cache(maxsize=2)(self.day_breakdown)
        super().__init__(*args, **kwargs)

    def get_day_breakdown(self, obj):
        _initial = copy.deepcopy(self.context['report_days'])
        for sheet in obj._timesheets:
            if sheet.timesheet_for.__str__() not in _initial.keys():
                continue
            _initial[sheet.timesheet_for.__str__()]['results'].append(
                AttendanceCalenderSerializer(instance=sheet,
                                             fields=('title',)).data
            )
        return _initial

    def day_breakdown(self, obj):
        breakdown = {}
        for date, value in self.get_day_breakdown(obj).items():
            breakdown.update({date: value['results']})
        return breakdown

