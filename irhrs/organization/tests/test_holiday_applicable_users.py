from dateutil.relativedelta import relativedelta

from irhrs.common.api.tests.common import BaseTestCase
from irhrs.common.models import ReligionAndEthnicity
from irhrs.core.constants.common import ETHNICITY, RELIGION
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import HolidayFactory, OrganizationDivisionFactory, \
    OrganizationBranchFactory
from irhrs.users.api.v1.tests.factory import UserFactory


class HolidayApplicableUsersTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.holiday = HolidayFactory()
        self.organization = self.holiday.organization
        self.user1 = UserFactory(_organization=self.organization)
        self.user2 = UserFactory(_organization=self.organization)

    def test_applicable_user_with_no_rules(self):
        users = self.holiday.applicable_users
        self.assertIn(self.user1, users)
        self.assertIn(self.user2, users)

    def test_applicable_user_with_gender(self):
        self.user1.detail.gender = 'Male'
        self.user1.detail.save()

        self.user2.detail.gender = 'Female'
        self.user2.detail.save()

        cases = {
            'All': [self.user1, self.user2],
            'Male': [self.user1],
            'Female': [self.user2],
            'Other': []
        }

        for case, result in cases.items():
            with self.atomicSubTest(msg=f"Gender: [{case}]"):
                self.holiday.rule.gender = case
                self.holiday.rule.save()

                users = self.holiday.applicable_users

                self.assertEqual(len(users), len(result), result)
                for user in result:
                    self.assertIn(user, users)

    def test_applicable_user_with_age_range(self):
        # age 20
        self.user1.detail.date_of_birth = get_today() - relativedelta(years=20)
        self.user1.detail.save()

        # age 40
        self.user2.detail.date_of_birth = get_today() - relativedelta(years=40)
        self.user2.detail.save()

        cases = {
            (16, 80): [self.user1, self.user2],
            (20, 40): [self.user1, self.user2],
            (25, 45): [self.user2],
            (25, 35): [],
            (15, 35): [self.user1],
            (45, 100): []
        }
        for case, result in cases.items():
            with self.atomicSubTest(msg=f"Age: [{case}]"):
                self.holiday.rule.lower_age = case[0]
                self.holiday.rule.upper_age = case[1]
                self.holiday.rule.save()

                users = self.holiday.applicable_users

                self.assertEqual(len(users), len(result), result)
                for user in result:
                    self.assertIn(user, users)

    def test_applicable_user_with_division(self):
        division1 = OrganizationDivisionFactory(organization=self.organization)
        division2 = OrganizationDivisionFactory(organization=self.organization)

        self.user1.detail.division = division1
        self.user1.detail.save()

        self.user2.detail.division = division2
        self.user2.detail.save()

        self.holiday.rule.division.add(division1)

        users = self.holiday.applicable_users

        self.assertIn(self.user1, users)
        self.assertNotIn(self.user2, users)

    def test_applicable_user_with_ethnicity(self):
        ethnicity1 = ReligionAndEthnicity.objects.create(name="One", category=ETHNICITY)
        ethnicity2 = ReligionAndEthnicity.objects.create(name="Two", category=ETHNICITY)

        self.user1.detail.ethnicity = ethnicity1
        self.user1.detail.save()

        self.user2.detail.ethnicity = ethnicity2
        self.user2.detail.save()

        self.holiday.rule.ethnicity.add(ethnicity1)

        users = self.holiday.applicable_users

        self.assertIn(self.user1, users)
        self.assertNotIn(self.user2, users)

    def test_applicable_user_with_religion(self):
        religion1 = ReligionAndEthnicity.objects.create(name="One", category=RELIGION)
        religion2 = ReligionAndEthnicity.objects.create(name="Two", category=RELIGION)

        self.user1.detail.religion = religion1
        self.user1.detail.save()

        self.user2.detail.religion = religion2
        self.user2.detail.save()

        self.holiday.rule.religion.add(religion1)

        users = self.holiday.applicable_users

        self.assertIn(self.user1, users)
        self.assertNotIn(self.user2, users)

    def test_applicable_user_with_branch(self):
        branch1 = OrganizationBranchFactory(organization=self.organization)
        branch2 = OrganizationBranchFactory(organization=self.organization)

        self.user1.detail.branch = branch1
        self.user1.detail.save()

        self.user2.detail.branch = branch2
        self.user2.detail.save()

        self.holiday.rule.branch.add(branch1)

        users = self.holiday.applicable_users

        self.assertIn(self.user1, users)
        self.assertNotIn(self.user2, users)
