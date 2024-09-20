from irhrs.core.utils import get_system_admin
from irhrs.notification.models import Notification
from irhrs.task.models.task import TaskActivity, TaskComment, Task, TaskAssociation


def fix_model(model_class, field, name):
    admin = get_system_admin()
    broken_items = model_class.objects.filter(**{f"{field}__isnull": True})
    print(f"Found {broken_items.count()} broken {name}.")
    broken_items.update(**{field: admin})
    print(f"Updated broken {name}.")


def apply_patch():
    model_field_name = (
        (Task, 'created_by', 'task'),
        (TaskAssociation, 'created_by', 'task association'),
        (TaskActivity, 'created_by', 'task activity'),
        (TaskComment, 'created_by', 'task comment.'),
        (Notification, 'actor', 'notification')
    )
    for model, field, name in model_field_name:
        fix_model(model, field, name)
