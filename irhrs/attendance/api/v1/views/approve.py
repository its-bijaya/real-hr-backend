from django.db import transaction
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from irhrs.attendance.api.v1.permissions import TimeSheetEntryApprovalPermission
from irhrs.attendance.api.v1.serializers.approve import TimeSheetApprovalSerializer, \
    TimeSheetEntryApproveSerializer
from irhrs.attendance.constants import APPROVED, REQUESTED, DECLINED, FORWARDED
from irhrs.attendance.models import TimeSheet
from irhrs.attendance.models.approval import TimeSheetApproval
from irhrs.attendance.utils.attendance import get_next_supervisor
from irhrs.core.constants.common import WEB_ATTENDANCE_APPROVAL
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, ListViewSetMixin, \
    GetStatisticsMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.notification.utils import add_notification
from irhrs.permission.constants.permissions.attendance import ATTENDANCE_APPROVAL_PERMISSION


class TimeSheetApprovalViewSet(OrganizationMixin, ListViewSetMixin, GetStatisticsMixin):
    serializer_class = TimeSheetApprovalSerializer
    queryset = TimeSheetApproval.objects.all()
    permission_classes = [TimeSheetEntryApprovalPermission]
    filter_backends = (FilterMapBackend,)
    filter_map = {
        'status': 'status',
        'start_date': 'timesheet__timesheet_for__gte',
        'end_date': 'timesheet__timesheet_for__lte',
        'user': 'timesheet__timesheet_user'
    }
    statistics_field = 'status'

    @property
    def mode(self):
        mode = self.request.query_params.get('as', 'user')
        if mode not in ['user', 'hr', 'supervisor']:
            return 'user'
        return mode

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['mode'] = self.mode
        if self.action == 'request_action' and 'pk' in self.kwargs:
            context['timesheet'] = self.get_object()
        return context

    def has_user_permission(self):
        if self.mode == 'hr' and self.request.user.is_authenticated:
            return validate_permissions(
                self.request.user.get_hrs_permissions(self.organization),
                ATTENDANCE_APPROVAL_PERMISSION
            )
        return True

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            timesheet__timesheet_user__detail__organization=self.organization
        )
        if self.mode == 'supervisor':
            queryset = queryset.filter(timesheet_entry_approval__recipient=self.request.user)
        elif self.mode == 'user':
            queryset = queryset.filter(timesheet__timesheet_user=self.request.user)
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['stats'] = self.statistics
        return response

    @transaction.atomic
    @action(
        detail=True,
        methods=['POST'],
        serializer_class=TimeSheetEntryApproveSerializer,
        url_path='action',
        url_name='action'
    )
    def request_action(self, request, *args, **kwargs):
        """
        Approve, Deny or Forward user request for web attendance request.
        """
        ser = self.get_serializer(
            data=request.data
        )
        ser.is_valid(raise_exception=True)

        entries = ser.data.get('timesheet')
        status = ser.data.get('status')

        if not entries:
            raise ValidationError({
                "detail": "At least one timesheet entry must be selected."
            })
        timesheet_approval = self.get_object()
        timesheet = timesheet_approval.timesheet
        user = timesheet.timesheet_user

        timesheet_entries = timesheet_approval.timesheet_entry_approval.filter(
            id__in=entries
        )

        # checks whether supervisor can decline or not
        if status == DECLINED and self.mode == 'supervisor':
            supervisor = user.supervisors.filter(
                supervisor=request.user
            ).first()
            if not getattr(supervisor, 'deny', None):
                raise ValidationError({
                    'detail': 'You can only approve or forward this request.'
                })

        interactive_data = dict(
            is_interactive=True,
            interactive_type=WEB_ATTENDANCE_APPROVAL,
            interactive_data={
                'timesheet_id': timesheet_approval.timesheet.id,
                'organization': {
                    'name': user.detail.organization.name,
                    'slug': user.detail.organization.slug,
                }
            }
        )
        if status == FORWARDED:
            next_supervisor = None

            # check if hr forwards the request
            if self.mode != 'supervisor':
                raise ValidationError({
                    'detail': 'You can only approve or deny requests.'
                })

            for timesheet_entry in timesheet_entries:
                # to get next_supervisor when it is empty
                if not next_supervisor:
                    next_supervisor = get_next_supervisor(
                        timesheet_entry.timesheet_approval.timesheet.timesheet_user,
                        timesheet_entry.recipient
                    )
                if not next_supervisor:
                    raise ValidationError({
                        'detail': 'You can only approve or deny requests.'
                    })
                timesheet_entry.recipient = next_supervisor.supervisor
                timesheet_entry.save()

            # send notification to next supervisor
            if next_supervisor:
                add_notification(
                    text=f"{user.full_name} attendance request for {timesheet.timesheet_for} has been "
                         f"{status.lower()} by {request.user.full_name}.",
                    recipient=next_supervisor.supervisor,
                    action=timesheet_approval,
                    actor=self.request.user,
                    url=f'/user/supervisor/attendance/requests/web-attendance/?user={user.id}',
                    **interactive_data
                )

        if status == APPROVED:
            for timesheet_entry in timesheet_entries:
                TimeSheet.objects.clock(
                    user=user,
                    timesheet=timesheet,
                    date_time=timesheet_entry.timestamp,
                    entry_method=timesheet_entry.entry_method,
                    entry_type=timesheet_entry.entry_type,
                    remarks=timesheet_entry.remarks,
                    remark_category=timesheet_entry.remark_category,
                    latitude=timesheet_entry.latitude,
                    longitude=timesheet_entry.longitude,
                    working_remotely=timesheet.working_remotely,
                )

        _ = timesheet_entries.update(status=status)

        # updating status of timesheet approval
        if not timesheet_approval.timesheet_entry_approval.filter(status=REQUESTED).exists():
            if timesheet_approval.timesheet_entry_approval.filter(status=FORWARDED).exists():
                timesheet_approval.status = FORWARDED
            elif timesheet_approval.timesheet_entry_approval.filter(status=APPROVED).exists():
                timesheet_approval.status = APPROVED
            else:
                timesheet_approval.status = DECLINED
        timesheet_approval.save()

        add_notification(
            text=f"Your attendance request for {timesheet.timesheet_for} has been "
                 f"{status.lower()} by {request.user.full_name}.",
            recipient=user,
            action=timesheet_approval,
            actor=self.request.user,
            url='/user/attendance/reports/web-attendance',
            **interactive_data
        )
        return Response({'detail': f'Successfully {status.lower()} attendance request.'})
