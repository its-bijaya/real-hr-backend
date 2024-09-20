from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import OrganizationMixin, OrganizationCommonsMixin
from irhrs.core.utils.common import get_today
from irhrs.payroll.api.v1.serializers.payroll_increment import PayrollIncrementSerializer
from irhrs.payroll.models import PayrollIncrement, UserExperiencePackageSlot
from irhrs.payroll.utils.calculator import create_package_rows
from irhrs.payroll.utils.helpers import get_last_payroll_generated_date
from irhrs.permission.constants.permissions import WRITE_PAYROLL_PACKAGE_HEADINGS_PERMISSION, \
    ALL_PAYROLL_PERMISSIONS
from irhrs.permission.permission_classes import permission_factory


class PayrollIncrementViewSet(OrganizationCommonsMixin, OrganizationMixin, ModelViewSet):
    queryset = PayrollIncrement.objects.all()
    organization_field = 'employee__detail__organization'
    serializer_class = PayrollIncrementSerializer
    permission_classes = [
        permission_factory.build_permission(
            "PayrollIncrementViewSet",
            allowed_to=[
                ALL_PAYROLL_PERMISSIONS,
                WRITE_PAYROLL_PACKAGE_HEADINGS_PERMISSION
            ]
        )
    ]

    def perform_destroy(self, instance):
        user = instance.employee
        last_payroll_generated_date = get_last_payroll_generated_date(user)

        if last_payroll_generated_date and last_payroll_generated_date >= instance.effective_from:
            raise self.permission_denied(self.request, "Increment used to generate payroll.")

        recalibrate = instance.effective_from <= get_today()
        super().perform_destroy(instance)

        if recalibrate:
            PayrollIncrementSerializer.recalibrate_package_amount_after_increment_update(user)




