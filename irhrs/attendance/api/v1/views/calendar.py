from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.conf import settings
from rest_framework.generics import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from dateutil.parser import parse
from rest_framework.response import Response

from irhrs.attendance.api.v1.serializers.calendar import \
    AttendanceCalenderSerializer, AttendanceCalendarRegenerateSerializer
from irhrs.attendance.constants import REQUESTED, FORWARDED
from irhrs.attendance.models import TimeSheet, AttendanceAdjustment
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin
from irhrs.organization.models import Organization
from irhrs.permission.constants.permissions import ATTENDANCE_PERMISSION, ATTENDANCE_REPORTS_PERMISSION, \
    ATTENDANCE_OFFLINE_PERMISSION
from irhrs.permission.permission_classes import permission_factory


class AttendanceCalendar(ListViewSetMixin):
    """
     List:

        Get all the time sheets for logged in use

        filters : start , end [YYYY-MM-DD]
        eg : ?start=1212-12-12&end=2020-12-12

    """
    serializer_class = AttendanceCalenderSerializer
    pagination_class = None
    start_date = None
    end_date = None
    _for_user_id = None
    permission_classes = [permission_factory.build_permission(
        "AttendanceCalendarPermission",
        actions={
            'employee_attendance': [
                ATTENDANCE_PERMISSION,
                ATTENDANCE_REPORTS_PERMISSION
            ],
            'regenerate_time_sheets': [
                ATTENDANCE_PERMISSION,
                ATTENDANCE_OFFLINE_PERMISSION
            ]
        }
    )]

    def get_queryset(self):
        if not self._for_user_id:
            return TimeSheet.objects.none()
        return TimeSheet.objects.filter(
            timesheet_user=self._for_user_id
        ).select_related('work_time',
                         'work_shift'
                         ).prefetch_related(
            'timesheet_entries',
            Prefetch('adjustment_requests',
                     queryset=AttendanceAdjustment.objects.filter(
                         status__in=[REQUESTED, FORWARDED]),
                     to_attr='adj_requests'))

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        self.start_date = self.request.query_params.get('start', None)
        self.end_date = self.request.query_params.get('end', None)

        if not (self.start_date and self.end_date):
            return TimeSheet.objects.none()
        try:
            self.start_date = parse(self.start_date)
            self.end_date = parse(self.end_date)
        except (ValueError, TypeError):
            return TimeSheet.objects.none()

        queryset = queryset.filter(
            timesheet_for__gte=self.start_date,
            timesheet_for__lte=self.end_date
        )
        return queryset

    def list(self, request, *args, **kwargs):
        self._for_user_id = self._for_user_id or self.request.user.id
        result = super().list(request, *args, **kwargs)
        data = {
            'start_date': self.start_date.date() if self.start_date else '',
            'end_date': self.end_date.date() if self.end_date else '',
            'results': result.data,
        }

        if self.action == 'employee_attendance':
            data['delete_allowed_entry_methods'] = settings.DELETE_ALLOWED_TIMESHEET_ENTRY_METHODS

        result.data = dict()
        result.data.update(data)
        return result

    def get_serializer_class(self):
        if self.action == 'regenerate_time_sheets':
            return AttendanceCalendarRegenerateSerializer
        return super().get_serializer_class()

    # Requires HR permission
    @action(detail=False, url_path=r'(?P<user_id>[\d]+)')
    def employee_attendance(self, request, user_id, *args, **kwargs):
        self._for_user_id = user_id
        return self.list(request, *args, **kwargs)

    @action(detail=False, url_path=r'(?P<user_id>[\d]+)/sub')
    def sub_ordinate_attendance(self, request, user_id, *args, **kwargs):
        if int(user_id) in \
                self.request.user.subordinates_pks or \
                self.request.user.id == int(user_id):
            self._for_user_id = user_id
            return self.list(request, *args, **kwargs)
        return Response(status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['POST'], url_path=r'(?P<user_id>[\d]+)/regenerate')
    def regenerate_time_sheets(self, request, user_id, *args, **kwargs):
        user = get_object_or_404(
            get_user_model().objects.filter(detail__organization=self.get_organization()),
            id=self.kwargs.get('user_id'),
        )
        context = self.get_serializer_context()
        context['user'] = user
        serializer = AttendanceCalendarRegenerateSerializer(
            data=request.data,
            context=context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Timesheet(s) will be regenerated.'
        })

    def get_organization(self):
        return get_object_or_404(
            Organization.objects.filter(
                id__in=self.request.user.switchable_organizations_pks
            ),
            slug=self.request.query_params.get('organization_slug')
        )
