from django.db.models import Count, Q
from rest_framework.response import Response

from irhrs.common.api.permission import CentralDashboardPermission
from irhrs.core.utils.common import apply_filters
from irhrs.core.utils.dashboard.central_dashboard import CentralDashboardMixin
from irhrs.leave.api.v1.reports.views.overview_summary import LeaveOverViewSummaryMixin
from irhrs.leave.constants.model_constants import REQUESTED, FORWARDED, APPROVED, DENIED
from irhrs.leave.models import LeaveRequest
from irhrs.organization.models import Organization


class LeaveDashboardViewSet(LeaveOverViewSummaryMixin, CentralDashboardMixin):
    permission_classes = [CentralDashboardPermission]

    def get_queryset(self):
        return Organization.objects.filter(
            id__in=self.request.user.switchable_organizations_pks
        )

    def list(self, request, *args, **kwargs):
        org_list = self.get_queryset()
        response = []
        filter_map = {
            'start_date': 'end__date__gte',
            'end_date': 'start__date__lte'
        }

        for org in org_list:
            queryset = LeaveRequest.objects.filter(
                user__detail__organization=org,
            )
            queryset = apply_filters(self.request.query_params, filter_map, queryset)
            leave_request = queryset.aggregate(
                all=Count("id", distinct=True),
                requested=Count(
                    "id",
                    filter=Q(status=REQUESTED),
                    distinct=True
                ),
                forwarded=Count(
                    "id",
                    filter=Q(status=FORWARDED),
                    distinct=True
                ),
                approved=Count(
                    "id",
                    filter=Q(status=APPROVED),
                    distinct=True
                ),
                denied=Count(
                    "id",
                    filter=Q(status=DENIED),
                    distinct=True
                ),
            )

            response.append(
                {
                    "organization": {
                        "name": org.name,
                        "slug": org.slug,
                        "abbreviation": org.abbreviation
                    },
                    "leave": {
                        "total": self.get_user_queryset(org).distinct().count(),
                        "present": self.get_present_qs(org),
                        "on_leave": self.get_on_leave_qs(org)
                    },
                    "leave_request": {
                        "All": leave_request.get('all'),
                        "Requested": leave_request.get('requested'),
                        "Approved": leave_request.get('approved'),
                        "Forwarded": leave_request.get('forwarded'),
                        "Denied": leave_request.get('denied')
                    }
                }
            )
        return Response(response)
