"""
Test the system for necessary dependencies to be loaded.

"""
from django.apps import apps
from django.core.exceptions import FieldError
from django.core.management import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from irhrs.common.models import DocumentCategory, ReligionAndEthnicity, \
    HolidayCategory
from irhrs.core.constants.common import NOTIFICATION_TYPE_CHOICES
from irhrs.core.seeder import (
    DOCUMENT_CATEGORIES, INDUSTRIES, RELIGIONS, ETHNICITIES, EMPLOYMENT_STATUS,
    EMPLOYMENT_LEVEL, HOLIDAY_CATEGORIES
)
from irhrs.organization.models import (
    Organization, Industry, EmploymentStatus, EmploymentLevel
)
from irhrs.permission.constants.permissions import hrs_permissions
from irhrs.permission.models import HRSPermission

seeders = {
    'DOCUMENT_CATEGORIES': (DOCUMENT_CATEGORIES, DocumentCategory),
    'INDUSTRIES': (INDUSTRIES, Industry),
    'RELIGIONS': (RELIGIONS, ReligionAndEthnicity),
    'ETHNICITIES': (ETHNICITIES, ReligionAndEthnicity),
    'EMPLOYMENT_STATUS': (EMPLOYMENT_STATUS, EmploymentStatus),
    'EMPLOYMENT_LEVEL': (EMPLOYMENT_LEVEL, EmploymentLevel),
    'HOLIDAY_CATEGORIES': (HOLIDAY_CATEGORIES, HolidayCategory),
}

MINIMUM_APPS = [
    'irhrs.common',
    'irhrs.users',
    'irhrs.organization',
    'irhrs.document',
    'irhrs.notification',
    'irhrs.noticeboard',
    'irhrs.permission',
    'irhrs.help',
    'irhrs.hris',
    'irhrs.websocket'
]

CGREEN = '\33[32m'
CRED = '\33[31m'
CBOLD = '\33[1m'
CEND = '\33[0m'


class Command(BaseCommand):
    help = "Checks the system for necessary dependencies"

    def test_permissions(self):
        """
        Check if the permissions has been installed.
        :return:
        """
        permissions = [permissions for permissions in dir(hrs_permissions)
                       if not permissions.startswith("_")]
        permission_data = [x for x in [
            getattr(hrs_permissions, perm) for perm in permissions
        ] if isinstance(x, dict)]
        results = []
        for perm in permission_data:
            res = HRSPermission.objects.filter(
                **perm
            ).exists()
            results.append((perm.get('name'), res))
        for permission, installed in results:
            formatting = CGREEN + '[X]' if installed else CRED + '[ ]'
            print(formatting, permission + CEND)

    def test_notification_templates(self):
        templates = NOTIFICATION_TYPE_CHOICES
        for org in Organization.objects.all():
            results = []
            for val, display in templates:
                res = org.templates.filter(
                    template__type=val
                ).exists()
                results.append((display, res))
            print(f'For {org}')
            for name, installed in results:
                formatting = CGREEN + '[X]' if installed else CRED + '[ ]'
                print(formatting, name + CEND)

    def test_initials(self):
        """
        Test the following initials:
        * Industry Type
        * Document Categories
        * Religion and Ethnicities.
        :return:
        """
        for seeder, attrs in seeders.items():
            constants = attrs[0]
            model = attrs[1]
            try:
                installed = model.objects.filter(
                    name__in=constants
                ).count()
            except FieldError:
                installed = model.objects.filter(
                    title__in=constants
                ).count()
            total = len(constants)
            name = ' '.join(seeder.split('_')).title()
            formatting = CGREEN + '[X]' if total == installed else CRED + '[ ]'
            print(formatting, name + CEND)

    def test_basic_apps(self):
        for module in MINIMUM_APPS:
            installed = apps.is_installed(module)
            formatting = CGREEN + '[X]' if installed else CRED + '[ ]'
            print(formatting, module.split('.')[1].title() + CEND)

    def test_pending_migrations(self):
        executor = MigrationExecutor(connection)
        leaf_nodes = executor.loader.graph.leaf_nodes()
        for app, leaf_node in leaf_nodes:
            pending_migrations = len(executor.migration_plan([(app,
                                                               leaf_node)]))
            formatting = CGREEN + '[X]' if pending_migrations == 0 else CRED \
                                                                        + '[ ]'
            print(formatting, app.title() + CEND)

    def handle(self, *args, **options):

        delim = '*' * 20

        print(CBOLD + CGREEN + delim + 'Testing Migrations' + delim + CEND)
        self.test_pending_migrations()
        print('\n\n')
        print(CBOLD + CGREEN + delim + 'Testing Permissions' + delim + CEND)
        self.test_permissions()
        print('\n\n')

        print(CBOLD + CGREEN + delim + 'Testing Notification Templates'
              + delim + CEND)
        self.test_notification_templates()
        print('\n\n')

        print(CBOLD + CGREEN + delim + 'Testing Initials' + delim + CEND)
        self.test_initials()
        print('\n\n')

        print(
            CBOLD + CGREEN + delim + 'Testing Basic Apps Installed' + delim
            + CEND
        )
        self.test_basic_apps()
        print('\n\n')
