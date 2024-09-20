from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Exists, Q
from rest_framework.fields import ReadOnlyField
from rest_framework.response import Response

from irhrs.attendance.api.v1.reports.serializers.summary import UserAttendanceSummarySerializer
from irhrs.attendance.api.v1.reports.views.attendance_by_category import AttendanceCategoryCommon
from irhrs.attendance.constants import WORKDAY, NO_LEAVE, TIME_OFF, FULL_LEAVE
from irhrs.attendance.models import TimeSheet
from irhrs.attendance.models.travel_attendance import TravelAttendanceDays
from irhrs.core.mixins.serializers import create_dummy_serializer
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, ListViewSetMixin
from irhrs.core.utils.common import get_today, get_common_queryset
from irhrs.leave.api.v1.serializers.on_leave import UserOnLeaveSerializer
from irhrs.leave.constants.model_constants import APPROVED
from irhrs.leave.models.request import LeaveSheet
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

USERS = get_user_model()


class SubordinateStatsForAttendanceAndLeave(
    AttendanceCategoryCommon,
    ListViewSetMixin
):
    serializer_class = create_dummy_serializer(
        {
            "user": UserThinSerializer(
                source="timesheet_user",
                fields=(
                    'id', 'full_name', 'profile_picture', "cover_picture", "is_online",
                    "job_title", 'is_current', 'organization',)
            ),
            "punch_in": ReadOnlyField(),
            "punch_out": ReadOnlyField()
        }
    )
    common_queryset = USERS.objects.all()

    def leave_queryset(self):
        queryset = get_common_queryset(
            self=self,
            queryset=self.common_queryset,
            fil=dict(
                leave_requests__status=APPROVED
            )
        )
        leave_sheet = LeaveSheet.objects.filter(
            leave_for=get_today(),
            request__is_deleted=False,
            request__status=APPROVED
        ).filter(
            request__user=OuterRef('id')
        )
        return queryset.current().annotate(
            leave_sheet_exists=Exists(leave_sheet)
        ).filter(leave_sheet_exists=True).select_related(
            'detail', 'detail__employment_level', 'detail__job_title',
            'detail__division'
        ).distinct()

    def punch_in_queryset(self, category):
        queryset = self.get_queryset().filter(
            **self.get_category_filter(category=category)
        )
        return queryset.select_related('timesheet_user', 'timesheet_user__detail',
                                       "timesheet_user__detail__job_title")

    def absent_queryset(self):
        queryset = get_common_queryset(
            self=self,
            queryset=self.common_queryset,
            fil=dict(
                user_experiences__is_current=True,
            )
        )
        is_present = self.common_queryset.current().filter(
            id=OuterRef("id"),
            timesheets__timesheet_for=get_today(),
            timesheets__is_present=True,
            timesheets__coefficient=WORKDAY,
            timesheets__leave_coefficient=NO_LEAVE
        )

        return queryset.annotate(
            is_present=Exists(is_present)
        ).filter(
            Q(is_present=False) and
            Q(
                timesheets__timesheet_for=get_today(),
                timesheets__coefficient=WORKDAY,
                timesheets__leave_coefficient=NO_LEAVE,
                timesheets__is_present=False
            )
        ).select_related(
            'detail',
            'detail__employment_level',
            'detail__job_title',
            'detail__division',
            'attendance_setting'
        ).distinct()

    # get data for stats
    def get_late_in_data(self):
        late_in_queryset = self.punch_in_queryset(category='late-in')
        late_in_serializer = self.get_serializer(
            late_in_queryset,
            many=True
        )
        return {
            'count': late_in_queryset.count(),
            'data': late_in_serializer.data
        }

    def get_early_out_data(self):
        early_out_queryset = self.punch_in_queryset(category='early-out')
        early_out_serializer = self.get_serializer(
            early_out_queryset,
            many=True
        )
        return {
            'count': early_out_queryset.count(),
            'data': early_out_serializer.data
        }

    def get_absent_data(self):
        absent_queryset = self.absent_queryset()
        absent_data = UserAttendanceSummarySerializer(
            absent_queryset,
            many=True
        )
        return {
            'count': absent_queryset.count(),
            'data': absent_data.data
        }

    def get_leave_data(self):
        leave_queryset = self.leave_queryset()
        leave_serializer = UserOnLeaveSerializer(
            leave_queryset,
            many=True,
            context=self.get_serializer_context()
        )
        return {
            'count': leave_queryset.count(),
            'data': leave_serializer.data
        }

    def list(self, request, *args, **kwargs):
        _data = {}
        _data = dict(
            leave=self.get_leave_data(),
            late_in=self.get_late_in_data(),
            early_out=self.get_early_out_data(),
            absent=self.get_absent_data()
        )
        return Response(_data)
