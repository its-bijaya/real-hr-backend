import datetime

from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import get_today
from irhrs.core.utils.filters import get_applicable_filters
from irhrs.leave.constants.model_constants import APPROVED, FULL_DAY, CREDIT_HOUR, TIME_OFF
from irhrs.leave.models import LeaveRequest
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer, UserThumbnailSerializer

HOURLY_CATEGORY = (CREDIT_HOUR, TIME_OFF)


class UserOnLeaveSerializer(UserThinSerializer):
    num_leaves = serializers.SerializerMethodField()
    count_leaves = serializers.SerializerMethodField()
    supervisor = UserThinSerializer(source='first_level_supervisor')
    _aggregate = None

    class Meta(UserThinSerializer.Meta):
        fields = UserThinSerializer.Meta.fields + [
            'num_leaves', 'count_leaves', 'supervisor'
        ]

    def _get_aggregates(self, instance):
        filter_map = {
            'leave_type': 'leave_rule__leave_type__name',
            'division': 'user__detail__division__slug',
            'gender': 'user__detail__gender__iexact',
            'marital_status': 'user__detail__marital_status__iexact',
            'start_date': 'start__date__gte',
            'end_date': 'end__date__lte',
        }

        applicable_filters = get_applicable_filters(
            self.request.query_params,
            filter_map
        )
        qs = instance.leave_requests.filter(
            status=APPROVED,
            **applicable_filters
        ).exclude(
            leave_rule__leave_type__category__in=HOURLY_CATEGORY
        )
        leave_for = self.request.query_params.get('leave_for')
        if leave_for in ['today', 'future']:
            if leave_for == 'today':
                qs = qs.filter(
                    start__date__lte=get_today(),
                    end__date__gte=get_today()
                )
            elif leave_for == 'future':
                # the list of leave before today, till future.
                qs = qs.filter(
                    (
                        Q(start__date__lt=get_today()) &
                        Q(end__date__gt=get_today())
                    ) |
                    (
                        Q(start__date__gt=get_today()) &
                        Q(end__date__gt=get_today())
                    )
                ).distinct()
        self._aggregate = qs.aggregate(
            num_leaves=Coalesce(Sum(Coalesce('balance', 0.0)), 0.0),
            count_leaves=Count('id')
        )
        return self._aggregate

    def get_num_leaves(self, instance):
        return self._get_aggregates(instance).get('num_leaves')

    def get_count_leaves(self, instance):
        return self._get_aggregates(instance).get('count_leaves')


class UserOnLeaveThinSerializer(UserThumbnailSerializer):
    """Serializer to show users on leave with name, part_of_day"""
    leave_type = serializers.ReadOnlyField(allow_null=True)
    part_of_day = serializers.ReadOnlyField(allow_null=True)

    class Meta(UserThumbnailSerializer.Meta):
        fields = UserThinSerializer.Meta.fields + [
            'leave_type', 'part_of_day'
        ]


class FutureOnLeaveSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer()
    range = SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = (
            'user', 'range'
        )

    def get_range(self, instance):
        part_of_day = instance.part_of_day
        display = instance.get_part_of_day_display()
        if part_of_day == FULL_DAY:
            if instance.start.date() == instance.end.date():
                return instance.start.astimezone().strftime(
                    '%Y-%m-%d'
                ) + f' [{display}]'
            return ' to '.join([
                instance.start.astimezone().strftime('%Y-%m-%d'),
                instance.end.astimezone().strftime('%Y-%m-%d'),
            ])
        start = instance.start.astimezone()
        return start.strftime(
            '%Y-%m-%d'
        ) + f' [{display}]'
