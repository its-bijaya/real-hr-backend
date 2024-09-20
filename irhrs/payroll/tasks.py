from django.contrib.auth import get_user_model

from irhrs.core.utils.common import get_today
from irhrs.payroll.api.v1.serializers.package_activity import PayrollPackageActivitySerializer
from irhrs.payroll.api.v1.serializers.payroll_increment import PayrollIncrementSerializer
from irhrs.payroll.models import PayrollIncrement, UserExperiencePackageSlot, Package, \
    CLONED_PACKAGE, CREATED_PACKAGE, UPDATED_PACKAGE, ASSIGNED, \
    UNASSIGNED, PACKAGE_DELETED
from irhrs.payroll.utils.calculator import create_package_rows

USER = get_user_model()


def update_package_salary():
    """
    Update package rows on payroll increment day
    """
    today = get_today()
    changed_user_ids = set(
        PayrollIncrement.objects.filter(effective_from=today).values_list('employee_id', flat=True)
    )
    user_qs = USER.objects.filter(id__in=changed_user_ids).current()
    for user in user_qs:
        PayrollIncrementSerializer.recalibrate_package_amount_after_increment_update(user)


def create_package_activity(title: str, package: Package, action, *args, **kwargs):

    activity_data = {
        'action': action,
        'package': package.id,
        'organization': package.organization.id,
        'assigned_to': kwargs.get('assigned_to').id if kwargs.get('assigned_to') else None,
        'title': title
    }

    create_serializer = PayrollPackageActivitySerializer(data=activity_data)
    create_serializer.is_valid(raise_exception=True)

    create_serializer.save()
