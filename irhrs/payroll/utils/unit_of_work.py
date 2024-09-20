from django.db.models import F, Sum, FloatField

from irhrs.core.constants.payroll import CONFIRMED
from irhrs.payroll.models import UnitOfWorkRequest


def get_unit_of_work_done(user, slot):
    return UnitOfWorkRequest.objects.filter(
            status=CONFIRMED,
            user=user,
            confirmed_on__gte=slot.get('start'),
            confirmed_on__lte=slot.get('end'),
        ).annotate(
            amount=F('rate__rate') * F('quantity')
        ).aggregate(
        sum=Sum('amount', output_field=FloatField())
    ).get('sum') or 0.0
