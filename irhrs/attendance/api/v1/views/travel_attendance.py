from copy import deepcopy

from django.db.models import Count, Q
from django.utils.functional import cached_property
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ModelViewSet

from irhrs.attendance.api.v1.serializers.travel_attendance import \
    TravelAttendanceSettingSerializer, \
    TravelAttendanceRequestSerializer, TravelAttendanceDaysSerializer, \
    TravelAttendanceDeleteRequestSerializer, TravelAttendanceWithCreditRequestSerializer, \
    TravelAttendanceOnBehalfSerializer
from irhrs.attendance.constants import APPROVED, DECLINED, CANCELLED, FORWARDED, REQUESTED
from irhrs.attendance.models.travel_attendance import TravelAttendanceRequest, \
    TravelAttendanceDays, \
    TravelAttendanceDeleteRequest
from irhrs.attendance.utils.helpers import get_appropriate_recipient, get_authority
from irhrs.core.mixins.viewset_mixins import RetrieveUpdateViewSetMixin, OrganizationMixin, \
    OrganizationCommonsMixin, GetStatisticsMixin, \
    ListCreateRetrieveViewSetMixin, ModeFilterQuerysetMixin
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, NullsAlwaysLastOrderingFilter
from irhrs.organization.models import Organization
from irhrs.permission.constants.permissions.attendance import ATTENDANCE_TRAVEL_PERMISSION, \
    ATTENDANCE_TRAVEL_SETTING_PERMISSION
from irhrs.permission.permission_classes import permission_factory
from irhrs.users.models import UserDetail
from ....models import TravelAttendanceSetting


class TravelAttendanceSettingViewSet(OrganizationCommonsMixin, OrganizationMixin,
                                     RetrieveUpdateViewSetMixin):
    """
    There is only one attendance setting per organization.
    """
    queryset = TravelAttendanceSetting.objects.all()
    serializer_class = TravelAttendanceSettingSerializer
    permission_classes = [
        permission_factory.build_permission(
            'TravelAttendanceSettingPermission',
            limit_write_to=[ATTENDANCE_TRAVEL_SETTING_PERMISSION]
        )
    ]

    def get_object(self):
        return self.get_queryset().first()


class TravelAttendanceRequestViewSet(
    ModeFilterQuerysetMixin,
    GetStatisticsMixin, OrganizationMixin, ListCreateRetrieveViewSetMixin
):
    """
    Create mechanics:

    ## With JSON

    * `request_remarks: '',`
    * `start: '',`
    * `end: '',`
    * `start_time: 'optional',`
    * `end_time: 'optional'`

    ## With Form Data

    * `request_remarks:hello 1234`
    * `start:2020-03-03`
    * `end:2020-03-03`
    * `attachment0: File`
    * `attachment1: File`
    * `attachment2: File`
    * credit_requests[0].credit_hour_date: 2020-02-02
    * credit_requests[0].credit_hour_duration: 00:30:00
    * credit_requests[1].credit_hour_date: 2020-02-03
    * credit_requests[1].credit_hour_duration: 00:45:00
    """
    queryset = TravelAttendanceRequest.objects.all()
    serializer_class = TravelAttendanceRequestSerializer
    filter_backends = (
        FilterMapBackend,
        SearchFilter,
        NullsAlwaysLastOrderingFilter
    )
    search_fields = (
        'user__first_name', 'user__middle_name', 'user__last_name', 'user__username'
    )
    filter_map = {
        'status': 'status'
    }
    ordering_fields_map = {
        'full_name': ('user__first_name', 'user__middle_name', 'user__last_name'),
        'start': 'start',
        'end': 'end',
        'balance': 'balance',
        'status': 'status',
        'created_at': 'created_at',
    }
    statistics_field = 'status'
    permission_to_check = ATTENDANCE_TRAVEL_PERMISSION
    user_definition = 'user'

    def get_serializer_class(self):
        if self.request.method.upper() == 'POST':
            if self.request.query_params.get('as') in ['supervisor', 'hr']:
                return TravelAttendanceOnBehalfSerializer
            return TravelAttendanceWithCreditRequestSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        recipient = self.request.query_params.get('as') == 'supervisor'
        ret_qs = super().get_queryset().filter(
            user__detail__organization=self.organization
        )
        if recipient:
            ret_qs = ret_qs.filter(recipient=self.request.user)

        return ret_qs

    def get_serializer(self, *args, **kwargs):
        exclude_fields = []
        # mode = self.request.query_params.get('as')
        # if mode == 'hr':
        # elif mode == 'supervisor':
        #     exclude_fields = ['recipient']
        # else:
        #     exclude_fields = ['user', 'recipient']
        if self.action != 'retrieve':
            exclude_fields.append('days')
            exclude_fields.append('deleted_days')
            exclude_fields.append('histories')
        kwargs['exclude_fields'] = exclude_fields
        return super().get_serializer(*args, **kwargs)

    def filter_queryset(self, queryset):
        ret = super().filter_queryset(queryset).select_related(
            'user',
            'user__detail',
            'user__detail__job_title',
            'user__detail__division',
            'user__detail__organization',
            'user__detail__employment_level',
            'recipient',
            'recipient__detail',
            'recipient__detail__job_title',
            'recipient__detail__division',
            'recipient__detail__organization',
            'recipient__detail__employment_level',
        )
        # if self.action == 'retrieve':
        #     ret = ret.prefetch_related(
        #         Prefetch(
        #             lookup='attachments',
        #             queryset=TravelAttendanceAttachments.objects.order_by('created_at'),
        #             to_attr='_attachments'
        #         ),
        #         Prefetch(
        #             lookup='travel_attendances',
        #             queryset=TravelAttendanceDays.objects.all(),
        #             to_attr='_travel_attendances'
        #         ),
        #     )
        return ret

    @cached_property
    def is_authority(self):
        return validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            ATTENDANCE_TRAVEL_PERMISSION
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            'user': self.request.user,
            'organization': self.organization,
            'travel_setting': self.travel_setting,
            'sender': self.request.user,
            'allow_request': self.allow_credit_hour_request
        })
        return ctx

    def list(self, request, *args, **kwargs):
        if not self.travel_setting:
            raise ValidationError({
                'non_field_errors': [
                    'Please assign Travel Settings for this organization.'
                ]
            })
        ret = super().list(request, *args, **kwargs)
        ret.data.update({
            'statistics': self.statistics,
            'allow_travel_request': bool(self.allow_credit_hour_request)
        })
        return ret

    @action(
        methods=['GET'],
        detail=False,
        url_path='stats'
    )
    def stats(self, *args, **kwargs):
        """
        Provides count of Travel Attendance Request.
        response:
        {
            "pending": <pending_request_count>,
            "approved": <approved_request_count>
        }
        """
        return Response(
            self.get_queryset().aggregate(
                pending=Count('id', filter=Q(status=REQUESTED)),
                approved=Count('id', filter=Q(status=APPROVED))
            )
        )

    @action(
        methods=['PUT'],
        detail=True,
        url_path=r'(?P<status>(approve|decline|cancel|forward))',
    )
    def perform_action(self, *args, **kwargs):
        instance = self.get_object()
        data = deepcopy(self.request.data)
        status = {
            'approve': APPROVED,
            'decline': DECLINED,
            'cancel': CANCELLED,
            'forward': FORWARDED
        }.get(
            self.kwargs.get('status')
        )
        self.verify_recipient(
            instance,
            status,
            self.request.user
        )
        next_recipient = {
            APPROVED: instance.recipient,
            DECLINED: instance.recipient,
            # Fix cancelled requests sent back to the user.
            CANCELLED: instance.recipient,
            FORWARDED: getattr(
                get_appropriate_recipient(
                    user=instance.user,
                    level=(get_authority(instance.user, instance.recipient) or -1) + 1
                ),
                'supervisor',
                None
            )
        }.get(status)
        if not next_recipient:
            raise ValidationError({
                'errors': [
                    'Next recipient is not available.'
                ]
            })
        data['status'] = status
        ser = self.serializer_class(
            instance=instance,
            data=self.request.data,
            context={
                **self.get_serializer_context(),
                'recipient': next_recipient,
                'status': status
            }
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def verify_recipient(self, instance, status, user):
        old_status = instance.status
        if old_status in [APPROVED, CANCELLED, DECLINED]:
            self.permission_denied(
                request=self.request,
                message=f'{old_status} travel requests can not be updated.'
            )
        new_status = status
        if new_status == CANCELLED and instance.user == self.request.user:
            return
        if self.is_authority:
            # IF HR, no further checks to be done.
            return
        correct_recipient = instance.recipient
        if user != correct_recipient:
            self.permission_denied(
                request=self.request,
                message='You can not perform any actions to this travel request.'
            )
        # The user is the valid recipient, but can user perform the action?
        authority_to_check = {
            APPROVED: 'approve',
            DECLINED: 'deny',
            FORWARDED: 'forward'
        }.get(new_status)
        if not instance.user.user_supervisors.filter(
            supervisor=user,
            **{
                authority_to_check: True
            }
        ).exists():
            self.permission_denied(
                request=self.request,
                message=f'You can not perform {new_status} on this request.'
            )

    @cached_property
    def travel_setting(self):
        try:
            return TravelAttendanceSetting.objects.get(
                organization=self.organization
            )
        except TravelAttendanceSetting.DoesNotExist:
            return

    @property
    def allow_credit_hour_request(self):
        return nested_getattr(
            self.request.user,
            'attendance_setting.credit_hour_setting.require_prior_approval'
        )


class TravelAttendanceDaysViewSet(OrganizationMixin, ModelViewSet):
    queryset = TravelAttendanceDays.objects.all()
    serializer_class = TravelAttendanceDaysSerializer
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    )

    def get_queryset(self):
        is_authority = validate_permissions(
            self.request.user.get_hrs_permissions(),
        )
        base_qs = TravelAttendanceRequest.objects.filter(
            travel_attendance__user__detail__organization=self.organization
        )
        if not is_authority:
            base_qs = TravelAttendanceRequest.objects.filter(
                travel_attendance__user=self.request.user
            )
        travel_attendance = get_object_or_404(
            base_qs,
            pk=self.kwargs.get('travel_attendance_id')
        )
        return travel_attendance.travel_attendances.all()


class TravelAttendanceDeleteRequestViewSet(
    GetStatisticsMixin, ModeFilterQuerysetMixin, OrganizationMixin, ModelViewSet
):
    queryset = TravelAttendanceDeleteRequest.objects.all()
    serializer_class = TravelAttendanceDeleteRequestSerializer
    filter_backends = (
        filters.SearchFilter, FilterMapBackend, NullsAlwaysLastOrderingFilter
    )
    user_definition = 'travel_attendance__user'
    search_fields = (
        'travel_attendance__user__first_name',
        'travel_attendance__user__middle_name',
        'travel_attendance__user__last_name',
    )
    permission_to_check = ATTENDANCE_TRAVEL_PERMISSION
    statistics_field = 'status'
    filter_map = {
        'status': 'status'
    }
    ordering_fields_map = {
        'full_name': (
            'travel_attendance__user__first_name', 'travel_attendance__user__middle_name',
            'travel_attendance__user__last_name',
        ),
        'start': 'travel_attendance__start',
        'end': 'travel_attendance__end',
        'balance': 'travel_attendance__balance',
        'created_at': 'created_at',
    }

    def get_serializer(self, *args, **kwargs):
        if self.request.method in ['PUT', 'PATCH'] and self.action != 'perform_action':
            kwargs['exclude_fields'] = ['travel_attendance', 'action_remarks']
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().filter(
            travel_attendance__user__detail__organization=self.organization
        )
        recipient = self.request.query_params.get('as') == 'supervisor'
        if recipient:
            return qs.filter(recipient=self.request.user)
        return qs

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).select_related(
            'travel_attendance',
            'travel_attendance__user',
            'travel_attendance__user__detail',
            'travel_attendance__user__detail__organization',
            'travel_attendance__user__detail__job_title',
            'travel_attendance__user__detail__division',
            'travel_attendance__user__detail__employment_level',
            'travel_attendance__user__detail__employment_status',
            'travel_attendance__recipient'
        )

    @action(
        methods=['PUT'],
        detail=True,
        url_path=r'(?P<status>(approve|decline|forward))',
        serializer_class=type(
            'ActionSerializer',
            (Serializer,),
            {
                'action_remarks': CharField(max_length=255)
            }
        )
    )
    def perform_action(self, *args, **kwargs):
        instance = self.get_object()
        status = {
            'approve': APPROVED,
            'decline': DECLINED,
            'forward': FORWARDED
        }.get(
            self.kwargs.get('status')
        )
        self.verify_recipient(
            instance,
            status,
            self.request.user
        )
        next_recipient = {
            APPROVED: instance.recipient,
            DECLINED: instance.recipient,
            FORWARDED: getattr(
                get_appropriate_recipient(
                    user=instance.travel_attendance.user,
                    level=(get_authority(instance.travel_attendance.user,
                                         instance.recipient) or -1) + 1
                ),
                'supervisor',
                None
            )
        }.get(status)
        if not next_recipient:
            raise ValidationError({
                'errors': [
                    'Next recipient is not available.'
                ]
            })
        ser = TravelAttendanceDeleteRequestSerializer(
            instance=instance,
            data=self.request.data,
            exclude_fields=['travel_attendance', 'deleted_days'],
            context={
                **self.get_serializer_context(),
                'recipient': next_recipient,
                'status': status
            }
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def verify_recipient(self, instance, status, user):
        old_status = instance.status
        if old_status in [APPROVED, DECLINED]:
            self.permission_denied(
                request=self.request,
                message=f'{old_status} travel delete requests can not be updated.'
            )
        new_status = status

        if self.is_authority:
            # IF HR, no further checks to be done.
            return
        correct_recipient = instance.recipient
        if user != correct_recipient:
            self.permission_denied(
                request=self.request,
                message='You can not perform any actions to this travel request.'
            )
        # The user is the valid recipient, but can user perform the action?
        authority_to_check = {
            APPROVED: 'approve',
            DECLINED: 'deny',
            FORWARDED: 'forward'
        }.get(new_status)
        if not instance.travel_attendance.user.user_supervisors.filter(
            supervisor=user,
            **{
                authority_to_check: True
            }
        ).exists():
            self.permission_denied(
                request=self.request,
                message=f'You can not perform {new_status} on this request.'
            )

    @cached_property
    def is_authority(self):
        return validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            ATTENDANCE_TRAVEL_PERMISSION
        )

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status in [APPROVED, DECLINED]:
            raise ValidationError({
                'errors': 'Can not delete this delete request.'
            })
        return super().destroy(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        ret.data['statistics'] = self.statistics
        return ret
