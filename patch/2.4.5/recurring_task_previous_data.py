from django.db import transaction

from irhrs.task.models.task import (TaskAssociation, Task,
                                    RecurringTaskDate, MAX_LIMIT_OF_TASK_SCORING_CYCLE)


def recurring_task_previous_data():
    with transaction.atomic():
        tasks = Task.objects.filter(
            recurring_rule__isnull=False,
        )
        queued_recurring_tasks = RecurringTaskDate.objects.filter(
            template__in=tasks
        ).values_list('created_task', flat=True)
        task_associations = TaskAssociation.objects.filter(task__in=queued_recurring_tasks)
        ta_count = task_associations.count()
        _tasks = []
        if ta_count > 0:
            print('*** Recalculating Cycle Status ***')
            for ta in task_associations:
                if not ta.task.approved:
                    cycle_status = 'Approval Pending'
                total_cycle = ta.taskverificationscore_set.count()
                if total_cycle < 1:
                    cycle_status = 'Score Not Provided'
                elif ta.taskverificationscore_set.filter(
                        ack__isnull=True).exists():
                    cycle_status = 'Acknowledge Pending'
                elif ta.taskverificationscore_set.filter(ack=True).exists():
                    cycle_status = 'Acknowledged'
                elif total_cycle == MAX_LIMIT_OF_TASK_SCORING_CYCLE:
                    cycle_status = 'Forwarded To HR'
                elif total_cycle > MAX_LIMIT_OF_TASK_SCORING_CYCLE:
                    cycle_status = 'Approved By HR'
                else:
                    cycle_status = 'Not Acknowledged'
                if ta.cycle_status != cycle_status:
                    ta.cycle_status = cycle_status
                    ta.save()
                    _tasks.append(ta.task.id)

        print(f'Affected Tasks are: {_tasks}')
