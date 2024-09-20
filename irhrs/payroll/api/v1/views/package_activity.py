from rest_framework.filters import SearchFilter, OrderingFilter

from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, OrganizationMixin, \
    OrganizationCommonsMixin
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.hris.api.v1.permissions import ViewPayrollReportPermission
from irhrs.payroll.api.v1.serializers.package_activity import PayrollPackageActivitySerializer
from irhrs.payroll.models import PayrollPackageActivity


class PayrollPackageActivityViewSet(OrganizationMixin, OrganizationCommonsMixin, ListViewSetMixin):
    serializer_class = PayrollPackageActivitySerializer
    permission_classes = [ViewPayrollReportPermission]
    queryset = PayrollPackageActivity.objects.all()
    filter_backends = (FilterMapBackend, SearchFilter, OrderingFilter,)
    ordering_fields = ('title', 'assigned_to', 'action')
    search_fields = ('title',)
    filter_map = {
        'assigned_to': 'assigned_to',
        'action': 'action',
        'package': 'package'
    }
