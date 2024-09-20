from datetime import date
from irhrs.payroll.api.v1 import serializers
from irhrs.payroll.api.v1.serializers.payroll_serializer import HeadingSerializer
from irhrs.organization.models import organization
from django.urls import reverse
from irhrs.users.models.experience import UserExperience
from irhrs.payroll.models.payroll import UserExperiencePackageSlot, PackageHeading

from irhrs.payroll.utils.payroll_behaviour_test_helper import PayrollBehaviourTestBaseClass
from irhrs.payroll.tests.utils import PackageUtil

from irhrs.payroll.models import (
    # CONFIRMED,
    GENERATED,
    Payroll,
    Heading
)


class PackageOne(PackageUtil):
    RULE_CONFIG = {
        'heading_a':  {
            'rules': ['1000'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
            'duration_unit': 'Monthly', 'taxable': None, 'absent_days_impact': None
        },
        'heading_b':  {
            'rules': ['__HEADING_A__ + 1000'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
            'duration_unit': 'Monthly', 'taxable': None, 'absent_days_impact': None
        },
        'heading_c':  {
            'rules': ['__HEADING_B__ + 1000'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
            'duration_unit': 'Monthly', 'taxable': None, 'absent_days_impact': None
        }
    }

class PackageTwo(PackageUtil):
    RULE_CONFIG = {
        'heading_a':  {
            'rules': ['1000'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
            'duration_unit': 'Monthly', 'taxable': None, 'absent_days_impact': None
        },
        'heading_b':  {
            'rules': ['__HEADING_A__ + 1000'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
            'duration_unit': 'Monthly', 'taxable': None, 'absent_days_impact': None
        },
        'heading_c':  {
            'rules': ['__HEADING_B__ + 1000'],
            'payroll_setting_type': 'Salary Structure', 'type': 'Type2Cnst',
            'duration_unit': 'Monthly', 'taxable': None, 'absent_days_impact': None
        }
    }

class TestBulkApplyHeadingToUser(PayrollBehaviourTestBaseClass):
    """
    Notes:
    Package should be checked whether it is used or not in order to create a clone
    """
    organization_name = 'Test'

    user_experience_package_slot_start_date = date(2017, 1, 1)
    user_experience_start_date = date(2017, 1, 1)

    users = [
        dict(
            email='employeeone@example.com',
            password='password',
            user_experience_start_date=date(2017, 1, 1),
            detail=dict(
                gender='Male',
                joined_date=date(2017, 1, 1)
            )
        ),
        dict(
            email='employeetwo@example.com',
            password='password',
            user_experience_start_date=date(2017, 1, 1),
            detail=dict(
                gender='Male',
                joined_date=date(2017, 1, 1)
            )
        )
    ]

    def setUp(self):
        super().setUp()
        self.client.force_login(
            self.admin
        )

        self.payroll, _ = self.get_payroll(
            date(2017, 1, 1),
            date(2017, 1, 31),
            self.created_users[0]
        )

    def create_user_experience_packge_slots(self):

        packages = self.create_packages()

        self.user_packages = dict()

        for index, user in enumerate(self.created_users):

            self.user_packages[user.id] = packages[index]

            UserExperiencePackageSlot.objects.create(
                user_experience=UserExperience.objects.get(
                    user=user, 
                    organization=self.organization
                ),
                active_from_date=self.user_experience_package_slot_start_date,
                package=packages[index]
            )

    def create_packages(self):
        package_util_one = PackageOne(
            organization=self.organization
        )

        package_util_two = PackageTwo(
            organization=self.organization
        )

        package_one = package_util_one.create_package()
        package_two = package_util_two.create_package()
        
        return (
            package_one,
            package_two
        )

    def create_payroll(self, from_date, to_date):
        create_payroll = Payroll.objects.create(
            organization=self.organization,
            from_date=from_date,
            to_date=to_date,
            extra_data={}
        )
        create_payroll.status = GENERATED
        create_payroll.save()
        return create_payroll

    def get_new_valid_heading(self):
        """Creates a valid heading based on testcase scoped headings.
        Valid heading here is a heading with valid rule.

        Returns:
            valid heading object
        """

        serializer = HeadingSerializer(
            data=dict(
                organization=self.organization.slug,
                order=4,
                rules=PackageUtil._get_rule_data_for_serializer(["__HEADING_C__ + __HEADING_B__"]),
                name="New Heading",
                type="Type2Cnst",
                payroll_setting_type='Salary Structure',
                duration_unit='Monthly',
                taxable=None,
                benefit_type=None,
                absent_days_impact=None
            )
        )

        serializer.is_valid(raise_exception=True)

        instance = serializer.save()

        return instance

    def test_bulk_apply_headings_to_users(self):

        new_heading = self.get_new_valid_heading()

        url = reverse(
            'api_v1:payroll:heading-bulk-apply-to-users',
            kwargs=dict(
                pk=new_heading.id
            )
        ) + f'?organization__slug={self.organization.slug}'

        res = self.client.post(
            url,
            data=dict(
                active_from_date=date(2017,2,1),
                users=[user.id for user in self.created_users]
            )
        )

        self.assertEqual(200, res.status_code)

        