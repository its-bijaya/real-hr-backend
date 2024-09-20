from django.db.models import Sum

from irhrs.leave.constants.model_constants import APPROVED, LEAVE_RENEW, HOURLY_LEAVE_CATEGORIES, \
    EMPLOYEE_SEPARATION
from irhrs.leave.models.account import LeaveEncashment

from irhrs.payroll.internal_plugins.registry import register_plugin


@register_plugin('employee-leave-encashment-from-renew')
def leave_encashment_from_renew(calculator, package_heading):
    """
    Leave Encashment On Renew
    """

    employee = calculator.employee
    from_date = calculator.from_date
    to_date = calculator.to_date

    queryset = LeaveEncashment.objects.filter(
        user=employee,
        status=APPROVED,
        approved_on__gte=from_date,
        approved_on__lte=to_date,
        source=LEAVE_RENEW
    ).exclude(account__rule__leave_type__category__in=HOURLY_LEAVE_CATEGORIES)

    encashed_days = queryset.aggregate(
        total_balance=Sum('balance')
    )['total_balance'] or 0.0
    sources = [
        {'model_name': 'LeaveEncashment', 'instance_id': pk, 'url': ''}
        for pk in queryset.values_list('pk', flat=True)
    ]
    return encashed_days, sources


@register_plugin('employee-leave-encashment-from-off-boarding')
def leave_encashment_from_off_boarding(calculator, package_heading):
    """
    Leave Encashment On Off boarding
    """

    employee = calculator.employee
    from_date = calculator.from_date
    to_date = calculator.to_date

    if not (
        employee.detail.last_working_date and
        from_date <= employee.detail.last_working_date <= to_date
    ):
        return 0, []
    queryset = LeaveEncashment.objects.filter(
        user=employee,
        status=APPROVED,
        source=EMPLOYEE_SEPARATION
    ).exclude(account__rule__leave_type__category__in=HOURLY_LEAVE_CATEGORIES)

    encashed_days = queryset.aggregate(
        total_balance=Sum('balance')
    )['total_balance'] or 0.0
    sources = [
        {'model_name': 'LeaveEncashment', 'instance_id': pk, 'url': ''}
        for pk in queryset.values_list('pk', flat=True)
    ]
    return encashed_days, sources
