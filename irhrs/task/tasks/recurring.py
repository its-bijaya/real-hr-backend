from copy import deepcopy

from django.contrib.auth import get_user_model
from django.utils import timezone

from irhrs.task.constants import PENDING, RESPONSIBLE_PERSON, APPROVAL_PENDING
from ..models.task import RecurringTaskDate, TaskCheckList, TaskAttachment


def create_recurring_task():
    # TODO @Shital, write unittest for `create_recurring_task`
    total_recurring_queue = RecurringTaskDate.objects.filter(
        created_task__isnull=True, recurring_at=timezone.now().date()
    )
    for recurring_date in total_recurring_queue:
        recurring_template_associations = recurring_date.template.task_associations.all()
        # more simpler logic and redundant code can be removed
        if not get_user_model().objects.filter(
                id__in=list(recurring_template_associations.filter(
                    association=RESPONSIBLE_PERSON).values_list(
                    'user_id', flat=True)
                )).current().count() > 0:
            continue

        created_task = deepcopy(recurring_date.template)

        created_task.id = None
        created_task.recurring_rule = None
        created_task.recurring_first_run = None
        created_task.status = PENDING
        created_task.approved = False
        created_task.approved_at = None

        # change modifier of the template task to the creator
        # because during the template lifetime , it could have been modified by any other
        created_task.modified_by = created_task.created_by
        created_task.deleted_at = None  # Need to work our for this condition .
        # this should be done by
        #   1. get today's date from timezone.now
        #   2. combine time of t.start_at to the todays date (Think about the timezone)
        #   3. then perform , combined_date + (t.stat_at - t.deadline)
        # but for now , this should work
        created_task.deadline = timezone.now() + (
                created_task.deadline - created_task.starts_at)
        created_task.starts_at = timezone.now()
        created_task.save()

        recurring_date.created_task = created_task
        recurring_date.last_tried = timezone.now()
        recurring_date.save()

        # associations
        for association in recurring_template_associations:
            # more simpler logic and redundant code can be removed
            if not get_user_model().objects.filter(
                    id=association.user_id).current().exists():
                continue
            assoc = deepcopy(association)
            assoc.id = None
            assoc.task = created_task
            assoc.cycle_status = APPROVAL_PENDING
            assoc.score = None
            assoc.remarks = None
            assoc.save()
            core_tasks = list(association.core_tasks.all())
            assoc.core_tasks.add(*core_tasks)

        # checklist
        recurring_template_checklists = recurring_date.template.task_checklists.all()
        check_list_objects = []
        for checklist in recurring_template_checklists:
            _obj = deepcopy(checklist)
            _obj.id = None
            _obj.task = created_task
            _obj.completed_by = None
            _obj.completed_on = None
            check_list_objects.append(_obj)
        TaskCheckList.objects.bulk_create(check_list_objects)

        # attachments
        recurring_template_attachments = recurring_date.template.task_attachments.all()
        attachment_objects = []
        for attachment in recurring_template_attachments:
            _obj = deepcopy(attachment)
            _obj.id = None
            _obj.task = created_task
            attachment_objects.append(_obj)
        TaskAttachment.objects.bulk_create(attachment_objects)
