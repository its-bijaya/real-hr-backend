import getpass
from irhrs.organization.models.organization import OrganizationAppearance
import json

from django.contrib.auth.models import Group
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.db.models.signals import post_save

from irhrs.common.management.commands.seed_org_data import seed_default_data_for
from irhrs.core.constants.user import GENDER_CHOICES
from irhrs.core.constants.organization import ORGANIZATION_OWNERSHIP
from irhrs.organization.models import Organization, ContractSettings
from irhrs.organization.models import UserOrganization
from irhrs.organization.signals import create_organization_settings
from irhrs.permission.constants.groups import ADMIN
from irhrs.users.models import User, UserDetail
from irhrs.users.utils import get_default_date_of_birth

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


class Command(BaseCommand):
    help = "Initial Setup"
    fixture_path = None

    organization_fields = {
        'name': {
            'help_text': 'Name: ',
            'max_length': 255,
            'fixture_field': 'organization_name',
        },
        'abbreviation': {
            'help_text': 'Abbreviation: ',
            'max_length': 15,
            'fixture_field': 'organization_abbr',
        },
        'about': {
            'help_text': 'About Section: ',
            'max_length': None,
            'fixture_field': 'organization_about'
        },
        'ownership': {
            'help_text': 'Ownership',
            'choices': [value for value, display in ORGANIZATION_OWNERSHIP],
            'type': 'choice',
            'fixture_field': 'organization_ownership'
        }
    }

    user_fields = {
        "email": {
            'help_text': 'Email: ',
            'max_length': 255,
            'fixture_field': 'user_email'
        },
        "password": {
            'help_text': 'Password: ',
            'max_length': 128,
            'type': 'password',
            'fixture_field': 'user_password'
        },
        "repeat_password": {
            'help_text': 'Repeat Password: ',
            'max_length': 128,
            'type': 'password',
            'fixture_field': 'user_password'
        },
        "first_name": {
            'help_text': 'First Name:',
            'max_length': 150,
            'fixture_field': 'user_first_name'
        },
        "last_name": {
            'help_text': 'Last Name:',
            'max_length': 150,
            'fixture_field': 'user_last_name'
        },
    }

    user_detail_fields = {
        "code": {
            'help_text': 'Employee Id: ',
            'max_length': 6,
            'fixture_field': 'user_code'
        },
        "gender": {
            'help_text': 'Gender',
            'choices': [value for value, display in GENDER_CHOICES],
            'type': 'choice',
            'fixture_field': 'user_gender'
        }
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--fixture-path',
            type=str,
            help='Load initial config data from fixture'
        )
        parser.add_argument(
            '--skip-if-exists',
            action='store_true',
            help='Skip setup if organization of given name already exist'
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Do not ask for user input, Add default Yes to options'
        )

    def load_data(self, data, fields):
        """
        Take input and load data
        :param data: dictionary to be filled
        :param fields: fields to take input
        :return: data
        """
        if self.fixture_path:
            return self.load_data_from_fixture(data, fields)
        else:
            return self.load_data_from_stdin(data, fields)

    def load_data_from_fixture(self, data, fields):
        """
        Take input and load data from self.fixture_path
        :param data: dictionary to be filled
        :param fields: fields to take input
        :return: data
        """
        with open(self.fixture_path) as fixture_file:
            fixture: dict = json.load(fixture_file)

        for field, properties in fields.items():
            fixture_field = properties.get('fixture_field', field)
            data[field] = fixture.get(fixture_field)

        return data

    def load_data_from_stdin(self, data, fields):
        """
        Take input and load data from stdin
        :param data: dictionary to be filled
        :param fields: fields to take input
        :return: data
        """
        for field in fields:
            data[field] = None
            # Repeatedly take input till it is not None
            while data[field] is None:
                properties = fields[field]
                property_type = properties.get('type')
                if property_type == 'password':
                    value = getpass.getpass(prompt=properties.get('help_text'))

                elif property_type == 'choice':
                    value = input("{} {}: ".format(properties.get('help_text'),
                                                   properties.get('choices')))
                else:
                    value = input(properties.get('help_text'))

                data[field] = self.validate_char_field(
                    value, max_length=properties.get('max_length', None),
                    choices=properties.get('choices', None))

        return data

    def create_organization(self):
        """
        Take input and create organization
        :return: organization
        """
        print("\n\nCreating New Organization")
        org_data = {key: None for key in self.organization_fields}
        org_data = self.load_data(org_data, self.organization_fields)

        org_data.update({
            'contacts': {'': ''},
            'size': '50 - 100 employees',
            'website': '',
            'registration_number': '',
            'vat_pan_number': '',
        })
        try:
            org = Organization.objects.create(**org_data)

            OrganizationAppearance.objects.create(organization=org)
            ContractSettings.objects.create(organization=org)

        except Exception as e:
            print(e)
            print("Could not create organization please try again.")
            if not self.fixture_path:
                # would end up in infinite recursion
                org = self.create_organization()
            else:
                raise e
        print("Successfully created organization {}".format(
            org_data.get('name')))
        return org

    def create_admin(self, organization):
        """
        Create admin for given organization
        :param organization: Organization
        :type organization: Organization
        :return: user
        """
        print("\n Create Admin for the organization")
        user_fields = dict(self.user_fields)
        user_data = {key: None for key in user_fields}
        user_data = self.load_data(user_data, user_fields)

        while user_data.get('password') != user_data.get('repeat_password'):
            print("Password did not match")
            user_fields.pop('email', None)
            user_fields.pop('first_name', None)
            user_fields.pop('last_name', None)
            user_data = self.load_data(user_data, user_fields)

        user_data.pop('repeat_password')
        user_data.update({'is_active': True})

        try:
            user = User.objects.create_user(**user_data)

            UserOrganization.objects.create(user=user, organization=organization,
                                            can_switch=True)

            # add first user to group Admin
            admin_group = Group.objects.get(name=ADMIN)
            user.groups.add(admin_group)
        except Exception as e:
            print(e)
            print("Could not create user. Please try again.")
            if not self.fixture_path:
                user = self.create_admin(organization)
            else:
                raise e

        print("Successfully create user for organization {}".format(
            organization))

        return user

    def create_user_detail(self, user, organization):
        """
        Crete user detail for user
        :param user: user whose user detail is to be created
        :param organization: user associated with organization
        :return:user
        """
        print("\n Create user detail for the user")
        user_detail_data = {key: None for key in self.user_detail_fields}
        user_detail_data = self.load_data(user_detail_data,
                                          self.user_detail_fields)
        user_detail_data.update({'user': user})
        user_detail_data.update({'date_of_birth': get_default_date_of_birth()})
        user_detail_data.update({'organization': organization})
        try:
            UserDetail.objects.create(**user_detail_data)
        except Exception as e:
            print(e)
            print("Could not create user detail. Please try again.")
            if not self.fixture_path:
                self.create_user_detail(user, organization)
            else:
                raise e
        print("Successfully created user_detail for user {}".format(user))

    @staticmethod
    def validate_char_field(value, blank=False, max_length=None, choices=None):
        """
        check empty field and max_length for char field
        """
        value = value.strip()

        if choices:
            if value in choices:
                return value
            else:
                print("Please enter a valid choice")
                return None

        if not (blank or bool(value)):
            print("This can not be empty")
            return None
        if max_length and len(value) > max_length:
            print("Value can not exceed {} in length".format(max_length))
            return None
        return value

    def handle(self, *args, **options):
        self.fixture_path = options.get('fixture_path')
        default_yes = options.get('no_input')
        skip_if_exists = options.get('skip_if_exists')

        if skip_if_exists:
            if not self.fixture_path:
                raise AssertionError(
                    'fixture_path must be present to use `skip-if-exists`')
            organization_name = self.load_data(
                {},
                {'name': self.organization_fields['name']}
            )['name']
            if Organization.objects.filter(name=organization_name).exists():
                print(add_color(
                    "Organization already exists ... [Skipping Initial Setup]",
                    YELLOW
                ))
                return

        proceed = default_yes or input(
            add_color('Do You want to create Organizations? (Y/N)\t', CYAN)
        ).upper() == 'Y'
        if not proceed:
            call_command('call_seeders', no_input=default_yes)
            return
        try:
            no_of_organizations = int(
                default_yes or input("Number of organizations to create: ")
            )
        except ValueError:
            print(add_color('Please select a valid number\nExit Setup', RED))
            return
        post_save.disconnect(sender=Organization,
                             receiver=create_organization_settings)
        for i in range(0, no_of_organizations):
            with transaction.atomic():
                organization = self.create_organization()
                proceed = default_yes or (input(
                    add_color(
                        'Create Default Settings for '
                        + organization.name
                        + ' (Recommended) (Y/N)',
                        CYAN
                    )
                ).upper() == 'Y')
                if proceed:
                    seed_default_data_for(organization)
                user = self.create_admin(organization=organization)
                self.create_user_detail(user=user, organization=organization)
        call_command('call_seeders', no_input=default_yes)
