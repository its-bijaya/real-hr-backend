from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from irhrs.core.mixins.serializers import create_read_only_dummy_serializer
from irhrs.core.utils import HumanizedDurationField
from irhrs.leave.constants.model_constants import APPROVED
from irhrs.leave.models import LeaveAccountHistory, LeaveType
from irhrs.leave.models.request import LeaveSheet
from irhrs.users.api.v1.serializers.thin_serializers import UserFieldThinSerializer


class LeaveTypesSerializerMixin:
    """
    Mixin that defines get_leave_types and get_total_leave methods used in SerializerMethodField

    Required in context
    -------------------
        :context leavesheet_filter: filter applied to leavesheet (dict)
        :context end_date_parsed: end date
        :selected_leaves: selected leave ids
    """

    def get_details_for_leave_type(self, user, leave_type_id):

        leavesheet_filter = self.context.get('leavesheet_filter', {})
        end_date = self.context.get('end_date_parsed', timezone.now())

        used = LeaveSheet.objects.filter(
            request__user_id=user.id, request__leave_rule__leave_type_id=leave_type_id
        ).filter(request__is_deleted=False, request__status=APPROVED, **leavesheet_filter).order_by().values(
            'request__user_id').aggregate(total_balance=Sum('balance'))["total_balance"]
        his = LeaveAccountHistory.objects.filter(
            user_id=user.id, account__rule__leave_type_id=leave_type_id
        ).filter(modified_at__date__lte=end_date).order_by('-modified_at').only(
            'new_usable_balance').first()

        # remaining balance at end date
        balance = his.new_usable_balance if his else '-'
        used = '-' if balance == '-' else used or 0.0
        return {
                'leave_type_id': leave_type_id,
                'balance': balance,
                'used': used
            }

    def get_leave_types(self, obj):
        """Leave types (used, balance) details of selected leaves"""
        leave_types = self.context.get('selected_leaves')
        data = []

        for lt in leave_types:
            # used balance at given date range
            lt_data = self.get_details_for_leave_type(user=obj, leave_type_id=lt)
            data.append(lt_data)
        return data

    def get_total_leave(self, obj):
        """total leave consumed in selected duration"""
        leave_types = self.context.get('selected_leaves')
        leavesheet_filter = self.context.get('leavesheet_filter', {})

        return LeaveSheet.objects.filter(
            request__user_id=obj.id,
            request__leave_rule__leave_type_id__in=leave_types
        ).filter(
            request__is_deleted=False,
            request__status=APPROVED,
            **leavesheet_filter
        ).order_by().values(
            'request__user_id'
        ).aggregate(total_balance=Sum('balance'))["total_balance"] or 0.0


class LeaveOnlyReportSerializer(LeaveTypesSerializerMixin,
                                UserFieldThinSerializer,
                                create_read_only_dummy_serializer([
                                    'working_days', 'present_days']), ):
    leave_types = serializers.SerializerMethodField()
    total_leave = serializers.SerializerMethodField()


class AttendanceAndLeaveReportSerializer(LeaveTypesSerializerMixin, UserFieldThinSerializer,
                                         create_read_only_dummy_serializer(['holidays', 'working_days',
                                                                            'present_days', 'off_days',
                                                                            'absent_days', 'total_lost',
                                                                            'confirmed_overtime']), ):
    total_lost = HumanizedDurationField()
    confirmed_overtime = HumanizedDurationField()
    leave_types = serializers.SerializerMethodField()
    total_leave = serializers.SerializerMethodField()


class ExportSerializerBase(LeaveTypesSerializerMixin, UserFieldThinSerializer,):
    pass
