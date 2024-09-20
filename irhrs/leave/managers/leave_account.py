from django.db.models import F, Manager
from django.db.models.functions import Coalesce


class LeaveAccountHistoryManager(Manager):
    def difference(self):
        return self.get_queryset().annotate(
            added=Coalesce(
                F('new_usable_balance') - F('previous_usable_balance'),
                0.0
            )
        )
