from django.db.models import Manager, Q

from irhrs.core.utils.common import get_today


class WorkDayManager(Manager):
    def applicable(self):
        return self.get_queryset().filter(
            Q(applicable_to__isnull=True) |
            Q(applicable_to__gte=get_today())
        )

    def today(self, day=None):
        filter = {'applicable_from__lte': get_today()}
        if day:
            filter.update({'day': day})
        return self.applicable().filter(**filter)
