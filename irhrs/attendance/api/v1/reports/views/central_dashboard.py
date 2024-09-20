from rest_framework.response import Response

from irhrs.attendance.api.v1.reports.views.summary import AttendanceSummaryInformation
from irhrs.attendance.models import TravelAttendanceDays
from irhrs.common.api.permission import CentralDashboardPermission
from irhrs.core.utils.common import get_today
from irhrs.core.utils.dashboard.central_dashboard import CentralDashboardMixin
from irhrs.organization.models import Organization


class AttendanceDashboardViewSet(AttendanceSummaryInformation, CentralDashboardMixin):
    permission_classes = [CentralDashboardPermission]

    @staticmethod
    def get_user_on_field_visit(org):
        return len(set(
            TravelAttendanceDays.objects.filter(
                day=get_today(),
                user__detail__organization=org
            ).values_list('user', flat=True)
        ))

    def get_queryset(self):
        return Organization.objects.filter(
            id__in=self.request.user.switchable_organizations_pks
        )

    def list(self, request, *args, **kwargs):
        org_list = self.get_queryset()
        response = []

        for org in org_list:
            response.append(
                {
                    "organization": {
                        "name": org.name,
                        "slug": org.slug,
                        "abbreviation": org.abbreviation
                    },
                    "attendance": {
                        "total": self.get_user_queryset(org).distinct().count(),
                        "present": self.get_present(self.get_user_queryset(org)).count(),
                        "absent": self.get_absent(self.get_user_queryset(org)).count(),
                        "offday": self.get_offday(self.get_user_queryset(org)).count(),
                        "on_travel": self.get_user_on_field_visit(org)
                    }
                }
            )
        return Response(response)
