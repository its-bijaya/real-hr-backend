from django.db.models import Count, Q
from rest_framework.fields import ReadOnlyField
from rest_framework.response import Response

from irhrs.attendance.api.v1.permissions import AttendanceWorkShiftPermission
from irhrs.attendance.constants import WORKDAY
from irhrs.attendance.models import WorkShift, TimeSheet
from irhrs.core.mixins.serializers import DummySerializer, create_dummy_serializer
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, OrganizationMixin
from irhrs.core.utils.common import get_today


class WorkShiftOverViewViewSet(OrganizationMixin, ListViewSetMixin):
    serializer_class = create_dummy_serializer({
            "work_shift": ReadOnlyField(source="name"),
            "total": ReadOnlyField(),
            "present": ReadOnlyField(),
            "id": ReadOnlyField()
        })
    permission_classes = [AttendanceWorkShiftPermission]

    def get_queryset(self):
        return WorkShift.objects.filter(organization=self.get_organization())

    def filter_queryset(self, queryset):
        today = get_today()
        queryset = queryset.annotate(
            total=Count(
                'timesheets',
                filter=Q(timesheets__timesheet_for=today)
            ),
            present=Count(
                'timesheets',
                filter=Q(timesheets__timesheet_for=today,
                         timesheets__is_present=True)
            )

        )
        return super().filter_queryset(queryset)

    def retrieve(self, request, **kwargs):
        shift = self.get_object()
        today = get_today()

        agg = TimeSheet.objects.filter(
            work_shift=shift,
            timesheet_for=today
        ).aggregate(
            total=Count("id"),
            present=Count("id", filter=Q(is_present=True)),
            absent=Count("id", filter=Q(
                is_present=False,
                coefficient=WORKDAY
            ))
        )
        data = {
            "total": agg.get("total"),
            "present": agg.get("present"),
            "absent": agg.get("absent"),
            "on_leave": 0
        }
        return Response(data)
