from django.db.models import Count, Q

from irhrs.core.mixins.viewset_mixins import OrganizationMixin, ListViewSetMixin
from irhrs.core.utils.common import get_today
from irhrs.hris.api.v1.permissions import HRISPermission
from irhrs.hris.api.v1.serializers.division_overview import \
    DivisionOverviewSerializer
from irhrs.organization.models import OrganizationDivision


class DivisionOverView(OrganizationMixin, ListViewSetMixin):
    serializer_class = DivisionOverviewSerializer
    permission_classes = [HRISPermission]

    def get_queryset(self):
        return OrganizationDivision.objects.exclude(is_archived=True).filter(
            organization=self.get_organization()).annotate(
            count=Count(
                'user_experiences',
                filter=Q(user_experiences__is_current=True)
                       & Q(Q(user_experiences__end_date__isnull=True)
                       | Q(user_experiences__end_date__gte=get_today()))
            )
        ).order_by('-count')
