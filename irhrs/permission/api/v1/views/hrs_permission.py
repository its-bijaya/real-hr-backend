from irhrs.core.mixins.viewset_mixins import ListViewSetMixin
from irhrs.permission.api.v1.serializers.hrs_permission import \
    HRSPermissionSerializer
from irhrs.permission.models import HRSPermission
from irhrs.permission.permission_classes import GroupPermission


class HRSPermissionViewSet(ListViewSetMixin):
    """
    list:

    List of HRS permissions
    """
    queryset = HRSPermission.objects.all()
    serializer_class = HRSPermissionSerializer
    permission_classes = [GroupPermission]
    filter_fields = ["category"]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_common = self.request.query_params.get('common', 'false').lower() == 'true'
        if is_common:
            return queryset.filter(organization_specific=False)
        return queryset.filter(organization_specific=True)
