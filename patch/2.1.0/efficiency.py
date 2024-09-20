from decimal import Decimal

from irhrs.task.constants import COMPLETED, CRITICAL, MAJOR, RESPONSIBLE_PERSON
from irhrs.task.models import Task


# Recalculate Efficiency
def recalculate_efficiency():
    total_completed_task = Task.objects.filter(status=COMPLETED, approved=True)

    for task in total_completed_task:
        priority_rate = 60.0 if task.priority == CRITICAL else 30.0 if task.priority == MAJOR else 10.0
        delayed_status_rate = 100.0
        if task.is_delayed:
            delay_time = task.finish - task.deadline
            if delay_time.days < 1:
                deductions = 0.0
            elif 1 >= delay_time.days <= 10:
                deductions = delay_time.days * 10.0
            else:
                deductions = 100.0
            delayed_status_rate -= deductions
        for assoc in task.task_associations.filter(
                association=RESPONSIBLE_PERSON):
            p = priority_rate * 0.10
            d = delayed_status_rate * 0.30
            s = (assoc.score * 10.0 * 0.60) if assoc.score else 0.0
            assoc.efficiency_from_priority = Decimal("%.2f" % p)
            assoc.efficiency_from_timely = Decimal("%.2f" % d)
            assoc.efficiency_from_score = Decimal("%.2f" % s)
            assoc.efficiency = Decimal("%.2f" % (assoc.efficiency_from_priority
                                                 + assoc.efficiency_from_timely
                                                 + assoc.efficiency_from_score))
            assoc.save(update_fields=['efficiency',
                                      'efficiency_from_priority',
                                      'efficiency_from_timely',
                                      'efficiency_from_score'])
