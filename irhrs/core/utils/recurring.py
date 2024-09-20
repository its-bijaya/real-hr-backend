from dateutil.rrule import rrulestr


def create_recurring_date(instance, model, filters, update=False):
    """
    To implement this utils you must have some fields in  your recurring model.
    Some of them are listed below:
        ...
        recurring_at = models.DateField()
        template = models.ForeignKey( ... )
        created_{template_related_to} = models.OneToOne( ... )
        ...
    for more info visit RecurringTrainingDate() model

    :param instance: instance of template
    :param model: Class of model on which your are implementing this logic
        example:
            model=RecurringTrainingDate

        while implementing this logic for RecurringTrainingDate() model

    :param filters: dict
        example:
            filters = {
                'template': task,
                'created_task__isnull': True
            }

    :param update: bool
    :return:
    """

    rule = instance.recurring_rule
    first_run = instance.recurring_first_run

    if update:
        deleted, _ = model.objects.filter(
            **filters
        ).delete()
        print("total deleted objects %d" % deleted)
    try:
        date_list = list(rrulestr(rule, dtstart=first_run))
    except (ValueError, AttributeError):
        date_list = []

    recurring_instance = [model(recurring_at=date, template=instance) for date in date_list]

    model.objects.bulk_create(recurring_instance)
