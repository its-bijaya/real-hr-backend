from django.core.management import BaseCommand, call_command
from django.forms.utils import pretty_name

BLACK = "\u001b[30m"
RED = "\u001b[31m"
GREEN = "\u001b[32m"
YELLOW = "\u001b[33m"
BLUE = "\u001b[34m"
MAGENTA = "\u001b[35m"
CYAN = "\u001b[36m"
WHITE = "\u001b[37m"
RESET = "\u001b[0m"


def add_color(text, color):
    return color + text + RESET


def call_seeders(seeders, default_yes=False):
    proceed = default_yes or (input(
        add_color('Do you want to seed data (Y/N)\t', CYAN)).upper() == 'Y')
    if not proceed:
        return
    for ind, seed_info in enumerate(seeders):
        seed, require, *extra = seed_info
        options = extra[0] if extra else {}
        good_name = pretty_name(seed)
        hint = {
            'recommend': 'Recommended',
            'require': 'Required'
        }.get(require)
        proceed = default_yes or (input(
            add_color(
                str(ind + 1)
                + '. Do You want to '
                + good_name
                + f" ({hint}) "
                + ' (Y/N)\t',
                CYAN
            )
        ).upper() == 'Y')
        if proceed:
            call_command(seed, **options)


class Command(BaseCommand):
    help = "Initial Setup"

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help=''
        )

    def handle(self, *args, **options):
        default = options.get('no_input')
        call_seeders([
            ('setup_hrs_permissions', 'require'),
            ('create_user_groups', 'require'),
            ('seed_id_cards', 'require'),
            ('seed_initials', 'require'),
            ('seed_locations', 'require'),
            ('schedule_tasks', 'recommend', {'no_input': True}),
            ('seed_organization_commons', 'recommend'),
            ('seed_notification_templates', 'recommend'),
        ], default)
