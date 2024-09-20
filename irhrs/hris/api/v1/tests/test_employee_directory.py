import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from faker import Factory
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience, \
    RHRSAPITestCase
from irhrs.hris.constants import NEW
from irhrs.users.models import UserDetail, UserSupervisor
from irhrs.users.api.v1.tests.factory import UserExperienceFactory, OrganizationFactory, UserFactory
from irhrs.organization.models import EmploymentJobTitle
from irhrs.organization.api.v1.tests.factory import ContractSettingsFactory,\
    EmploymentJobTitleFactory
from irhrs.organization.models import UserOrganization


class UserDirectoryTest(RHRSTestCaseWithExperience):
    # TODO @Shital: Write test for supervisor filter.

    users = [
        ('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
        ('hello@hello.com', 'secretThing', 'Male', 'Clerk'),
        ('helloa@hello.com', 'secretThing', 'Male', 'Clerka'),
        ('hellob@hello.com', 'secretThing', 'Male', 'Clerkb'),
        ('helloc@hello.com', 'secretThing', 'Male', 'Clerkc'),
    ]
    organization_name = "Google"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123
    fake = Factory.create()

    directory_url = reverse('api_v1:hris:user-directory-list')

    def setUp(self):
        super().setUp()
        self.today = timezone.now()
        self.user = get_user_model()
        # Here all users details are listed
        self.sys_user = list(
            self.user.objects.filter(
                email__in=[
                    user[0] for user in self.users
                ]
            )
        )
        self.client.login(email=self.users[0][0], password=self.users[0][1])

    def test_employee_directory(self):

        # request for employee directory
        response = self.client.get(self.directory_url)
        # test get request is successful or not
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # test all the users is created or not
        self.assertEqual(
            response.data.get('count'),
            get_user_model().objects.all().exclude_admin().current().count()
        )

    def test_update_join_date(self):
        """
        update join_date of all user, by default join date is set to today. so now we update each
        users joined date
        :return:
        """

        for index, user in enumerate(self.sys_user):
            days = 365 * index
            join_date = self.today.date() - datetime.timedelta(days=days)
            UserDetail.objects.filter(user=user).update(
                joined_date=join_date)

        # request for employee directory
        response = self.client.get(self.directory_url)
        # test get request is successful or not
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        employees_list = response.data.get('results')

        # Here we get the user detail from database
        get_user_detail = list(
            UserDetail.objects.filter(
                user_id__in=[
                    user.id for user in self.sys_user
                ]
            )
        )

        # now we test data from response and from database
        for employee_data in employees_list:
            joined_date = employee_data.get('joined_date')
            if joined_date <= self.today.date() <= joined_date + relativedelta(months=1):
                # Here user created in one month should have NEW tag
                self.assertEqual(employee_data.get('tag').get('onboarding'), NEW)
            else:
                self.assertFalse(employee_data.get('tag').get('onboarding'))
            for employee_user_detail in get_user_detail:

                # Here we test the join date is equal to database user id
                if employee_data.get('user').get('id') == employee_user_detail.user.id:
                    self.assertEqual(employee_data.get('joined_date'),
                                     employee_user_detail.joined_date)

    def test_user_directory_supervisor_filter(self):
        for index, user in enumerate(self.created_users):
            if index == 0:
                continue

            if index == len(self.created_users) - 1:
                continue
            UserSupervisor.objects.create(
                user=user,
                supervisor=self.admin,
                authority_order=1
            )

        UserSupervisor.objects.create(
            user=self.created_users[1],
            supervisor=self.created_users[2],
            authority_order=2
        )

        UserSupervisor.objects.create(
            user=self.created_users[4],
            supervisor=self.created_users[2],
            authority_order=2
        )

        url = self.directory_url + f'?supervisor={self.admin.id}'
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('count'),
            4
        )
        expected_user_id = [
            self.created_users[1].id, self.created_users[2].id, self.created_users[3].id,
            self.created_users[4].id
        ]
        user_id = list()
        for item in response.json().get('results'):
            user_id.append(item.get('user').get('id'))
        self.assertEqual(
            set(user_id),
            set(expected_user_id)
        )


class TestPastAndCurrentEmployeeList(RHRSAPITestCase):
    users = [
        ('hellomanone@gmail.com', 'secretWorldIsThis', 'Male'),
        ('hellomanonpppp@gmail.com', 'AsecretWorldIsThis', 'Female'),
    ]
    organization_name = "Apple"
    division_name = "Programming"
    division_ext = 123

    def setUp(self):
        super().setUp()
        self.client.force_login(user=self.admin)
        self.kwargs = {
            'organization_slug': self.organization.slug
        }
        ContractSettingsFactory(
            organization=self.organization
        )

    @property
    def past_employee_list_url(self):
        url = reverse(
            'api_v1:hris:users-past',
            kwargs = {
                'organization_slug': self.organization.slug
            }
        )
        return url

    @property
    def current_employee_list_url(self):
        url = reverse(
            'api_v1:hris:users-list',
            kwargs = {
                'organization_slug': self.organization.slug
            }
        )
        return url

    def test_contract_expired_user_with_is_current_true(self):
        five_days = datetime.timedelta(days=5)
        hundred_days = datetime.timedelta(days=100)
        first_exp_data = {
            "organization": self.organization,
            "user": self.created_users[1],
            "start_date": timezone.now().date() - hundred_days,
            "end_date": timezone.now().date() - five_days,
            "is_current": True,
            "current_step": 1,
            "employment_status__is_contract": True
        }
        user_experience = UserExperienceFactory(**first_exp_data)
        # check on past user list
        response = self.client.get(self.past_employee_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(
            response.json()['results'][0]['user']['id'],
            self.created_users[1].id
        )
        # check it does not show up in current list
        response = self.client.get(self.current_employee_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)

    def test_contract_expired_user_with_is_current_False(self):
        five_days = datetime.timedelta(days=5)
        hundred_days = datetime.timedelta(days=100)
        first_exp_data = {
            "organization": self.organization,
            "user": self.created_users[1],
            "start_date": timezone.now().date() - hundred_days,
            "end_date": timezone.now().date() - five_days,
            "is_current": False,
            "current_step": 1,
            "employment_status__is_contract": True
        }
        user_experience = UserExperienceFactory(**first_exp_data)
        response = self.client.get(self.current_employee_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)

        # check on past user list
        response = self.client.get(self.past_employee_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(
            response.json()['results'][0]['user']['id'],
            self.created_users[1].id
        )

class TestSupervisorFilterDifferentOrganization(RHRSTestCaseWithExperience):
    users = [
        ('Anish@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
        ('pratima@gmail.com', 'AsecretWorldIsThis', 'Female', 'developer'),
    ]
    organization_name = "Apple"
    division_name = "Programming"
    division_ext = 123
    def setUp(self):
        super().setUp()
        self.another_organization = OrganizationFactory(
            name="microsoft",
        )
        self.supervisor_user = UserFactory(
            _organization=self.another_organization)
        UserOrganization.objects.create(user=self.supervisor_user, organization=self.another_organization,
                                        can_switch=True)
        for user in self.created_users:
            UserSupervisor.objects.create(
                user=user,
                supervisor=self.supervisor_user,
                user_organization=self.organization,
                supervisor_organization=self.another_organization
            )
        self.client.force_login(self.supervisor_user)

    def get_supervisor_subordinates_url(self, org_slug=None, method=None, supervisor_id=None):
        if org_slug is None:
            return reverse('api_v1:users:users-supervisor')
        elif method == "user-directory-list":
            return reverse("api_v1:hris:user-directory-list")+f"?search=&supervisor={supervisor_id}&organization={org_slug}"
        return reverse(
            f'api_v1:hris:{method}',
            kwargs = {
                'organization_slug': org_slug
            }
        )+f"?supervisor={supervisor_id}"

    def test_supervisor_can_switch_organization(self):
        url = self.get_supervisor_subordinates_url()
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.json()['supervisor_switchable_organizations'][0]['name'],
            self.organization_name,
            response.json()
        )

    def test_employee_directory_for_different_organization(self):

        supervisor_id = self.supervisor_user.id
        supervisor_subordinates = UserSupervisor.objects.filter(
            supervisor=self.supervisor_user,
            user_organization=self.organization,
            supervisor_organization=self.another_organization
        ).order_by('created_at')
        supervisor_subordinate_count = supervisor_subordinates.count()
        normal_user_org_slug = self.organization.slug
        url = self.get_supervisor_subordinates_url(normal_user_org_slug, "overview-summary-list", supervisor_id)
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.json()['Total Employee'],
            supervisor_subordinate_count,
            response.json()
        )

        url = self.get_supervisor_subordinates_url(normal_user_org_slug, 'user-list', supervisor_id)
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.json()['joined']['total'],
            supervisor_subordinate_count
        )
        self.assertEqual(
            response.json()['genders']['total'],
            supervisor_subordinate_count
        )

        url = self.get_supervisor_subordinates_url(normal_user_org_slug, 'user-directory-list', supervisor_id)
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.json()['count'],
            supervisor_subordinate_count,
            response.json()
        )

        for user, subordinate in zip(response.json()['results'], supervisor_subordinates.order_by()):
            self.assertEqual(
                user['user']['id'],
                subordinate.user.id,
                response.json()
            )
            self.assertEquals(
                user['user']['organization']['name'],
                subordinate.user_organization.name,
                response.json()
            )
            self.assertEqual(
                user['supervisor']['id'],
                subordinate.supervisor.id,
                response.json()
            )
            self.assertEqual(
                user['supervisor']['organization']['name'],
                subordinate.supervisor_organization.name,
                response.json()
            )
