import json

from django.contrib.auth import get_user_model
from faker import Factory

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.organization.models import OrganizationBranch


class OrganizationSetUp(RHRSTestCaseWithExperience):
    users = [
        ('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
        ('hello@hello.com', 'secretThing', 'Male', 'Clerk'),
        ('helloa@hello.com', 'secretThing', 'Male', 'Clerka'),
        ('hellob@hello.com', 'secretThing', 'Male', 'Clerkb'),
    ]
    organization_name = "Google"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123
    fake = Factory.create()
    user = get_user_model()

    def setUp(self):
        super().setUp()
        self.sys_user = list(
            self.user.objects.filter(email__in=[user[0] for user in self.users[1:]]).order_by('id')
        )
        self.branch = OrganizationBranch.objects.create(
            organization=self.organization,
            branch_manager=None,
            name=self.fake.word(),
            description=self.fake.text(max_nb_chars=150),
            contacts=json.dumps({
                'Mobile': '1234567890'
            }),
            email='',
            code='',
            mailing_address='',
        )
        self.client.login(email=self.users[0][0], password=self.users[0][1])
