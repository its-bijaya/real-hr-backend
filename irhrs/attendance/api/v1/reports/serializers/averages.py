from django.db import models
from django.db.models.functions import Cast
from django.utils import timezone
from rest_framework.response import Response

from irhrs.attendance.models import TimeSheet
from irhrs.attendance.utils.attendance import get_week
from irhrs.core.mixins.viewset_mixins import (
    ListViewSetMixin, OrganizationMixin
)


class WorkHoursAverageViewSet(OrganizationMixin, ListViewSetMixin):
    queryset = TimeSheet.objects.all()
    filter_fields = ('work_shift',)

    def get_queryset(self):
        return super().get_queryset().filter(
            timesheet_user__detail__organization=self.get_organization()
        )

    def list(self, request, *args, **kwargs):
        week_start_date, week_end_date = get_week(timezone.now())
        qs = self.filter_queryset(self.get_queryset()).filter(
            timesheet_for__gte=week_start_date,
            timesheet_for__lte=week_end_date
        )
        qs = qs.order_by().values(
            'work_shift__work_days__day'
        ).annotate(
            average_punch_in=models.Avg(Cast('punch_in', models.TimeField())),
            average_punch_out=models.Avg(Cast('punch_out', models.TimeField())),
            average_working=models.Avg(
                Cast(
                    'punch_out', models.TimeField()
                ) - Cast(
                    'punch_in', models.TimeField())
            )
        )
        response = []
        for result in qs:
            json = {
                'work_day': result['work_shift__work_days__day'],
                'average_punch_in': result['average_punch_in'],
                'average_punch_out': result['average_punch_out'],
                'average_working': result['average_working']
            }
            response.append(json)
        return Response(response)
