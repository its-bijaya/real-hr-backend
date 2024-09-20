from django.utils.functional import cached_property
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.attendance.api.v1.permissions import (
    AttendanceOvertimeSettingPermission
)
from irhrs.attendance.constants import REQUESTED, FORWARDED, APPROVED, DECLINED, INVALID_MODE_ACTIONS
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin, ModeFilterQuerysetMixin, GetStatisticsMixin, ListCreateRetrieveViewSetMixin,
    ListCreateRetrieveDestroyViewSetMixin, ListUpdateViewSetMixin, ListRetrieveUpdateViewSetMixin,
    ListRetrieveViewSetMixin)
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.payroll.utils.generate import \
    raise_validation_error_if_payroll_in_generated_or_processing_state
from irhrs.permission.constants.permissions import (
    ATTENDANCE_PERMISSION, ATTENDANCE_CREDIT_HOUR_REQUEST_PERMISSION
)
from ..serializers.credit_hours import CreditHourSettingSerializer, CreditHourRequestSerializer, \
    CreditHourRequestEditSerializer, CreditHourDeleteRequestSerializer, \
    CreditHourRequestOnBehalfSerializer, CreditHourBulkRequestSerializer
from ....constants import CANCELLED
from ....models.credit_hours import CreditHourSetting, CreditHourRequest, CreditHourRequestHistory, \
    CreditHourDeleteRequest, CreditHourDeleteRequestHistory
from ....utils.helpers import validate_appropriate_pre_approval_actor


class CreditHourSettingViewSet(OrganizationMixin, ModelViewSet):
    serializer_class = CreditHourSettingSerializer
    queryset = CreditHourSetting.objects.all()
    lookup_field = 'slug'
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    )
    search_fields = (
        'name',
    )
    ordering_fields = (
        'name', 'modified_at'
    )
    filter_fields = (
        'is_archived',
    )
    ordering = '-modified_at'
    permission_classes = [AttendanceOvertimeSettingPermission]

    def get_queryset(self):
        return self.queryset.filter(organization=self.get_organization())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'organization': self.get_organization()
        })
        return context

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # allow delete if the overtime setting is not assigned to anyone.
        editable = instance.editable
        if not editable:
            return Response(
                data={
                    "message":
                        "Cannot delete Credit Hour Setting as it has been used."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # allow delete if the overtime setting is not assigned to anyone.
        editable = instance.editable
        if not editable:
            return Response(
                data={
                    "message":
                        "Cannot update Credit Hour Setting as it has been used."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)


class CreditHourPreApprovalRequestViewSet(
    ModeFilterQuerysetMixin,
    GetStatisticsMixin,
    OrganizationMixin,
    ListCreateRetrieveDestroyViewSetMixin
):
    """
    Author @raw-V

    Developer's Checklist
        Staff members may have to respond to emergencies or undertake extended field trips.
        The office workload at times can be heavy and may require extra hours.
        Therefore, in order to compensate staff for service beyond what is reasonably expected of a staff member, an award of credit hours should be possible.
        The existence of credit hours is intended to recognize the extra effort of staff and to avoid - burnout as a result of excessively long or burdensome work schedules.
        Only selected employees are entitled to the accrual and usage of credit hours for time worked beyond the x (40 hr/wk)hour work week.
        -> Work timings is defined as per the shift.
        It is incumbent upon the staff person to complete tasks and duties outlined in their scope of work within each x (40 hour work week).
        Below are the policies applicable:
        Staff cannot earn more than x-hours (24 credit hours) cumulatively.
        -> Use the limits `daily_limit`, `weekly_limit` and `monthly_limit` to restrict this behavior.
        Credit hours may be used in combination with annual leave.
        -> Will be done in [HRIS-2032]
        Credit hours’ time accrued are capped at x hours (8 hours) on any given day, regardless of the hours worked.
        -> Use the limits `daily_limit`, `weekly_limit` and `monthly_limit` to restrict this behavior.
        Supervisor approval is required for all credit hours earned and used by filling in the “time-sheet” form. Staff must indicate on this form the time period in which the credit hours were earned and for what purpose.
        -> API: http://normaluser/api/v1/attendance/alpl/credit-hour/pre-approval/
        -> DAT:
        {
            "remarks": "Application for 2 hours credit.",
            "credit_hour_duration": "02:00:00",
            "credit_hour_date": "2020-06-01"
        }
        Credit hours will not be authorized as a result of inefficiency.
        -> Manual Verification.
        Setting for offday/holiday request for credit hour.
        -> Limits are verified accordingly.
        Minimum amount of time(x hours or minutes) in credit hour request
        -> Minimum Request limit verified.

        Summary:
        Request API:
            http://normaluser/api/v1/attendance/alpl/credit-hour/pre-approval/
            Payload:
            {
                "remarks": "Application for 2 hours credit.",
                "credit_hour_duration": "02:00:00",
                "credit_hour_date": "2020-06-01"
            }
        Actions API:
            http://normaluser/api/v1/attendance/alpl/credit-hour/pre-approval/<id>/<action>/?as=<role>
            <action> {approve|cancel|decline|forward}
            <role> {hr|supervisor|blank means self or user}
            {
                "remarks": "Application for 2 hours credit."
            }
        Edit API:
            http://normaluser/api/v1/attendance/alpl/credit-hour/<id>/edit
            Payload:
            {
                "remarks": "Modification for 3 hours credit.",
                "credit_hour_duration": "03:00:00"
            }

        After the Credit Hour is approved, a CreditHourTimeSheetEntry is created.
        The background task for this process is:
            irhrs.attendance.tasks.credit_hours.generate_credit_hours_for_approved_credit_hours
        which filters only approved credit hour requests with leave accounts assigned.

        CreditHourTimeSheetEntry is fed by another task:
            irhrs.attendance.tasks.credit_hours.add_credit_to_leave_account
        which adds CreditHourTimeSheetEntry's approved duration to minutes in Leave Account.

    """
    queryset = CreditHourRequest.objects.exclude(is_deleted=True)
    serializer_class = CreditHourRequestSerializer
    filter_backends = (
        filters.SearchFilter, OrderingFilterMap, FilterMapBackend
    )
    statistics_field = 'status'
    filter_map = {
        'status': 'status',
        'start_date': 'credit_hour_date__gte',
        'end_date': 'credit_hour_date__lte',
    }
    ordering_fields_map = {
        'full_name': ('sender__first_name', 'sender__middle_name', 'sender__last_name'),
        'credit_hour_date': 'credit_hour_date',
        'credit_hour_duration': 'credit_hour_duration',
        'modified_at': 'modified_at'
    }
    search_fields = ('sender__first_name', 'sender__middle_name', 'sender__last_name','sender__username')
    user_definition = 'sender'
    ordering = '-modified_at'
    permission_to_check = [ATTENDANCE_PERMISSION, ATTENDANCE_CREDIT_HOUR_REQUEST_PERMISSION]

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
        ctx['organization'] = self.get_organization()
        if not self.request.query_params.get('as') in ['hr', 'supervisor']:
            ctx['allow_edit'] = self.allow_edit
        ctx['credit_hour_user_id'] = self.request.data.get('user_id', None)
        return ctx

    @action(
        detail=True,
        methods=['POST'],
        url_path=r'(?P<action>(approve|decline|cancel|forward))',
    )
    def perform_action(self, *args, **kwargs):
        remarks = self.request.data.get('remarks')
        credit_hour = self.get_object()
        action_status_map = {
            'approve': APPROVED,
            'decline': DECLINED,
            'forward': FORWARDED,
            'cancel': CANCELLED
        }
        status = action_status_map.get(kwargs.get('action'))
        self.validate_terminal_actions(
            performed=status,
            existing=credit_hour.status,
            mode=self.request.query_params.get('as')
        )
        if not remarks:
            raise ValidationError({
                'remarks': 'Remarks is required.'
            })
        validate_appropriate_pre_approval_actor(
            user=self.request.user,
            pre_approval=credit_hour,
            status=status,
            permissions=self.permission_to_check
        )

        # Develop Serializer Payload.
        ser = CreditHourRequestSerializer(
            instance=credit_hour,
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

    @action(
        detail=False,
        methods=['POST'],
        url_path='request-bulk'
    )
    def request_bulk(self, *args, **kwargs):
        ser = CreditHourBulkRequestSerializer(
            data=self.request.data,
            context=self.get_serializer_context()
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"success": "Credit hours request sent successfully."},
                         status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['POST'],
        url_path='request-on-behalf'
    )
    def request_on_behalf(self, *args, **kwargs):
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=self.get_organization()
        )
        if not self.request.query_params.get('as') == 'hr':
            raise self.permission_denied(self.request, 'Only HR can send this request.')
        if not validate_permissions(
            self.request.user.get_hrs_permissions(self.get_organization()),
            ATTENDANCE_CREDIT_HOUR_REQUEST_PERMISSION
        ):
            raise self.permission_denied(self.request)
        ser = CreditHourRequestOnBehalfSerializer(
            data=self.request.data,
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
        if self.action == 'request_bulk':
            return CreditHourBulkRequestSerializer
        if self.action == 'request_on_behalf':
            return CreditHourRequestOnBehalfSerializer
        if self.action == 'edit':
            return CreditHourRequestEditSerializer
        elif self.action == 'destroy':
            return CreditHourDeleteRequestSerializer
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
        )
        return qs

    def get_object(self):
        obj = super().get_object()
        obj._histories = CreditHourRequestHistory.objects.filter(
            credit_hour=obj,
        ).defer('credit_hour').select_related(
            'action_performed_by',
            'action_performed_by__detail',
            'action_performed_by__detail__organization',
            'action_performed_by__detail__division',
            'action_performed_by__detail__employment_level',
            'action_performed_by__detail__job_title',
        )
        return obj

    def destroy(self, request, *args, **kwargs):
        delete_instance = self.get_object()
        if delete_instance.status != APPROVED:
            raise ValidationError("Can not delete Credit Requests except Approved status.")
        if self.request.user != delete_instance.sender:
            raise ValidationError("Only sender can request for delete.")
        existing = delete_instance.delete_requests.exclude(
            status__in=[DECLINED, CANCELLED]
        ).first()
        if existing:
            raise ValidationError(f"Delete Request exists in {existing.status} state.")
        # if not nested_getattr(self.credit_hour_setting, 'allow_delete'):
        #     raise ValidationError("Delete is not allowed.")
        # Flow remaining.
        # 1. Send status deleted and request to FLS.
        # 2. When supervisor approves the delete status,
        # 3. Revert the gained credit hours
        serializer = CreditHourDeleteRequestSerializer(
            data=self.request.data,
            context={
                **self.get_serializer_context(),
                'credit_request': delete_instance,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Delete Request Sent'}, status=status.HTTP_204_NO_CONTENT)

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
            REQUESTED: (FORWARDED, APPROVED, DECLINED, CANCELLED),
            FORWARDED: (FORWARDED, APPROVED, DECLINED),
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
            nested_getattr(
                self.credit_hour_setting, 'require_prior_approval'
            )
        )

    @property
    def allow_edit(self):
        return nested_getattr(
            self.request.user.attendance_setting,
            'credit_hour_setting.allow_edit_of_pre_approved_credit_hour'
        )

    @cached_property
    def credit_hour_setting(self):
        return nested_getattr(
            self.request.user,
            'attendance_setting.credit_hour_setting'
        )

"""
When Employee request travel attendance with credit hour,
and both are approved then leave balance is updated with 00:00:00 as expected,
but when adjustment is sent for the same day and adjustment was approved,
leave balance was not updated.
"""


class CreditHourDeleteRequestViewSet(
    ModeFilterQuerysetMixin,
    GetStatisticsMixin,
    OrganizationMixin,
    ListRetrieveViewSetMixin
):
    queryset = CreditHourDeleteRequest.objects.all()
    serializer_class = CreditHourDeleteRequestSerializer
    filter_backends = (
        filters.SearchFilter, OrderingFilterMap, FilterMapBackend
    )
    statistics_field = 'status'
    filter_map = {
        'status': 'status',
    }
    ordering_fields_map = {
        'full_name': ('sender__first_name', 'sender__middle_name', 'sender__last_name'),
        'modified_at': 'modified_at'
    }
    search_fields = ('sender__first_name', 'sender__middle_name', 'sender__last_name')
    user_definition = 'sender'
    ordering = '-modified_at'
    permission_to_check = [ATTENDANCE_PERMISSION, ATTENDANCE_CREDIT_HOUR_REQUEST_PERMISSION]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['show_delete_history'] = self.action == 'retrieve'
        return ctx

    @action(
        detail=True,
        methods=['PUT'],
        url_path=r'(?P<action>(approve|decline|cancel|forward))',
    )
    def perform_action(self, *args, **kwargs):
        delete_request = self.get_object()
        action_status_map = {
            'approve': APPROVED,
            'decline': DECLINED,
            'forward': FORWARDED,
            'cancel': CANCELLED
        }
        performed = action_status_map.get(kwargs.get('action'))
        CreditHourPreApprovalRequestViewSet.validate_terminal_actions(
            performed=performed,
            existing=delete_request.status
        )
        validate_appropriate_pre_approval_actor(
            user=self.request.user,
            pre_approval=delete_request,
            status=performed,
            permissions=self.permission_to_check
        )

        # Develop Serializer Payload.
        ser = CreditHourDeleteRequestSerializer(
            instance=delete_request,
            data=self.request.data,
            context={
                'status': performed,
                **self.get_serializer_context()
            },
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

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
        )
        return qs

    def get_object(self):
        obj = super().get_object()
        obj._histories = CreditHourDeleteRequestHistory.objects.filter(
            delete_request=obj,
        ).defer('delete_request').select_related(
            'action_performed_by',
            'action_performed_by__detail',
            'action_performed_by__detail__organization',
            'action_performed_by__detail__division',
            'action_performed_by__detail__employment_level',
            'action_performed_by__detail__job_title',
        )
        return obj

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        ret.data['statistics'] = self.statistics
        return ret
