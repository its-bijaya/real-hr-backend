from django.test import override_settings
from django.contrib.auth import get_user_model

from rest_framework.exceptions import ValidationError

from irhrs.core.utils.common_utils import get_system_admin
from irhrs.common.api.tests.common import RHRSAPITestCase

User = get_user_model()


class MaxUSerCountTestCase(RHRSAPITestCase):
    users = (
        ("userone@example.com", "password", "Male"),
        ("usertwo@example.com", "password", "Male"),
        ("userthree@example.com", "password", "Male"),
        ("userfour@example.com", "password", "Male"),
        ("userfive@example.com", "password", "Male"),
    )
    organization_name = "TestOrganization"

    @override_settings(MAX_USERS_COUNT=7)
    def test_valid_user_create_below_the_limit(self):
        User.objects.create_user(
            email="usersix@example.com",
            password="password",
            first_name="firstname",
            middle_name="middlename",
            last_name="lastname",
        )
        admin = get_system_admin()
        self.assertEqual(User.objects.exclude(id=admin.id).count(), 6)

    @override_settings(MAX_USERS_COUNT=6)
    def test_valid_user_create_on_the_limit(self):
        User.objects.create_user(
            email="usersix@example.com",
            password="password",
            first_name="firstname",
            middle_name="middlename",
            last_name="lastname",
        )
        admin = get_system_admin()
        self.assertEqual(User.objects.exclude(id=admin.id).count(), 6)

    @override_settings(MAX_USERS_COUNT=5)
    def test_invalid_user_create_over_the_limit(self):
        with self.assertRaises(ValidationError):
            User.objects.create_user(
                email="usersix@example.com",
                password="password",
                first_name="firstname",
                middle_name="middlename",
                last_name="lastname",
            )
