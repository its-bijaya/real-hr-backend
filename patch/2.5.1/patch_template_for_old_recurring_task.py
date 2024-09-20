"""
This patch sets approved value to False if training templates has already been approved.

This issue is raised due to old implementation of recurring task. Where template it self runs
through a task cycle ( from assign to user to complete).
"""
from irhrs.task.models import Task


def patch_template_for_old_recurring_task():
    tasks = Task.objects.filter(
        recurring_rule__isnull=False,
        approved=True
    )

    updated_tasks = list(tasks.values('id', 'created_by'))
    print("\nStopped Recurring Task Template: \n", updated_tasks)
    # task.update(approved=False, approved_at=None)
    for task in tasks:
        task.recurring_task_queue.filter(created_task__isnull=True).delete()
