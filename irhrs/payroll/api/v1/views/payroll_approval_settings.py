from irhrs.core.mixins.viewset_mixins import OrganizationCommonsMixin, \
    OrganizationMixin, ListCreateViewSetMixin
from irhrs.payroll.api.v1.serializers.payroll_approval_settings import \
    PayrollApprovalSettingsCreateSerializer, PayrollApprovalSettingsSerializer
from irhrs.payroll.models import PayrollApprovalSetting
from irhrs.permission.constants.permissions import ALL_PAYROLL_PERMISSIONS, \
    PAYROLL_SETTINGS_PERMISSION, GENERATE_PAYROLL_PERMISSION
from irhrs.permission.permission_classes import permission_factory


class PayrollApprovalSettingsViewSet(
    OrganizationCommonsMixin,
    OrganizationMixin,
    ListCreateViewSetMixin
):
    serializer_class = PayrollApprovalSettingsSerializer
    queryset = PayrollApprovalSetting.objects.all()
    permission_classes = [
        permission_factory.build_permission(
            "PayrollApprovalSetttingPermission",
            limit_read_to=[
                ALL_PAYROLL_PERMISSIONS,
                PAYROLL_SETTINGS_PERMISSION,
                GENERATE_PAYROLL_PERMISSION
            ],
            limit_write_to=[ALL_PAYROLL_PERMISSIONS, PAYROLL_SETTINGS_PERMISSION]
        )
    ]

    def get_serializer_class(self):
        if self.action == 'create':
            return PayrollApprovalSettingsCreateSerializer
        return super().get_serializer_class()

