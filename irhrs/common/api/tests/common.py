import contextlib
import datetime
import tempfile

from cuser.middleware import CuserMiddleware
from dateutil.parser import parse
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.signals import post_save
from django.test import TestCase
from django.utils import timezone
from django.utils.functional import cached_property
from PIL import Image
from faker import Factory
from rest_framework import status as drf_status
from rest_framework.test import APITestCase

from irhrs.core.constants.organization import GOVERNMENT
from irhrs.core.utils import nested_getattr, get_system_admin
from irhrs.organization.models import (
    Organization, OrganizationDivision,
    UserOrganization, EmploymentJobTitle)
from irhrs.organization.signals import create_organization_settings
from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.constants.permissions import hrs_permissions \
    as permissions_module
from irhrs.permission.models import HRSPermission
from irhrs.permission.models.hrs_permisssion import OrganizationGroup
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models import User, UserDetail
from irhrs.users.models.experience import UserExperience
from irhrs.users.utils import get_default_date_of_birth

# exclude builtins from module
permissions = [permissions for permissions in dir(permissions_module)
               if not permissions.startswith("_")]

from django.core.cache import cache


class BaseTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cache.clear()
        super().setUpTestData()

    def tearDown(self) -> None:
        CuserMiddleware.del_user()
        cache.clear()
        super().tearDown()

    def _should_check_constraints(self, connection):
        return False

    @contextlib.contextmanager
    def atomicSubTest(self, **kwargs):
        """
        :keyword kwargs: kwargs to pass in subTest
        :return: A ContextManager which will rollback to initial save point upon exit

        Run all your cases inside a test case. Test execution will not be interrupted when single
        test fails, it will run all test cases and show result at last

        Usage
        ---
        .. code-block:: python

            for case in cases:
                with self.atomicSubTest():
                    run_test(case)
        """
        savepoint = transaction.savepoint()

        try:
            with self.subTest(**kwargs):
                yield savepoint
        finally:
            transaction.savepoint_rollback(savepoint)


class GrantPermissionAndValidateData:
    def validate_data(self, results, data):
        """
        used for validating data whether computed data asserts or not with response data
        :param results: response data (list of dict)
        :param data: computed data (queryset)
        :return:
        """

        def parse_date(_key, _value, _data):
            if type(getattr(_data, _key)) is datetime.date:
                return parse(_value).date()
            elif type(getattr(_data, _key)) is datetime.datetime:
                return parse(_value)
            return _value

        for index, datum in enumerate(data):
            for key, value in results[index].items():
                if hasattr(datum, key):
                    if isinstance(getattr(datum, key), models.Manager):
                        if value:
                            self.assertEqual(
                                list(getattr(datum, key).values(
                                    *(list(value[0].keys()))
                                )),
                                value
                            )
                    elif isinstance(getattr(datum, key), models.Model):
                        pk_data = nested_getattr(datum, key).id
                        pk_field = 'id'
                        if isinstance(value, dict) and 'slug' in value:
                            pk_data = nested_getattr(datum, key).slug
                            pk_field = 'slug'

                        self.assertEqual(
                            pk_data,
                            value if not isinstance(value, dict) else value.get(pk_field),
                            f'Computed and response {key} {pk_field} must be equal'
                        )
                    else:
                        self.assertEqual(
                            nested_getattr(datum, key),
                            parse_date(key, value, datum),
                            f'Computed {key} and response {key} must be equal'
                        )

    def grant_permissions(self):
        permission_objects = []
        for permission in permissions:
            data = getattr(permissions_module, permission)
            if not isinstance(data, dict):
                continue
            obj = HRSPermission(**data)
            try:
                obj.full_clean()
                permission_objects.append(obj)
            except ValidationError:
                pass

        objs = HRSPermission.objects.bulk_create(permission_objects)

        # Grant admin all the created permissions
        admin = Group.objects.get(name=ADMIN)

        # add in org groups
        for og in OrganizationGroup.objects.filter(
                group=admin
        ):
            og.permissions.add(*objs)

        admin_group, _ = Group.objects.get_or_create(name=ADMIN)

        # Admin for organization
        OrganizationGroup.objects.all().delete()
        org_specific_group, _ = OrganizationGroup.objects.get_or_create(
            organization=self.organization,
            group=admin_group
        )
        org_specific_group.permissions.add(
            *HRSPermission.objects.filter(
                organization_specific=True
            )
        )
        for user in admin_group.user_set.all():
            UserOrganization.objects.create(
                organization=org_specific_group.organization,
                user=user,
                can_switch=True
            )

        # Admin for common permissions
        common_group, _ = OrganizationGroup.objects.get_or_create(
            organization=None,
            group=admin_group
        )
        common_group.permissions.add(
            *HRSPermission.objects.filter(
                organization_specific=False
            )
        )

    def create_organization(self):
        org_data = {
            'name': self.organization_name,
            'abbreviation': self.organization_name[:3].upper(),
            'about': 'This is about',
            'contacts': {},  # set empty for now,
            'ownership': GOVERNMENT,
            'size': '50 - 100 employees',
            'website': '',
            'registration_number': '',
            'vat_pan_number': '',
            'established_on': '2017-01-11'
        }
        self.organization = Organization.objects.create(**org_data)


class RHRSAPITestCase(APITestCase, BaseTestCase, GrantPermissionAndValidateData):
    """
    Base Test Case for RHRS

    It creates organization and populates user model.

    set `organization_name` and `users` to do so.

    organization_name = 'Name of Organization'

    users = [
            ('email1@email.com', 'password', 'gender'),
            ('email2@email.com', 'password', 'gender')
        ]


    It will generate organization abbreviation name by capitalizing
    first 3 letters of its name

    *Note*: Users will have `first_name` as first part of their email
    *Note*: The first user will be Admin and will get all permissions by default
    """
    organization_name = None
    users = None
    admin = None
    status = drf_status

    def __init__(self, *args, **kwargs):
        assert self.organization_name is not None
        assert self.users is not None
        self.created_users = list()
        super().__init__(*args, **kwargs)

    def create_users(self, after_create=None):
        """
        Create users and call after create functions with
        params (userdetail, parsed_data)

        parsed_data is the return data of method get_parsed_data

        :param after_create: functions to call after create
        :type after_create: list
        """
        after_create = after_create or []
        i = 0
        for user in self.users:
            parsed_data = self.get_parsed_data(user)

            email = parsed_data.get('email')
            password = parsed_data.get('password')
            gender = parsed_data.get('gender')
            name = email.split('@')[0]

            data = {
                'email': email,
                'first_name': name.split('.')[0],
                'last_name': name.split('.')[-1],
                'password': password,
                'username': email,
                'is_active': True
            }
            user = User.objects.create_user(**data)
            self.created_users.append(user)
            UserOrganization.objects.create(user=user,
                                            organization=self.organization)

            code = "{}{}".format(self.organization.abbreviation, i)
            i += 1

            user_detail_data = {
                'user': user,
                'code': code,
                'gender': gender,
                'date_of_birth': get_default_date_of_birth(),
                'organization': self.organization
            }

            userdetail = UserDetail.objects.create(**user_detail_data)

            if not self.admin:
                self.admin = user
                Group.objects.get(name=ADMIN).user_set.add(user)

            for func in after_create:
                func(userdetail, parsed_data)

    @staticmethod
    def get_parsed_data(user_data):
        email, password, gender = user_data
        return {
            "email": email,
            "password": password,
            "gender": gender
        }

    def setUp(self):
        post_save.disconnect(sender=Organization, receiver=create_organization_settings)
        self.create_organization()
        self.create_users()
        self.grant_permissions()


class RHRSTestCaseWithExperience(RHRSAPITestCase):
    """
    Base test case with UserExperience for all users

    users = [('email', 'password', 'gender', 'job_title'), ...]
    """
    division_name = "TestDivision"
    division_ext = 123

    def create_division(self, name=None, ext=None):
        if not name:
            name = str(self.division_name)
        if not ext:
            ext = int(self.division_ext)

        assert name is not None
        assert ext is not None

        division = OrganizationDivision.objects.create(**{
            "organization": self.organization,
            "name": name,
            "extension_number": ext
        })
        self.division = division

    def create_experience(self, userdetail, parsed_data):
        job_title = parsed_data.get('job_title')
        job_title, _ = EmploymentJobTitle.objects.get_or_create(
            organization=self.organization,
            title=job_title
        )

        # set user division head if not set
        if not self.division.head:
            self.division.head = userdetail.user
            self.division.save()

        data = {
            "organization": self.organization,
            "user": userdetail.user,
            "job_title": job_title,
            "division": self.division,
            "start_date": timezone.now().date(),
            "is_current": True,
            "current_step": 1
        }

        UserExperience.objects.create(**data)

    @staticmethod
    def get_parsed_data(user_data):
        email, password, gender, job_title = user_data
        return {
            "email": email,
            "password": password,
            "gender": gender,
            "job_title": job_title
        }

    def setUp(self):
        self.create_organization()
        self.create_division()
        self.create_users(after_create=[self.create_experience])
        self.grant_permissions()


class TestCaseValidateData(BaseTestCase):

    def validate_data(self, results, data):
        """
        used for validating data whether computed data asserts or not with response data
        :param results: response data (dict)
        :param data: computed data (instance)
        :return:
        """

        def parse_date(_key, _value, _data):
            if type(getattr(_data, _key)) is datetime.date:
                return parse(_value).date()
            elif type(getattr(_data, _key)) is datetime.datetime:
                return parse(_value)
            return _value

        for index, datum in enumerate(data):
            for key, value in results[index].items():
                if hasattr(datum, key):
                    if isinstance(getattr(datum, key), models.Manager):
                        if value:
                            self.assertEqual(
                                list(getattr(datum, key).values(
                                    *(list(value[0].keys()))
                                )),
                                value
                            )
                    elif isinstance(getattr(datum, key), models.Model):
                        self.assertEqual(
                            nested_getattr(datum, key).id,
                            value if not isinstance(value, dict) else value.get('id'),
                            f'Computed {key} id and response {key} id must be equal'
                        )
                    else:
                        self.assertEqual(
                            nested_getattr(datum, key),
                            parse_date(_key=key, _value=value, _data=datum),
                            f'Computed {key} and response {key} must be equal'
                        )


class RHRSUnitTestCase(APITestCase, BaseTestCase, GrantPermissionAndValidateData):
    """
    Base test case with UserExperience for all users using factory
    """
    # TODO: @shital remove this class
    fake = Factory.create()
    SYS_USERS = []
    ACTIONS = ['early_out', 'late_in', 'absent', 'leave']
    kwargs = {}
    file = None

    def setUp(self):
        self.organization_name = self.fake.word()
        self.create_organization()
        self.create_users()
        self.grant_permissions()
        self.client.force_login(user=self.USER)

    def create_users(self, count=10):
        users = [
            UserFactory(
                email=f'{self.fake.first_name()}.{self.fake.last_name()}{self.fake.word()}@gmail.com'
            ) for _ in range(count)
        ]
        self.USER = users[0]
        self.SYS_USERS = users
        UserDetail.objects.filter(user__in=users).update(organization=self.organization)
        Group.objects.get(name=ADMIN).user_set.add(users[0])

    @cached_property
    def SYS_ADMIN(self):
        # TODO: @shital change name to snake case
        return get_system_admin()


class FileHelpers:
    """
    Helper class that helps in testing files
    """

    @staticmethod
    def get_image(size=(200, 200)):
        """
        returns temporary image file
        """
        temp_file = tempfile.NamedTemporaryFile(suffix='.png')
        color = (255, 0, 0, 0)
        image = Image.new("RGBA", size, color)
        image.save(temp_file, 'png')
        temp_file.seek(0)
        return temp_file
