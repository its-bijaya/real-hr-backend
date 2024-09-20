from copy import deepcopy

from django.utils import timezone

from irhrs.task.constants import PENDING
from ..models import RecurringTrainingDate


def create_recurring_training():
    # TODO @Shital, write unittest for `create_recurring_task`
    total_recurring_queue = RecurringTrainingDate.objects.filter(
        created_training__isnull=True,
        recurring_at=timezone.now().date()
    )

    for recurring_date in total_recurring_queue:
        template_training = recurring_date.template

        created_training = deepcopy(template_training)
        created_training.id = None
        created_training.start = timezone.now()
        created_training.end = timezone.now() + (
            created_training.end - created_training.start
        )
        created_training.status = PENDING
        created_training.save()

        user_training = recurring_date.user_trainings.all()
        for user in user_training:
            _obj = deepcopy(user)
            _obj.id = None
            _obj.start = timezone.now()
            _obj.save()
