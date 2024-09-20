from datetime import datetime
from django.conf import settings
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import (
    GetStatisticsMixin, ModeFilterQuerysetMixin, OrganizationMixin, ListCreateRetrieveUpdateViewSetMixin,
    ListCreateRetrieveViewSetMixin)
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.permission.constants.permissions import ATTENDANCE_OVERTIME_CLAIM_PERMISSION, ATTENDANCE_PERMISSION
from ..serializers.pre_approval import PreApprovalOvertimeSerializer, PreApprovalOvertimeEditSerializer
from ....constants import APPROVED, DECLINED, FORWARDED, REQUESTED, CONFIRMED, CANCELLED, INVALID_MODE_ACTIONS
from ....models.pre_approval import PreApprovalOvertime, PreApprovalOvertimeHistory
from ....tasks.pre_approval import is_pre_approved_overtime_editable
from ....utils.helpers import validate_appropriate_pre_approval_actor
from irhrs.attendance.utils.helpers import get_week_range
from ....utils.overtime_utils import get_pre_approval_overtime_sum
from irhrs.organization.models import FiscalYear

ALLOW_CANCEL = True
REQUIRE_CONFIRM = getattr(settings, 'REQUIRE_PRE_APPROVAL_CONFIRMATION', False)
PRE_APPROVAL_ACTIONS = ['approve', 'decline', 'forward']
if ALLOW_CANCEL:
    PRE_APPROVAL_ACTIONS.append('cancel')
if REQUIRE_CONFIRM:
    PRE_APPROVAL_ACTIONS.append('confirm')
PRE_APPROVAL_ACTIONS_URL = r'(?P<action>({}))'.format(
    '|'.join(PRE_APPROVAL_ACTIONS)
)


class PreApprovalOvertimeViewSet(
    ModeFilterQuerysetMixin,
    GetStatisticsMixin,
    OrganizationMixin,
    ListCreateRetrieveViewSetMixin
):
    """
    Author @raw-V

    Please find the backend API at /api/v1/attendance/alpl/overtime/pre-approval/:
    {
      "remarks": "Request for 2 hours for",
      "overtime_duration": "02:00:00",
      "overtime_date": "2020-05-05"
    }
    Perform actions:

    /api/v1/attendance/alpl/overtime/pre-approval/1/approve/

    All available actions:

    forward
    approve
    decline

    Pre Approval Overtime may be editable once Approved, (defined through settings).
    In case of edit,
    API: /api/v1/attendance/alpl/overtime/pre-approval/1/
    {

       "overtime_duration": "05:00:00",
      "remarks": "edited to 5 hours"
    }

    """
    queryset = PreApprovalOvertime.objects.all()
    serializer_class = PreApprovalOvertimeSerializer
    filter_backends = (
        filters.SearchFilter, OrderingFilterMap, FilterMapBackend
    )
    statistics_field = 'status'
    filter_map = {
        'status': 'status',
        'start_date': 'overtime_date__gte',
        'end_date': 'overtime_date__lte',
    }
    ordering_fields_map = {
        'full_name': ('sender__first_name', 'sender__middle_name', 'sender__last_name'),
        'overtime_date': 'overtime_date',
        'overtime_duration': 'overtime_duration',
        'created_at': 'created_at',
        'modified_at': 'modified_at',
    }
    search_fields = ('sender__first_name', 'sender__middle_name', 'sender__last_name','sender__username')
    # For ModeFilterQuerysetMixin
    user_definition = 'sender'
    permission_to_check = [ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION]

    def get_serializer_context(self):
        """
        Sets the following parameters required for serializer.

        :sender: Whom does this Pre Approval belong to.
        If Request On Behalf is implemented, be sure to set `sender` appropriately.
        """
        ctx = super().get_serializer_context()
        ctx['sender'] = self.request.user
        ctx['show_history'] = self.action == 'retrieve'
        ctx['allow_request'] = self.allow_request
        if not self.request.query_params.get('as') in ['hr', 'supervisor']:
            ctx['allow_edit'] = self.allow_edit
        return ctx

    @action(
        detail=True,
        methods=['POST'],
        url_path=PRE_APPROVAL_ACTIONS_URL,
    )
    def perform_action(self, *args, **kwargs):
        remarks = self.request.data.get('remarks')
        pre_approval = self.get_object()
        action_status_map = {
            'approve': APPROVED,
            'decline': DECLINED,
            'forward': FORWARDED,
            'confirm': CONFIRMED,
            'cancel': CANCELLED
        }
        status = action_status_map.get(kwargs.get('action'))
        self.validate_terminal_actions(
            performed=status,
            existing=pre_approval.status,
            mode=self.request.query_params.get('as')
        )
        if not remarks:
            raise ValidationError({
                'remarks': 'Remarks is required.'
            })
        if len(remarks) > 255:
            raise ValidationError({
                'remarks': 'Remarks must be less than 255 characters.'
            })
        validate_appropriate_pre_approval_actor(
            user=self.request.user,
            pre_approval=pre_approval,
            status=status,
            permissions=self.permission_to_check
        )

        # Develop Serializer Payload.
        ser = PreApprovalOvertimeSerializer(
            instance=pre_approval,
            data=dict(),
            context={
                'action': True,
                'status': status,
                'remarks': remarks,
                **self.get_serializer_context()
            },
            fields=['action_remarks']
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    @action(
        detail=True,
        methods=['POST'],
    )
    def edit(self, *args, **kwargs):
        if self.request.query_params.get('as') in ['hr', 'supervisor']:
            raise ValidationError('Only sender can edit the request.')
        ser = self.get_serializer(
            data=self.request.data,
            instance=self.get_object(),
            context=self.get_serializer_context()
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'perform_action':
            kwargs['fields'] = ['remarks']
        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'edit':
            return PreApprovalOvertimeEditSerializer
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        ret.data.update({
            'statistics': self.statistics
        })
        # Test mode if its supervisor or HR. Because, allow_request doesn't make sense then.
        if not self.request.query_params.get('as') in ['hr', 'supervisor']:
            ret.data.update({
                'allow_request': self.allow_request,
            })
        return ret

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('as') == 'supervisor':
            qs = qs.filter(recipient=self.request.user)
        qs = qs.select_related(
            'sender',
            'sender__detail',
            'sender__detail__organization',
            'sender__detail__division',
            'sender__detail__employment_status',
            'sender__detail__employment_level',
            'sender__detail__job_title',
            'sender__detail__branch',
            'recipient',
            'recipient__detail',
            'recipient__detail__organization',
            'recipient__detail__division',
            'recipient__detail__employment_status',
            'recipient__detail__employment_level',
            'recipient__detail__job_title',
            'recipient__detail__branch',
            'overtime_entry__overtime_settings'
        )
        return qs

    def get_object(self):
        obj = super().get_object()
        obj._histories = PreApprovalOvertimeHistory.objects.filter(
            pre_approval=obj,
        ).defer('pre_approval').select_related(
            'action_performed_by',
            'action_performed_by__detail',
            'action_performed_by__detail__organization',
            'action_performed_by__detail__division',
            'action_performed_by__detail__employment_level',
            'action_performed_by__detail__job_title',
            'action_performed_to',
            'action_performed_to__detail',
            'action_performed_to__detail__organization',
            'action_performed_to__detail__division',
            'action_performed_to__detail__employment_level',
            'action_performed_to__detail__job_title',
        )
        return obj

    @staticmethod
    def validate_terminal_actions(performed, existing, mode='user') -> None:
        """
        Terminal Actions is defined as statuses that can not be acted upon further.
        i.e. if in forwarded state, only Approve, forward, decline, confirm is possible
        :param performed: Action Performed i.e. Approved, Confirmed, Declined, etc.
        :param existing: The request's current state. i.e. Requested, Forwarded, etc.
        :param mode: The mode accessing this API. defaults to user
        """
        allowed_actions = {
            REQUESTED: (FORWARDED, APPROVED, DECLINED, CONFIRMED, CANCELLED),
            FORWARDED: (FORWARDED, APPROVED, DECLINED, CONFIRMED),
            APPROVED: (DECLINED, CONFIRMED),
        }
        if performed not in allowed_actions.get(existing, []):
            raise ValidationError(
                f"Can not perform {performed} for {existing} requests."
            )
        invalid_defined = INVALID_MODE_ACTIONS.get(performed)
        if invalid_defined and mode in invalid_defined:
            raise ValidationError(
                f"Can not perform {performed} as {mode}."
            )

    @property
    def allow_request(self):
        return bool(
            getattr(
                self.request.user.attendance_setting.overtime_setting,
                'require_prior_approval', None
            )
        )

    @property
    def allow_edit(self):
        return nested_getattr(
            self.request.user.attendance_setting,
            'overtime_setting.require_prior_approval'
        )

    @action(
        detail=False,
        methods=['GET'],
        url_path='remaining-limit'
    )
    def get_remaining_ot_limit(self, request, *args, **kwargs):
        ot_request_for = self.request.query_params.get('request_for')
        user = request.user
        daily_sum = get_pre_approval_overtime_sum(user, ot_request_for, ot_request_for)
        ot_date = datetime.strptime(ot_request_for, '%Y-%m-%d').date()
        start_week_range, end_week_range = get_week_range(ot_date)
        month_start, month_end = self.get_fiscal_month_for_date(ot_date, user.detail.organization)
        weekly_sum = get_pre_approval_overtime_sum(user, end_week_range, start_week_range)
        monthly_sum = get_pre_approval_overtime_sum(user, month_end, month_start)

        ot_setting = nested_getattr(self.request.user, 'attendance_setting.overtime_setting')

        limit_detail = {
            'daily_ot_limit': None,
            'weekly_ot_limit': None,
            'monthly_ot_limit': None
        }

        if ot_setting.daily_overtime_limit:
            limit_detail['daily_ot_limit'] = self.calculated_ot_limit(
                ot_setting.daily_overtime_limit, daily_sum
            )

        if ot_setting.weekly_overtime_limit:
            limit_detail['weekly_ot_limit'] = self.calculated_ot_limit(
                ot_setting.weekly_overtime_limit, weekly_sum
            )

        if ot_setting.monthly_overtime_limit:
            limit_detail['monthly_ot_limit'] = self.calculated_ot_limit(
                ot_setting.monthly_overtime_limit, monthly_sum
            )

        return Response(limit_detail)

    @staticmethod
    def calculated_ot_limit(ot_limit_type, duration):
        actual_duration = int((duration/60).total_seconds())
        if actual_duration > ot_limit_type:
            return
        return ot_limit_type - actual_duration
    
    @staticmethod
    def get_fiscal_month_for_date(date, organization):
        fy = FiscalYear.objects.current(organization=organization)
        if fy:
            fm = fy.fiscal_months.filter(
                start_at__lte=date,
                end_at__gte=date,
            ).order_by(
                'start_at'
            ).values_list('start_at', 'end_at')
            if fm:
                return fm[0]
        raise ValidationError(
            "Fiscal Year is not defined."
        )
