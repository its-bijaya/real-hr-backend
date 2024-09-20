from django.contrib.auth import get_user_model
from django.db.models import Sum, F, Q, Subquery
from django.db.models.functions import Coalesce
from rest_framework import serializers

from irhrs.leave.api.v1.serializers.settings import LeaveTypeSerializer
from irhrs.leave.models import LeaveRule
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

User = get_user_model()


class LeaveIrregularityReportSerializer(serializers.Serializer):
    leave_type = serializers.SerializerMethodField()
    num_leaves = serializers.ReadOnlyField()
    limit_exceeded = serializers.ReadOnlyField()
    limit = serializers.ReadOnlyField()

    def get_leave_type(self, instance):
        return LeaveTypeSerializer(
            fields=['name', 'category'],
            instance=instance.rule.leave_type,
            allow_null=True
        ).data


class IndividualLeaveIrregularitiesSerializer(UserThinSerializer):
    user = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    class Meta(UserThinSerializer.Meta):
        fields = (
            'user', 'result'
        )

    def get_result(self, instance, count_only=False):
        lim_type = self.context.get('lim_type')
        st = self.context.get('start_period')
        ed = self.context.get('end_period')

        # filter applicable leave rules only.

        irregulars = LeaveRule.objects.filter(
            leave_type__master_setting=self.context.get('active_setting'),
            irregularity_report=True,
            leave_irregularity__isnull=False
        ).only('id')

        results = instance.leave_accounts.filter(
            rule_id__in=Subquery(irregulars)
        ).annotate(
            num_leaves=Sum(
                'leave_requests__sheets__balance',
                filter=Q(
                    leave_requests__sheets__leave_for__range=(st, ed)
                )
            ),
            limit=F(f'rule__leave_irregularity__{lim_type}')
        ).annotate(
            limit_exceeded=Coalesce(
                F('num_leaves') - F('limit'),
                0
            )
        ).filter(
            limit_exceeded__gt=0
        )
        if count_only:
            return results.aggregate(r=Sum('limit_exceeded')).get('r')
        ret = LeaveIrregularityReportSerializer(results, many=True).data
        return ret

    def get_user(self, instance):
        return UserThinSerializer(instance).data


class LeaveIrregularitiesOverviewSerializer(
    IndividualLeaveIrregularitiesSerializer
):
    result = serializers.SerializerMethodField()

    def get_result(self, instance, count_only=False):
        return super().get_result(instance, count_only=True)


class MostLeavesReportSerializer(IndividualLeaveIrregularitiesSerializer):
    result = serializers.ReadOnlyField(source='num_leaves')
