from django.contrib.auth import get_user_model

from irhrs.task.models.task import RecurringTaskDate

USER = get_user_model()


def stop_recurring_task_for_offboarded_employee():
    users = USER.objects.filter(
        is_active=False,
        is_blocked=True,
        detail__last_working_date__isnull=False,
    )
    stop_task_for_offboarded_user = []

    for user in users:
        recurring_task = RecurringTaskDate.objects.filter(
            template__deleted_at__isnull=True,
            template__created_by=user,
            template__recurring_rule__isnull=False,
            recurring_at__gte=user.detail.last_working_date
        )
        if recurring_task:
            stop_task_for_offboarded_user.append(user.id)
        recurring_task.delete()

    if stop_task_for_offboarded_user:
        print("Recurring task stopped for following users: ")
        print(stop_task_for_offboarded_user)
