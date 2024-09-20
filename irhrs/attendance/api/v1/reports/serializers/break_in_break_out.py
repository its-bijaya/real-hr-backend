from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from irhrs.attendance.constants import BREAK_IN, BREAK_OUT, OTHERS, PUNCH_OUT
from irhrs.attendance.models import TimeSheet, TimeSheetEntry
from irhrs.attendance.utils.break_in_break_out import get_pair, get_total_lost
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import apply_filters, get_today
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import UserDetail


class BreakInBreakOutDetailReportSerializer(DynamicFieldsModelSerializer):
    pairs = serializers.SerializerMethodField()

    class Meta:
        model = TimeSheet
        fields = (
            'pairs',
        )

    @staticmethod
    def _get_pair(qs):
        # There is get_pair util. Use that function instead of this staticmethod.
        # TODO @Ravi: remove this method
        return get_pair(qs)

    def get_pairs(self, timesheet):
        # get pairs
        breakout_category = self.context.get('breakout_category')
        results = []

        qs = TimeSheetEntry.objects.filter(
            timesheet__timesheet_user=timesheet.timesheet_user,
            timesheet__timesheet_for=timesheet.timesheet_for,
            is_deleted=False
        ).filter(
            entry_type__in=[BREAK_IN, BREAK_OUT, PUNCH_OUT]
        )
        if breakout_category:
            qs = qs.filter(remark_category=breakout_category)
        pairs = self._get_pair(qs)
        for start, end in pairs:
            break_out = start.timestamp
            break_in = end.timestamp if end else None

            # since PUNCH_OUT is included, ignore last not pairing entry
            if not break_in:
                continue

            lost = (break_in - break_out) if end else timezone.timedelta(0)
            results.append({
                'category': start.remark_category or OTHERS,
                'date': start.timesheet.timesheet_for,
                'break_in_latitude': start.latitude,
                'break_in_longitude': start.longitude,
                'break_out_latitude': end.latitude,
                'break_out_longitude': end.longitude,
                'break_in': break_in.astimezone() if break_in else break_in,
                'break_out_remark': start.remarks,
                'break_in_remark': end.remarks if end else None,
                'break_out': break_out.astimezone() if break_out else break_out,
                'lost': lost.total_seconds() / 60
            })
        return results


class BreakInBreakOutReportSerializer(DynamicFieldsModelSerializer):
    user = serializers.SerializerMethodField()
    break_in_out_count = serializers.ReadOnlyField()
    total_lost = serializers.SerializerMethodField()

    class Meta:
        model = UserDetail
        fields = (
            'user', 'break_in_out_count', 'total_lost'
        )

    def get_user(self, instance):
        return UserThinSerializer(instance).data

    def get_total_lost(self, instance):
        return get_total_lost(self.queryset(instance))

    def queryset(self, instance):
        return apply_filters(
            self.request.query_params,
            {
                'start_date': 'timesheet__timesheet_for__gte',
                'end_date': 'timesheet__timesheet_for__lte',
                'remark_category': 'remark_category'
            },
            TimeSheetEntry.objects.select_related(
                'timesheet',
            ).filter(
                is_deleted=False,
                timesheet__timesheet_user=instance,
            ).filter(
                Q(
                    entry_type__in=[BREAK_IN, BREAK_OUT, PUNCH_OUT]
                )
            )
        )


class BreakOutRawReportSerializer(DynamicFieldsModelSerializer):
    user = serializers.SerializerMethodField()
    break_in_out_count = serializers.ReadOnlyField()
    total_lost = serializers.ReadOnlyField()

    class Meta:
        model = UserDetail
        fields = (
            'user', 'break_in_out_count', 'total_lost'
        )

    def get_user(self, instance):
        return UserThinSerializer(instance).data
