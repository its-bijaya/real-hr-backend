from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from irhrs.attendance.api.v1.permissions import AttendanceAdjustmentPermission
from irhrs.attendance.api.v1.serializers.adjustment import \
    AttendanceAdjustmentDetailSerializer, AttendanceAdjustmentDeclineSerializer, \
    AttendanceAdjustmentHistorySerializer, AttendanceAdjustmentBulkSerializer, \
    AttendanceAdjustmentActionSerializer, AttendanceAdjustmentUpdateEntrySerializer, \
    AttendanceAdjustmentDeleteEntrySerializer
from irhrs.attendance.constants import FORWARDED, DECLINED, REQUESTED, APPROVED, CANCELLED
from irhrs.attendance.models import AttendanceAdjustment, \
    AttendanceAdjustmentHistory
from irhrs.attendance.utils.attendance import \
    get_adjustment_request_forwarded_to
from irhrs.core.constants.common import ATTENDANCE
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    ListRetrieveViewSetMixin, CreateViewSetMixin, OrganizationCommonsMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.core.utils.subordinates import set_supervisor_permissions
from irhrs.core.utils.user_activity import create_user_activity
from irhrs.permission.constants.permissions import ATTENDANCE_PERMISSION, \
    ATTENDANCE_ADJUSTMENTS_REQUEST_PERMISSION

USER = get_user_model()


class AttendanceAdjustmentViewSet(OrganizationMixin,
                                  ListRetrieveViewSetMixin):
    """
    filters:
        division= division_slug
        branch= branch_slug
    """
    queryset = AttendanceAdjustment.objects.select_related(
        'timesheet',
        'timesheet__timesheet_user',
        'timesheet__timesheet_user__detail',
        'timesheet__timesheet_user__detail__organization',
        'timesheet__timesheet_user__detail__division',
        'timesheet__timesheet_user__detail__job_title',
        'timesheet__timesheet_user__detail__employment_level',
        'sender__detail',
        'sender__detail__organization',
        'sender__detail__division',
        'sender__detail__job_title',
        'sender__detail__employment_level',
        'receiver__detail',
        'receiver__detail__organization',
        'receiver__detail__division',
        'receiver__detail__job_title',
        'receiver__detail__employment_level'
    )
    serializer_class = AttendanceAdjustmentDetailSerializer

    filter_backends = (SearchFilter, OrderingFilterMap, FilterMapBackend)
    search_fields = (
        'timesheet__timesheet_user__first_name',
        'timesheet__timesheet_user__middle_name',
        'timesheet__timesheet_user__last_name',
        'timesheet__timesheet_user__username'
    )

    ordering_fields_map = {
        'full_name': ('timesheet__timesheet_user__first_name',
                      'timesheet__timesheet_user__middle_name',
                      'timesheet__timesheet_user__last_name'),
        'timesheet': 'timesheet__timesheet_for',
        'created_at': 'created_at',
        'modified_at': 'modified_at',
    }
    filter_map = {
        'status': 'status',
        'receiver': 'receiver',
        'user_id': 'timesheet__timesheet_user__id',
        'branch': 'sender__detail__branch__slug',
        'division': 'sender__detail__division__slug',
        'start_date': 'timesheet__timesheet_for__gte',
        'end_date': 'timesheet__timesheet_for__lte',
    }
    permission_classes = [AttendanceAdjustmentPermission]


    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ['supervisor', 'hr']:
            return mode
        return 'user'

    def check_permissions(self, request):
        if self.mode == "hr" and request.user and request.user.is_authenticated:
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                ATTENDANCE_ADJUSTMENTS_REQUEST_PERMISSION,
                ATTENDANCE_PERMISSION
            )
            # If not is_hr and mode is hr raise permission denied directly
            if not is_hr:
                raise PermissionDenied
        super().check_permissions(request)

    def has_user_permission(self):
        if self.mode == "hr":
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                ATTENDANCE_ADJUSTMENTS_REQUEST_PERMISSION,
                ATTENDANCE_PERMISSION
            )
            # If not is_hr and mode is hr raise permission denied directly
            if not is_hr:
                return False

        # post actions limited to hr and supervisor now allow others as
        # get_queryset will filter
        if self.action in ['forward', 'approve', 'decline', 'bulk_action']:
            return self.mode in ['hr', 'supervisor']

        if self.action == 'cancel':
            return self.mode == 'hr'

        return True

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            Q(timesheet__timesheet_user__detail__organization=
              self.get_organization())
        )
        if self.mode == 'supervisor':
            return queryset.filter(
                receiver_id=self.request.user.id
            )
        if self.mode == 'hr':
            return queryset

        # default as=user
        # When HR deletes the timesheet entries, sender is HR,
        # Due to which user cannot see their cancelled request.
        # So filter by timesheet user is done instead of sender
        return queryset.filter(
            timesheet__timesheet_user=self.request.user
        )

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        if self.action == 'list' and self.mode == 'supervisor':
            return set_supervisor_permissions(page, self.request.user.id, 'sender')
        return page

    def get_serializer(self, *args, **kwargs):
        if (
            (self.action == 'list' and not self.mode == 'supervisor')
            or self.action == 'retrieve'
        ):
            kwargs.update({
                'exclude_fields': ['permissions']
            })
        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        if self.action in ['forward', 'approve', 'decline', 'cancel']:
            return AttendanceAdjustmentDeclineSerializer
        return super().get_serializer_class()

    def _qs_for_aggregate(self, user_id=None):
        self.filter_map.pop('status', None)
        # same reason as in get_queryset() when mode == "user"
        aggregate_qs = self.get_queryset().filter(
            timesheet__timesheet_user=user_id
        ) if user_id else self.get_queryset()
        res = self.filter_queryset(aggregate_qs).aggregate(
            Requested=Count('id', filter=Q(status=REQUESTED)),
            Forwarded=Count('id', filter=Q(status=FORWARDED)),
            Approved=Count('id', filter=Q(status=APPROVED)),
            Declined=Count('id', filter=Q(status=DECLINED)),
            Cancelled=Count('id', filter=Q(status=CANCELLED)),
            All=Count('id')
        )
        self.filter_map['status'] = 'status'
        return res

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        try:
            _user_id = request.query_params.get('user_id')
            user_id = int(_user_id) if _user_id else None
        except (TypeError, ValueError):
            user_id = None
        aggregate = self._qs_for_aggregate(user_id)
        response.data.update({"counts": aggregate})
        return response

    @action(methods=['GET'], detail=False, url_name='counts')
    def counts(self, request, *args, **kwargs):
        # Adjustments, whose recipient the user is
        queryset = self.filter_queryset(self.get_queryset())
        if self.mode == 'supervisor':
            queryset = queryset.filter(
                receiver=request.user,
                sender__detail__organization=self.organization
            )
        elif validate_permissions(
            request.user.get_hrs_permissions(self.organization),
            ATTENDANCE_PERMISSION
        ):
            queryset = queryset
        else:
            queryset = queryset.none()
        return Response(queryset.aggregate(
            Requested=Count('id', filter=Q(status=REQUESTED)),
            Forwarded=Count('id', filter=Q(status=FORWARDED)),
            Approved=Count('id', filter=Q(status=APPROVED)),
            Declined=Count('id', filter=Q(status=DECLINED)),
            Cancelled=Count('id', filter=Q(status=CANCELLED)),
            All=Count('id')
        ))

    @action(methods=['POST'], detail=True, url_name='forward',
            url_path='forward')
    def forward(self, request, *args, **kwargs):
        adjustment = self.get_object()

        if adjustment.status in [APPROVED, DECLINED]:
            raise ValidationError(
                {'non_field_errors':
                    [
                        "Could not forward request. Status is already"
                        f" {adjustment.status}"
                    ]
                }
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        forward_to = get_adjustment_request_forwarded_to(adjustment)

        if adjustment.receiver != request.user:
            raise PermissionDenied

        if not forward_to:
            raise ValidationError(
                {'non_field_errors': ["You can not forward this request."]}
            )

        adjustment.receiver = forward_to.supervisor
        adjustment.status = FORWARDED
        adjustment.save()

        AttendanceAdjustmentHistory.objects.create(
            adjustment=adjustment,
            action_performed_by=request.user,
            action_performed_to=forward_to.supervisor,
            action_performed=FORWARDED,
            remark=serializer.data.get('remark')
        )

        create_user_activity(
            request.user,
            f"forwarded an adjustment request.",
            ATTENDANCE
        )

        return Response(data={'message': 'Successfully forwarded request.'})

    @action(methods=['POST'], detail=True, url_name='approve',
            url_path='approve')
    def approve(self, request, *args, **kwargs):
        adjustment = self.get_object()

        if adjustment.status not in [FORWARDED, REQUESTED]:
            raise ValidationError({'non_field_errors': ["Could not approve "
                                                        "request. The status "
                                                        "is already "
                                                        f"{adjustment.status}."
                                                        ]})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        authority = self.get_authority(adjustment)

        # if receiver is acting
        if self.mode != 'hr' and request.user == adjustment.receiver and not getattr(
                authority, 'approve', None
        ):
            raise ValidationError({
                'non_field_errors': ["You do not have permission to approve "
                                     "this request."]})

        adjustment.approve(approved_by=request.user,
                           remark=serializer.data.get('remark'))

        create_user_activity(
            request.user,
            f"approved an adjustment request.",
            ATTENDANCE
        )
        return Response({'message': 'Approved Attendance Adjustment'})

    @action(methods=['POST'], detail=True, url_name='decline',
            url_path='decline')
    def decline(self, request, *args, **kwargs):
        adjustment = self.get_object()

        if adjustment.status not in [FORWARDED, REQUESTED]:
            raise ValidationError({'non_field_errors': ["Could not decline "
                                                        "requestThe status "
                                                        "is already "
                                                        f"{adjustment.status}."]
                                   })

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        authority = self.get_authority(adjustment)

        # if receiver is acting
        if request.user == adjustment.receiver and not getattr(
                authority, 'deny', None
        ):
            raise ValidationError({
                'non_field_errors': ["You do not have permission to decline "
                                     "this request."]})

        adjustment.status = DECLINED
        adjustment.save()

        AttendanceAdjustmentHistory.objects.create(
            adjustment=adjustment,
            action_performed_by=request.user,
            action_performed_to=request.user,
            action_performed=DECLINED,
            remark=serializer.data.get('remark')
        )

        create_user_activity(
            request.user,
            "declined an adjustment request.",
            ATTENDANCE
        )

        return Response({'message': 'Declined adjustment request.'})

    @action(methods=['POST'], detail=True, url_name='cancel',
            url_path='cancel')
    def cancel(self, request, *args, **kwargs):
        return Response(status=410)
        # instance = self.get_object()
        # if instance.status != APPROVED:
        #     raise ValidationError(
        #         {'non_field_errors': _("Only approved requests can be cancelled.")}
        #     )
        #
        # serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # instance.cancel(cancelled_by=self.request.user, remark=serializer.data.get('remark'))
        #
        # create_user_activity(
        #     request.user,
        #     f"cancelled an adjustment request.",
        #     ATTENDANCE
        # )
        #
        # return Response({'message': 'Cancelled Attendance Adjustment'})

    @action(methods=['GET'], detail=True, url_name='history',
            url_path='history')
    def history(self, request, *args, **kwargs):
        adjustment = self.get_object()
        qs = adjustment.adjustment_histories.all()

        paginated_queryset = self.paginate_queryset(qs)
        data = AttendanceAdjustmentHistorySerializer(
            paginated_queryset, many=True).data
        return self.get_paginated_response(data)

    @action(methods=['POST'], detail=False, url_name='bulk-action',
            url_path='bulk-action', serializer_class=DummySerializer)
    def bulk_action(self, request, *args, **kwargs):
        """
        BULK ACTION

        POST DATA -->

            [{
                "adjustment": adjustment_id,
                "action": "approve",
                "remark": "Approved"
            },...]

        `action` can be one of "approve", "deny" or "forward"
        """
        ctx = self.get_serializer_context()
        ctx["adjustments"] = self.get_queryset()

        ser = AttendanceAdjustmentActionSerializer(
            data=request.data, many=True, context=ctx
        )
        ser.is_valid(raise_exception=True)
        ser.save()

        return Response({"message": _("Successfully Applied actions")})

    @staticmethod
    def get_authority(adjustment):
        return adjustment.sender.supervisors.filter(
            supervisor=adjustment.receiver
        ).first()


class AttendanceBulkAdjustmentViewSet(
    OrganizationMixin,
    OrganizationCommonsMixin,
    CreateViewSetMixin
):
    serializer_class = AttendanceAdjustmentBulkSerializer


class AttendanceAdjustmentUpdateDeleteEntryViewSet(
    OrganizationMixin,
    OrganizationCommonsMixin,
    CreateViewSetMixin
):
    def get_serializer_class(self):
        return {
            'edit': AttendanceAdjustmentUpdateEntrySerializer,
            'delete': AttendanceAdjustmentDeleteEntrySerializer,
        }.get(self.kwargs.get('adjustment_action', 'edit'))

    def get_serializer(self, *args, **kwargs):
        if self.kwargs.get('adjustment_action') == 'delete':
            kwargs['fields'] = ('timesheet', 'timesheet_entry', "description")
        return super().get_serializer(*args, **kwargs)
