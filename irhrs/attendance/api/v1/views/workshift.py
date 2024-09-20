from dateutil import parser
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.functional import cached_property

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status

from irhrs.attendance.api.v1.permissions import (
    UserActiveShiftPermission, AttendanceWorkShiftPermission,
)
from irhrs.attendance.api.v1.serializers.workshift import WorkShiftSerializer, \
    WorkTimingSerializer, UserWorkTimingSerializer, WorkShiftLegendSerializer
from irhrs.attendance.models import WorkShift, WorkTiming, WorkShiftLegend, IndividualUserShift
from irhrs.attendance.utils.attendance import get_timing_info
from irhrs.attendance.utils.helpers import get_weekday
from irhrs.attendance.validation_error_messages import INVALID_DATE
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    OrganizationCommonsMixin, DisallowPatchMixin, ListRetrieveViewSetMixin, \
    UserMixin, ListViewSetMixin, ValidateUsedData, ListCreateViewSetMixin
from irhrs.core.utils.common import DummyObject, combine_aware

USER = get_user_model()


class WorkShiftViewSet(
    DisallowPatchMixin,
    OrganizationCommonsMixin,
    OrganizationMixin,
    ValidateUsedData,
    ModelViewSet
):
    """
    create:

    Create work shifts

        {
            "name": "WorkShift Name",
            "start_time_grace": "00:10:00", // Grace time in punch in
            "end_time_grace": "00:10:00", // Grace time for punch out
            "work_days": [
                {
                    "day": 1,
                    // Week days index starting from 1 up to 7
                    "timings": [
                        {
                            "start_time": "10:00",
                            "end_time": "18:00",
                            "extends": true/false // extends over night
                        }, ...
                    ]
                }, ...
            ]
        }

    """
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ("name",)
    filter_fields = ('is_default',)
    ordering_fields = ["name", "start_time_grace", "end_time_grace", "modified_at"]
    ordering = "name"
    serializer_class = WorkShiftSerializer
    queryset = WorkShift.objects.all()
    permission_classes = [AttendanceWorkShiftPermission]
    related_names = {
        'old_change_types',
        'new_change_types',
        'individual_shifts',
        'timesheets'
    }


class WorkTimingViewSet(
    OrganizationMixin,
    ListRetrieveViewSetMixin
):
    """
    list:

    List of work timing for given user

    -- filters

        user_id=user_ud
        date=YYYY/mm/dd

    default is today
    """
    serializer_class = WorkTimingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ("start_time", "end_time")
    permission_classes = [AttendanceWorkShiftPermission]

    def get_queryset(self):
        user = self.user
        date = self.request.query_params.get('date')
        if date:
            try:
                date_time = parser.parse(date)
            except (TypeError, ValueError):
                raise ValidationError(INVALID_DATE)
        else:
            date_time = timezone.now()

        day = get_weekday(date_time)
        if not user:
            return WorkTiming.objects.none()

        if not (
            hasattr(user, 'attendance_setting') and
            user.attendance_setting.work_shift
        ):
            raise ValidationError(
                "User has not attendance setting or shift assigned."
            )
        work_day = user.attendance_setting.work_shift.work_days \
            .today().filter(day=day).first()
        if not work_day:
            return WorkTiming.objects.none()
        return work_day.timings.all()

    @cached_property
    def user(self):
        user_id = self.request.query_params.get("user_id", None)
        organization = self.get_organization()
        if user_id:
            try:
                return USER.objects.get(
                    id=int(user_id),
                    detail__organization=organization
                )
            except (USER.DoesNotExist, TypeError):
                pass
        return None

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except ValidationError as e:
            return Response({"detail": e.detail}, 400)


class UserActiveWorkShiftViewSet(
    UserMixin,
    ListViewSetMixin
):
    """
    # Active Work shift info for user

    sample response


        {
            "shift": {
                "id": 3,
                "name": "Overnight Shift"
            },
            "timing": {
                "id": 10,
                "start_time": "20:00:00",
                "end_time": "04:00:00",
                "extends": true
            },
            "timesheet_for": "2019-05-20",
            "start_datetime": "2019-05-20T20:00:00+05:45",
            "end_datetime": "2019-05-21T04:00:00+05:45"
        }


    --> 404 will be raised if user is not found or user does not have an attendance setting

    --> `shift`, `timing`, `start_datetime` and `end_datetime` will be null for user whose shift is not assigned

    --> `timing`, `start_datetime` and `end_datetime` will be null if user does not have a shift that day
    """
    serializer_class = UserWorkTimingSerializer
    permission_classes = [UserActiveShiftPermission]

    def has_user_permission(self):
        return self.request.user == self.user

    def list(self, request, *args, **kwargs):
        attendance_setting = getattr(self.user, 'attendance_setting', None)
        if not attendance_setting:
            return Response(
                {'detail': "No attendance setting found for this user."},
                status=status.HTTP_404_NOT_FOUND
            )
        attendance_setting.force_prefetch_for_work_shift = True
        attendance_setting.force_prefetch_for_previous_day = True

        work_shift = attendance_setting.work_shift

        timing_info = get_timing_info(timezone.now(), work_shift)

        instance = DummyObject(
            shift=work_shift,
            timing=timing_info.get("timing"),
            timesheet_for=timing_info.get("date")
        )

        if instance.timing:
            instance.start_datetime = combine_aware(instance.timesheet_for,
                                                    instance.timing.start_time)
            instance.end_datetime = combine_aware(
                (instance.timesheet_for + timezone.timedelta(days=1)
                 if instance.timing.extends else instance.timesheet_for),
                instance.timing.end_time
            )

        serializer = self.get_serializer(instance=instance)
        return Response(serializer.data)


class WorkShiftLegendViewSet(
    OrganizationCommonsMixin,
    OrganizationMixin,
    ListCreateViewSetMixin
):
    """
    # Shift Legend Info

    sample response
        {
            "id": 12,
            "legend_color": "#9E9E9EFF",
            "legend_text": "MO",
            "shift":
                {
                    "id": 287,
                    "name": "Morning shift"
                }
        }


    Bulk update payload data
        [
          {
            "id": 12,
            "legend_color": "#9E9E9EFF",
            "legend_text": "MO",
            "shift": 287,
          },
          { ... }
        ]
"
    """
    serializer_class = WorkShiftLegendSerializer
    queryset = WorkShiftLegend.objects.all().select_related("shift")
    organization_field = "shift__organization"
    permission_classes = [AttendanceWorkShiftPermission]

    def get_serializer(self, *args, **kwargs):
        if "data" in kwargs:
            data = kwargs["data"]
            # check if many is required
            if isinstance(data, list):
                kwargs["many"] = True

        return super(WorkShiftLegendViewSet, self).get_serializer(*args, **kwargs)
