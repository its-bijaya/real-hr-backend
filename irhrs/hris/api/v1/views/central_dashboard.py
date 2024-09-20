from django.db.models import Count, Q
from rest_framework.response import Response

from irhrs.common.api.permission import CentralDashboardPermission
from irhrs.core.constants.user import PENDING, APPROVED, REJECTED
from irhrs.core.utils.dashboard.central_dashboard import CentralDashboardMixin
from irhrs.hris.api.v1.views.statistics import HRISStatisticMixin
from irhrs.organization.models import Organization
from irhrs.users.models import ChangeRequest
from irhrs.websocket.consumers.global_consumer import UserOnline


class HRISDashboardViewSet(HRISStatisticMixin, CentralDashboardMixin):
    permission_classes = [CentralDashboardPermission]

    def get_queryset(self):
        return Organization.objects.filter(
            id__in=self.request.user.switchable_organizations_pks
        ).select_related("contract_settings")

    def list(self, request, *args, **kwargs):
        org_list = self.get_queryset()
        response = []
        for org in org_list:
            online_employees = UserOnline.all_active_user_ids()
            aggregate_data = self.get_user_queryset(org).aggregate(
                online_count=Count(
                    "id",
                    filter=Q(id__in=online_employees),
                    distinct=True
                ),
                total=Count(
                    "id",
                    distinct=True
                )
            )

            total = aggregate_data.get('total')
            active = aggregate_data.get('online_count')

            change_request = ChangeRequest.objects.filter(
                user__user_experiences__is_current=True,
                user__detail__organization=org
            ).aggregate(
                all=Count("id", distinct=True),
                pending=Count(
                    "id",
                    filter=Q(status=PENDING),
                    distinct=True
                ),
                approved=Count(
                    "id",
                    filter=Q(status=APPROVED),
                    distinct=True
                ),
                rejected=Count(
                    "id",
                    filter=Q(status=REJECTED),
                    distinct=True
                )

            )
            response.append(
                    {
                        "organization": {
                            "name": org.name,
                            "slug": org.slug,
                            "abbreviation": org.abbreviation
                        },
                        "hris": {
                            "All": total,
                            "Active": active,
                            "Inactive": total - active,
                            "Incomplete":
                                self.get_incomplete_profiles_queryset(
                                    self.get_user_queryset(org)).count(),
                            "Critical_contracts":
                                self.get_critical_contracts_queryset(org,
                                                                     self.get_user_queryset(org)).count()
                        },
                        "change_request": {
                            "Total": change_request.get('all'),
                            "Pending": change_request.get('pending'),
                            "Approved": change_request.get('approved'),
                            "Rejected": change_request.get('rejected')

                        }

                    }
            )
        return Response(response)
