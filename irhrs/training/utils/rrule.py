from irhrs.core.utils.recurring import create_recurring_date
from irhrs.training.models import RecurringTrainingDate


def recurring_date_for_training(training, update=False):
    return create_recurring_date(
        instance=training,
        model=RecurringTrainingDate,
        filters=dict(template=training, created_training__isnull=True),
        update=update
    )
