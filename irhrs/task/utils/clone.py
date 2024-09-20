"""@irhrs_docs"""
from copy import deepcopy

from django.contrib.contenttypes.models import ContentType

from irhrs.notification.models import Notification
from irhrs.task.constants import RESPONSIBLE_PERSON, OBSERVER
from irhrs.task.models.task import TaskCheckList, TaskAttachment


def task_disassociate(original_task_instance):
    original_task_instance.freeze = True
    original_task_instance.save(update_fields=['freeze'])
    for responsible_person in original_task_instance.task_associations.filter(
            association=RESPONSIBLE_PERSON
    )[1:]:

        task_instance = deepcopy(original_task_instance)
        task_instance.id = None
        task_instance.freeze = False
        task_instance.save()

        responsible_person.task = task_instance
        responsible_person.save()

        # now this responsible person belongs to a new task , so change the
        # notification URL that was generated previously
        content_type = ContentType.objects.get_for_model(responsible_person)
        Notification.objects.filter(
            action_content_type=content_type,
            action_object_id=responsible_person.id,
            recipient=responsible_person.user
        ).update(url=f'/user/task/my/{responsible_person.task.id}/detail')

        for observer in original_task_instance.task_associations.filter(
                association=OBSERVER
        ):
            observer.id = None
            observer.task = task_instance
            observer.save()
            core_tasks = list(observer.core_tasks.all())
            observer.core_tasks.add(*core_tasks)

        # checklist
        original_checklists = original_task_instance.task_checklists.all()
        check_list_objects = []
        for checklist in original_checklists:
            checklist.id = None
            checklist.task = task_instance
            checklist.completed_by = None
            checklist.completed_on = None
            check_list_objects.append(checklist)
        TaskCheckList.objects.bulk_create(check_list_objects)

        # attachments
        original_attachments = original_task_instance.task_attachments.all()
        attachment_objects = []
        for attachment in original_attachments:
            attachment.id = None
            attachment.task = task_instance
            attachment_objects.append(attachment)
        TaskAttachment.objects.bulk_create(attachment_objects)

    original_task_instance.freeze = False
    original_task_instance.save(update_fields=['freeze'])
