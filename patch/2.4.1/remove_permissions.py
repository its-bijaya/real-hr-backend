from django.core.management import call_command

from irhrs.permission.models import HRSPermission

HRSPermission.objects.all().delete()
call_command(
    'setup_hrs_permissions'
)
