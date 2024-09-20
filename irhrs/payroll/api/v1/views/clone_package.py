from irhrs.core.mixins.viewset_mixins import CreateViewSetMixin, OrganizationMixin, OrganizationCommonsMixin
from irhrs.payroll.api.v1.serializers.clone_package import PackageCloneSerializer
from irhrs.payroll.models import Package
from irhrs.permission.constants.permissions import WRITE_PAYROLL_PACKAGE_HEADINGS_PERMISSION
from irhrs.permission.permission_classes import permission_factory


class ClonePackageViewSet(
    OrganizationMixin,
    OrganizationCommonsMixin,
    CreateViewSetMixin
):

    serializer_class = PackageCloneSerializer
    queryset = Package.objects.all()
    permission_classes = [
        permission_factory.build_permission(
            "PayrollPackageClonePermission",
            allowed_to=[WRITE_PAYROLL_PACKAGE_HEADINGS_PERMISSION],
        )
    ]
