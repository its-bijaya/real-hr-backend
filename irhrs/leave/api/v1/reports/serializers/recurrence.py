from django.db.models import Count
from rest_framework.fields import ReadOnlyField, SerializerMethodField

from irhrs.core.mixins.serializers import DummySerializer
from irhrs.leave.constants.model_constants import APPROVED
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer


class TypeOccurrenceSerializer(DummySerializer):
    type_id = ReadOnlyField(source='leave_rule__leave_type')
    name = ReadOnlyField(source='leave_rule__leave_type__name')
    requests = ReadOnlyField()


class UserRecurrenceSerializer(UserThinSerializer):
    occurrences = SerializerMethodField()

    class Meta(UserThinSerializer.Meta):
        fields = UserThinSerializer.Meta.fields + ['occurrences']

    def get_occurrences(self, obj):
        filters = self.context.get('filters')

        # filter occurrences if dates are sent
        if filters:
            fil = {
                'start__date__lte': filters.get('end'),
                'end__date__gte': filters.get('start')
            }
        else:
            fil = {}

        active_leave_accounts = self.context.get('active_leave_accounts')

        qs = obj.leave_requests.filter(
            status=APPROVED,
            **fil
        )
        if active_leave_accounts:
            qs = qs.filter(
                leave_account__in=active_leave_accounts
            )
        qs = qs.order_by().values(
            'leave_rule__leave_type__name',
            'leave_rule__leave_type'
        ).annotate(
            requests=Count('leave_rule__leave_type')
        ).order_by('leave_rule__leave_type')

        return TypeOccurrenceSerializer(
            qs, many=True
        ).data
