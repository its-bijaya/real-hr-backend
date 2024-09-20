from django.db.models import Manager, Q

from irhrs.task.constants import RESPONSIBLE_PERSON, OBSERVER


class TaskManager(Manager):

    def base(self):
        return self.filter(
            Q(deleted_at__isnull=True) &
            (Q(recurring_rule__isnull=True) | Q(recurring_rule__iexact=''))
        )

    def recurring(self, user):
        return self.filter(
            Q(deleted_at__isnull=True) &
            Q(created_by=user) &
            Q(recurring_rule__isnull=False)
        )

    def my_tasks(self, user):
        return self.base().filter(
            (Q(created_by=user) |
             Q(task_associations__user=user))
        ).distinct()

    def as_creator(self, user):
        return self.base().filter(
            Q(created_by=user)
        )

    def as_responsible(self, user):
        return self.base().filter(
            Q(task_associations__user=user) & Q(
                task_associations__association=RESPONSIBLE_PERSON)
        )

    def as_observer(self, user):
        return self.base().filter(
            Q(task_associations__user=user) & Q(
                task_associations__association=OBSERVER)
        )

    def as_supervisor(self, user):
        subordinates_pks = user.subordinates_pks
        return self.base().filter(
            (Q(created_by_id__in=subordinates_pks) |
             Q(task_associations__user_id__in=subordinates_pks)
             )
        ).distinct()
