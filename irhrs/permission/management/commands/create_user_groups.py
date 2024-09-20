from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand

from irhrs.permission.constants import groups as groups_module

group_objects = []

# exclude builtins from module
groups = [group for group in dir(groups_module) if not group.startswith("_")]


class Command(BaseCommand):
    help = "Create user groups required for the system"

    def handle(self, *args, **kwargs):
        print("Creating user groups ...")
        for group in groups:
            group_name = str(getattr(groups_module, group))
            obj = Group(name=group_name)
            try:
                obj.full_clean()
                group_objects.append(obj)
            except ValidationError as e:
                print(e.messages)
                print(f"Ignoring group {group_name}")

        for group in group_objects:
            # because bulk create does not dispatch `post_save`
            group.save()
        print("Created user groups")
