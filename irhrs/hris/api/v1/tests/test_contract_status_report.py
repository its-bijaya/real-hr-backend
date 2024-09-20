import datetime

from django.utils import timezone
from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.organization.models import (
    Organization, OrganizationDivision,
    UserOrganization, EmploymentJobTitle)
from irhrs.organization.api.v1.tests.factory import ContractSettingsFactory
from irhrs.users.models import UserExperience
from irhrs.users.api.v1.tests.factory import UserExperienceFactory


class TestEmployeeContractStatus(RHRSTestCaseWithExperience):
    users = [('hellomanone@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
             ('hellomantwo@hello.com', 'secretThing', 'Male', 'Sales Person'),
             ]
    organization_name = "Apple"
    division_name = "Programming"
    division_ext = 123

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

        five_days = datetime.timedelta(days=5)
        hundred_days = datetime.timedelta(days=100)
        first_exp_data = {
            "organization": self.organization,
            "user": userdetail.user,
            "job_title": job_title,
            "division": self.division,
            "start_date": timezone.now().date() - hundred_days,
            "end_date": timezone.now().date(),
            "is_current": True,
            "current_step": 1,
            "employment_status__is_contract": True
        }
        user_experience = UserExperienceFactory(**first_exp_data)

    def setUp(self):
        super().setUp()
        self.client.force_login(user=self.admin)
        self.kwargs = {
            'organization_slug': self.organization.slug
        }
        ContractSettingsFactory(
            organization=self.organization
        )

    def test_cannot_renew_contract_on_overlapping_date(self):
        four_days = datetime.timedelta(days=4)
        five_days = datetime.timedelta(days=5)
        contract_to_renew = (
            self.created_users[1].user_experiences.order_by('end_date')
            .last()
        )
        self.kwargs.update({
            'pk': contract_to_renew.id
        })
        contract_renew_url = reverse(
            'api_v1:hris:contract-status-renew',
            kwargs=self.kwargs
        )
        payload = {
            "end_date": timezone.now().date() + five_days
        }
        response = self.client.post(
            path=contract_renew_url,
            data=payload,
            format='json',
        )
        new_contract = (
            self.created_users[1].user_experiences.order_by('end_date')
            .last()
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contract_to_renew.refresh_from_db()
        self.assertEqual(
            contract_to_renew.end_date,
            timezone.now().date(),
        )
        self.assertEqual(
            new_contract.end_date,
            timezone.now().date() + five_days,
        )
        # renewing multiple time on future date should
        # throw error if it overlaps
        self.kwargs.update({
            'pk': new_contract.id
        })
        contract_renew_url = reverse(
            'api_v1:hris:contract-status-renew',
            kwargs=self.kwargs
        )
        payload.update({
            "end_date": timezone.now().date() + five_days
        })
        response = self.client.post(
            path=contract_renew_url,
            data=payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['end_date'],
            ['Contract already exists until the given date.']
        )

    def test_cannot_renew_contract_as_todays_date(self):
        contract_to_renew = (
            self.created_users[1].user_experiences.order_by('end_date')
            .last()
        )
        self.kwargs.update({
            'pk': contract_to_renew.id
        })
        self.contract_renew_url = reverse(
            'api_v1:hris:contract-status-renew',
            kwargs=self.kwargs
        )
        payload = {
            "end_date": timezone.now().date()
        }
        response = self.client.post(
            path=self.contract_renew_url,
            data=payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        future_date_validation_error = {
            'end_date': ['This value must be a future date']
        }
        self.assertEqual(response.json(), future_date_validation_error)
