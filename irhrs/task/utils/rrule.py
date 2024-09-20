"""@irhrs_docs"""
from dateutil.rrule import rrulestr

from irhrs.task.models.task import RecurringTaskDate


def recurring_date_for_task(task, update=False):
    rule = task.recurring_rule
    first_run = task.recurring_first_run

    if update:
        deleted, _ = RecurringTaskDate.objects.filter(template=task,
                                                      created_task__isnull=True
                                                      ).delete()
        print("total deleted objects %d" % deleted)
    try:
        date_list = list(rrulestr(rule, dtstart=first_run))
    except (ValueError, AttributeError):
        date_list = []

    recurring_task = [RecurringTaskDate(recurring_at=date,
                                        template=task) for date in date_list]

    RecurringTaskDate.objects.bulk_create(recurring_task)
