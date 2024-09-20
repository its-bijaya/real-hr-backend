from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

from irhrs.attendance.api.v1.serializers.timesheet_report_request import \
    ReadOnlyTimeSheetReportRequestSerializer, TimeSheetReportActionSerializer, \
    RemarksRequiredSerializer, TimeSheetReportRequestHistorySerializer, RemarksOptionalSerializer
from irhrs.attendance.constants import REQUESTED, APPROVED, FORWARDED, DECLINED, CONFIRMED, \
    GENERATED
from irhrs.attendance.models.timesheet_report_request import TimeSheetReportRequest, \
    TimeSheetReportRequestHistory
from irhrs.attendance.utils.timesheet_report import generate_timesheet_report_of_user, \
    update_timesheet_report
from irhrs.core.mixins.viewset_mixins import ListRetrieveViewSetMixin, OrganizationMixin, \
    OrganizationCommonsMixin, GetStatisticsMixin
from irhrs.core.utils import subordinates, get_system_admin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.permission.constants.permissions import HAS_PERMISSION_FROM_METHOD
from irhrs.permission.constants.permissions.attendance import \
    ATTENDANCE_TIMESHEET_REPORT_PERMISSION, ATTENDANCE_TIMESHEET_REPORT_VIEW_PERMISSION
from irhrs.permission.permission_classes import permission_factory

USER = get_user_model()


class TimeSheetReportRequestViewSet(
    GetStatisticsMixin,
    OrganizationMixin,
    OrganizationCommonsMixin,
    ListRetrieveViewSetMixin
):

    queryset = TimeSheetReportRequest.objects.all().select_related(
        'user',
        'user__detail',
        'user__detail__job_title',
        'user__detail__organization',
        'recipient',
        'recipient__detail',
        'recipient__detail__job_title',
        'recipient__detail__organization'
    )
    organization_field = 'user__detail__organization'
    serializer_class = ReadOnlyTimeSheetReportRequestSerializer

    permission_classes = [
        permission_factory.build_permission(
            "TimeSheetReportRequestPermission",
            allowed_to=[HAS_PERMISSION_FROM_METHOD]
        )
    ]
    filter_backends = [FilterMapBackend, OrderingFilterMap]
    ordering_fields_map = {
        'modified_at': 'modified_at',
        'created_at': 'created_at',
        'month_from_date': 'month_from_date',
        'month_to_date': 'month_to_date'
    }

    filter_map = {
        'user': 'user',
        'recipient': 'recipient',
        'status': 'status',
        'from_date': 'month_from_date__gte',
        'to_date': 'month_from_date__lte'
    }  # for statistics mixin
    statistics_field = 'status'

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs.update({'exclude_fields': ['report_data', 'authorized_signature']})
        return super().get_serializer(*args, **kwargs)

    def has_user_permission(self):
        if self.mode == 'hr':
            if validate_permissions(
                    self.request.user.get_hrs_permissions(self.get_organization()),
                    ATTENDANCE_TIMESHEET_REPORT_PERMISSION
            ) or (
                    self.request.method in SAFE_METHODS
                    and validate_permissions(
                        self.request.user.get_hrs_permissions(self.get_organization()),
                        ATTENDANCE_TIMESHEET_REPORT_VIEW_PERMISSION
                    )
            ):
                return True
            return False
        return True

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ['hr', 'supervisor']:
            return mode
        return 'user'

    def get_queryset(self):
        qs = super().get_queryset()
        if self.mode == 'hr':
            user_status = self.request.query_params.get('user_status')
            if user_status == 'past':
                qs = qs.filter(user__in=USER.objects.all().past())
            elif user_status == 'current':
                qs = qs.filter(user__in=USER.objects.all().current())
            return qs
        elif self.mode == 'supervisor':
            return qs.filter(recipient=self.request.user)
        else:
            return qs.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['counts'] = self.statistics
        return response

    def perform_request(self, instance, remarks, attached_signature):
        instance.recipient = instance.user.first_level_supervisor_including_bot
        if not instance.recipient:
            raise ValidationError({'non_field_errors': _("First level supervisor not found.")})

        if instance.status not in [GENERATED, DECLINED]:
            raise ValidationError({
                'non_field_errors': _("Only generated or declined status can be requested.")
            })

        instance.status = REQUESTED
        instance.save()

        TimeSheetReportRequestHistory.objects.create(
            request=instance,
            actor=self.request.user,
            action=REQUESTED,
            action_to=instance.recipient,
            attached_signature=attached_signature,
            remarks=remarks
        )
        # send notification

    def perform_approve(self, instance, remarks, attached_signature):

        if instance.status not in [REQUESTED, FORWARDED]:
            raise ValidationError({
                'non_field_errors': _("Only requested or forwarded status can be approved.")
            })
        if self.mode == 'supervisor' and not subordinates.authority_exists(
            instance.user, self.request.user, 'approve'
        ):
            raise self.permission_denied(self.request)

        instance.status = APPROVED
        instance.save()

        TimeSheetReportRequestHistory.objects.create(
            request=instance,
            actor=self.request.user,
            action=APPROVED,
            attached_signature=attached_signature,
            remarks=remarks
        )
        # send notification

    def perform_deny(self, instance, remarks):
        allowed_status = [REQUESTED, FORWARDED, APPROVED] \
            if self.mode == 'hr' else [REQUESTED, FORWARDED]

        if instance.status not in allowed_status:
            raise ValidationError({
                'non_field_errors': _(f"Only {', '.join(allowed_status)} status can be denied.")
            })

        if self.mode == 'supervisor' and not subordinates.authority_exists(
            instance.user, self.request.user, 'deny'
        ):
            raise self.permission_denied(self.request)

        instance.status = DECLINED
        instance.save()

        TimeSheetReportRequestHistory.objects.create(
            request=instance,
            actor=self.request.user,
            action=DECLINED,
            action_to=instance.user,
            remarks=remarks
        )
        # send notification

    def perform_forward(self, instance, remarks):
        if instance.status not in [REQUESTED, FORWARDED]:
            raise ValidationError({
                'non_field_errors': _("Only requested or forwarded status can be forwarded.")
            })

        if not subordinates.authority_exists(
            instance.user, self.request.user, 'forward'
        ):
            raise self.permission_denied(self.request)

        instance.recipient = subordinates.get_next_level_supervisor(
            instance.user,
            instance.recipient
        )

        if not instance.recipient:
            raise ValidationError({'non_field_errors': _("Next level supervisor not found.")})

        instance.status = FORWARDED
        instance.save()

        TimeSheetReportRequestHistory.objects.create(
            request=instance,
            actor=self.request.user,
            action=FORWARDED,
            action_to=instance.recipient,
            remarks=remarks
        )
        # send notification

    def perform_confirm(self, instance, remarks, attached_signature):
        if instance.status != APPROVED and not (
            instance.status == REQUESTED and
            instance.user.first_level_supervisor_including_bot == get_system_admin()
        ):
            raise ValidationError({
                'non_field_errors': _("Only approved status can be confirmed.")
            })
        instance.status = CONFIRMED
        instance.save()

        TimeSheetReportRequestHistory.objects.create(
            request=instance,
            actor=self.request.user,
            action=CONFIRMED,
            action_to=instance.user,
            attached_signature=attached_signature,
            remarks=remarks
        )
        # send notification

    def perform_regenerate(self, instance, remarks):
        if instance.status not in [GENERATED, DECLINED]:
            raise ValidationError({
                'non_field_errors': _("Only denied and generated status can be regenerated.")
            })
        new_report_data = generate_timesheet_report_of_user(
            user=instance.user,
            fiscal_month=instance.fiscal_month,
            report_settings=None,  # will be taken from user.detail.organization by util
        )
        update_timesheet_report(
            instance=instance,
            report_data=new_report_data,
            actor=self.request.user,
            remarks=remarks
        )

    @action(
        methods=['post'],
        detail=True,
        serializer_class=TimeSheetReportActionSerializer,
        url_path='request',
        url_name='request'
    )
    def request_action(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (self.mode == 'user' and instance.user == request.user):
            raise self.permission_denied(request)

        serializer = TimeSheetReportActionSerializer(
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        remarks = serializer.validated_data.get('remarks', '')
        authorized_signature = None
        if serializer.validated_data.get('add_signature', False):
            authorized_signature = request.user.signature

        self.perform_request(instance, remarks, authorized_signature)

        return Response({
            'message': 'Successfully requested'
        })

    @action(
        methods=['post'],
        detail=True,
        serializer_class=TimeSheetReportActionSerializer,
        url_path='approve',
        url_name='approve'
    )
    def approve_action(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (self.mode == 'hr' or (
            self.mode == 'supervisor' and instance.recipient == request.user)
        ):
            raise self.permission_denied(request)

        serializer = TimeSheetReportActionSerializer(
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        remarks = serializer.validated_data.get('remarks', '')
        authorized_signature = None
        if serializer.validated_data.get('add_signature', False):
            authorized_signature = request.user.signature

        self.perform_approve(instance, remarks, authorized_signature)

        return Response({
            'message': 'Successfully approved'
        })

    @action(
        methods=['post'],
        detail=True,
        serializer_class=RemarksRequiredSerializer,
        url_path='deny',
        url_name='deny'
    )
    def deny_action(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (self.mode == 'hr' or (
            self.mode == 'supervisor' and instance.recipient == request.user)
        ):
            raise self.permission_denied(request)

        serializer = RemarksRequiredSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        remarks = serializer.validated_data.get('remarks', '')

        self.perform_deny(instance, remarks)

        return Response({
            'message': 'Denied Request'
        })

    @action(
        methods=['post'],
        detail=True,
        serializer_class=RemarksRequiredSerializer,
        url_path='forward',
        url_name='forward'
    )
    def forward_action(self, request, *args, **kwargs):
        instance = self.get_object()
        if (not (
            self.mode == 'supervisor' and instance.recipient == request.user
        )):
            raise self.permission_denied(request)

        serializer = RemarksRequiredSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        remarks = serializer.validated_data.get('remarks', '')

        self.perform_forward(instance, remarks)

        return Response({
            'message': 'Successfully forwarded request.'
        })

    @action(
        methods=['post'],
        detail=True,
        serializer_class=TimeSheetReportActionSerializer,
        url_path='confirm',
        url_name='confirm'
    )
    def confirm_action(self, request, *args, **kwargs):
        instance = self.get_object()
        if not self.mode == 'hr':
            raise self.permission_denied(request)

        serializer = TimeSheetReportActionSerializer(
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        remarks = serializer.validated_data.get('remarks', '')
        authorized_signature = None
        if serializer.validated_data.get('add_signature', False):
            authorized_signature = request.user.signature

        self.perform_confirm(instance, remarks, authorized_signature)

        return Response({
            'message': 'Successfully confirmed request.'
        })

    @action(
        methods=['post'],
        detail=True,
        serializer_class=RemarksOptionalSerializer,
        url_path='regenerate',
        url_name='regenerate'
    )
    def regenerate_action(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (self.mode == 'hr' or (self.mode == 'user' and self.request.user == instance.user)):
            raise self.permission_denied(request)

        serializer = RemarksOptionalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        remarks = serializer.validated_data.get('remarks', '')

        self.perform_regenerate(instance, remarks)

        return Response({
            'message': 'Successfully regenerated request.'
        })

    @action(
        methods=['get'],
        detail=True,
        serializer_class=TimeSheetReportRequestHistorySerializer
    )
    def histories(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.histories.order_by('-created_at').select_related(
            'actor',
            'actor__detail',
            'actor__detail__organization',
            'actor__detail__job_title',
            'action_to',
            'action_to__detail',
            'action_to__detail__organization',
            'action_to__detail__job_title',
        )
        page = self.paginate_queryset(qs)
        ser = self.serializer_class(page, context=self.get_serializer_context(), many=True)

        return self.get_paginated_response(ser.data)
