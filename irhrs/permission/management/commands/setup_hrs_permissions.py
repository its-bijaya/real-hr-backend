from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand

from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.models.hrs_permisssion import OrganizationGroup
from ...models import HRSPermission

from irhrs.permission.constants.permissions import hrs_permissions\
    as permissions_module


# exclude builtins from module
permissions = [permissions for permissions in dir(permissions_module)
               if not permissions.startswith("_")]

C_GREEN = '\33[32m'
C_RED = '\33[31m'
C_BOLD = '\33[1m'
C_END = '\33[0m'


class Command(BaseCommand):
    help = "Create permissions for the system."

    def handle(self, *args, **kwargs):
        print(C_GREEN + C_BOLD + "Creating permissions ..." + C_END)
        permission_objects = []
        code = set()
        created = ignored = list()
        for permission in permissions:
            data = getattr(permissions_module, permission)
            if not isinstance(data, dict):
                continue
            permission_name = data.get("name")
            get_code = data.get("code")
            code.add(get_code)
            updated_permission = self.update_permission_data(get_code, data)
            if not updated_permission:
                obj = HRSPermission(**data)
                try:
                    obj.full_clean()
                    permission_objects.append(obj)
                    created.append(permission_name)
                except ValidationError as e:
                    ignored.append(permission_name)

        print(
            C_GREEN
            + 'Created Permission List: '
            + '\n'.join([x.name for x in permission_objects])
            + C_END
        )
        self.remove_permission(code)
        objs = HRSPermission.objects.bulk_create(permission_objects)

        # Grant admin all the created permissions
        admin, _created = Group.objects.get_or_create(name=ADMIN)

        # add in org groups
        for og in OrganizationGroup.objects.filter(
            group=admin
        ):
            og.permissions.add(*objs)

    @staticmethod
    def remove_permission(code):
        print(C_RED + C_BOLD + "Removing permissions ..." + C_END)
        get_database_code = set(HRSPermission.objects.values_list('code', flat=True))
        remove_code = get_database_code - code
        print(
            C_RED
            + 'Deleted Permission Code: '
            + '\n'.join([x for x in remove_code])
            + C_END
        )
        HRSPermission.objects.filter(code__in=list(remove_code)).delete()

    @staticmethod
    def update_permission_data(code, data):
        print(C_GREEN + C_BOLD + "Updating permissions ..." + C_END)
        try:
            permission_data = HRSPermission.objects.get(code=code)

        except HRSPermission.DoesNotExist:
            return False

        permission_data.name = data.get('name')
        permission_data.organization_specific = data.get('organization_specific')
        permission_data.description = data.get('description') if data.get(
            'description') else ''
        permission_data.category = data.get('category')
        permission_data.save()
        print(
            C_GREEN
            + 'Updated Permission: '
            + f'{permission_data.name}'
            + C_END
        )
        return True
