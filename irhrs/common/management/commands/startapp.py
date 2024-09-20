import os

from django.conf import settings
from django.core.management.templates import TemplateCommand

APPS_DIRECTORY = settings.APPS_DIR
TEMPLATE_BASE_DIR = 'scratch/app_template/'


class Command(TemplateCommand):
    help = (
        f"Creates a RealHr compatible app in {APPS_DIRECTORY}"
    )
    missing_args_message = "You must provide an App name."

    def handle(self, **options):
        app_name = options.pop('name')
        _ = options.pop('directory')
        print(f"Creating app {app_name}")
        target = os.path.join(APPS_DIRECTORY, app_name.lower())
        if not os.path.exists(target):
            os.mkdir(target)
        print(f"Installing app on {target}")
        options.update(
            {
                'template': TEMPLATE_BASE_DIR
            }
        )
        print(f"Creating.....")
        super().handle('app', app_name, target, **options)
        print("Successfully Created")
        print(f"**** Add irhrs.{app_name} "
              f"in PROJECT_APPS on config/settings/base.py ****")

#
# USE_DJANGO_DEFAULT_COMMAND = True
# if USE_DJANGO_DEFAULT_COMMAND:
#   from django.core.management.commands.startapp import Command as \
#   StartAppCommand
#   Command = StartAppCommand
