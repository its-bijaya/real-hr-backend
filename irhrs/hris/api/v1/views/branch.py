from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from irhrs.core.mixins.viewset_mixins import OrganizationMixin, ListViewSetMixin
from irhrs.hris.api.v1.permissions import HRISPermission, HRISReportPermission
from irhrs.hris.api.v1.serializers.division_overview import \
    DivisionOverviewSerializer
from irhrs.organization.models import OrganizationBranch


class BranchOverView(OrganizationMixin, ListViewSetMixin):
    """
    list:
    employee list

    For filters refer to drf browsable api
    for date range filters send 'start_date' and 'end_date'
    on `yyyy-mm-dd` format.
    """
    serializer_class = DivisionOverviewSerializer  # same fields so reused
    permission_classes = [HRISReportPermission]
    filter_backends = (DjangoFilterBackend, )
    filter_fields = ('is_archived',)

    def get_queryset(self):
        return OrganizationBranch.objects.filter(
            organization=self.get_organization()).annotate(
            count=Count(
                'user_experiences',
                filter=Q(user_experiences__is_current=True)
            )
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get(
            'end_date', str(timezone.now().date()))

        if start_date:
            try:
                queryset = queryset.filter(
                    user_experiences__user__detail__joined_date__gte=start_date,
                    user_experiences__user__detail__joined_date__lte=end_date,
                    user_experiences__is_current=True
                )
            except (TypeError, ValidationError):
                # invalid date format
                pass

        return queryset

    @staticmethod
    def has_user_permission():
        return False
