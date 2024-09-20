"""@irhrs_docs"""
from decimal import Decimal

from django.db.models import Subquery, OuterRef
from django.utils.timezone import now, timedelta

from irhrs.hris.models.onboarding_offboarding import TaskTemplateMapping
from irhrs.notification.models.notification import OrganizationNotification
from irhrs.notification.utils import notify_organization
from irhrs.permission.constants.permissions import TASK_PERMISSION, TASK_REPORT_PERMISSION, TASK_APPROVALS_PERMISSION
from irhrs.task.constants import CRITICAL, MAJOR
from ..models import Task
from ..models.task import TaskAssociation, TaskActivity


def get_all_descendants(task_id, include_self=False, unique_only=True):
    descendants = [task_id] if include_self else []
    task_lists = list(
        Task.objects.base().filter(
            parent_id=task_id
        ).values_list('id', flat=True)
    )
    if task_lists:
        for _t in task_lists:
            descendants.extend(get_all_descendants(_t, include_self=True))

    return list(set(descendants)) if unique_only else descendants


def get_all_ancestors(task_id, include_self=False):
    ancestors = [task_id] if include_self else []
    _task = Task.objects.base().filter(id=task_id).first()
    if _task and _task.parent_id:
        ancestors.extend(get_all_ancestors(_task.parent_id, include_self=True))
    return ancestors


def get_all_associations(task_list, include_creator=True, unique_only=True):
    associations = []
    associations.extend(list(
        TaskAssociation.objects.filter(
            task_id__in=task_list).values_list('user_id', flat=True))
    )
    if include_creator:
        associations.extend(list(
            Task.objects.base().filter(
                id__in=task_list).values_list(
                'created_by_id', flat=True)
        ))
    return list(set(associations)) if unique_only else associations


def notify_on_boarding_task() -> None:
    # Background task that filters all tasks within a 5-minute interval.
    five_minutes_before = (now() - timedelta(minutes=5)).replace(microsecond=0)
    latest_change = TaskActivity.objects.filter(
        task_id=OuterRef('pk')
    ).order_by('-created_at')[:1]
    onboarding_tasks_updated_within_five_minutes = Task.objects.filter(
        tasktemplatemapping__isnull=False
    ).annotate(
        last_status_change=Subquery(
            latest_change.values('created_at')
        )
    ).filter(
        last_status_change__gte=five_minutes_before
    )
    for task in onboarding_tasks_updated_within_five_minutes:
        organization = TaskTemplateMapping.objects.get(
            task=task
        ).template_detail.template.organization
        slug = organization.slug
        text = f'{task.modified_by} updated the task {task.title} to ' \
            f'{task.get_status_display()}'
        notify_organization(
            text=text,
            url=f'/admin/{slug}/task/{task.id}/detail',
            organization=organization,
            action=task,
            actor=task.modified_by,
            permissions=[
                TASK_PERMISSION,
                TASK_REPORT_PERMISSION,
                TASK_APPROVALS_PERMISSION
            ]
        )


def recalculate_efficiency(task, user, score_verification_instance):
    if isinstance(user, int) or isinstance(user, str):
        _kwargs = {'user_id': user}
    else:
        _kwargs = {'user': user}

    assoc = task.task_associations.get(
        **_kwargs
    )
    priority_rate = 60.0 if \
        task.priority == CRITICAL else 30.0 if \
        task.priority == MAJOR else 10.0
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
    p = priority_rate * 0.10
    d = delayed_status_rate * 0.30
    if score_verification_instance.score:
        s = score_verification_instance.score * 10.0 * 0.60
    else:
        s = 0.0
    assoc.efficiency_from_priority = Decimal("%.2f" % p)
    assoc.efficiency_from_timely = Decimal("%.2f" % d)
    assoc.efficiency_from_score = Decimal("%.2f" % s)
    assoc.efficiency = Decimal(
        "%.2f" % (assoc.efficiency_from_priority
                  + assoc.efficiency_from_timely
                  + assoc.efficiency_from_score))
    assoc.save(update_fields=['efficiency',
                              'efficiency_from_priority',
                              'efficiency_from_timely',
                              'efficiency_from_score'])
