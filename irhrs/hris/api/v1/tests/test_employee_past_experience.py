"""
Past experience of employee refers to the experience they have gain in their past company
"""
from operator import add
from random import randint

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience, RHRSUnitTestCase
from irhrs.core.utils.common import get_today
from datetime import timedelta
from irhrs.users.api.v1.tests.factory import UserPastExperienceFactory


class TestEmployeePastExperience(RHRSUnitTestCase):
    def setUp(self):
        super().setUp()
        self.create_past_experience()

    def create_users(self, count=10):
        super().create_users(count=5)

    @property
    def employee_past_experience_detail_url(self):
        return reverse(
            'api_v1:users:user-past-experience-list',
            kwargs=self.kwargs
        )

    def create_past_experience(self):
        for user in self.SYS_USERS:
            UserPastExperienceFactory(
                user=user,
                start_date=get_today() - relativedelta(years=randint(3, 4)),
                end_date=get_today() - relativedelta(years=randint(1, 2))
            )

    def test_employee_past_experience(self):
        """
        test for viewing employee past experience
        :return:
        """
        self._test_detail_view()

    def _test_detail_view(self):
        """
        :return:
        """
        """
        --------------------------------------------------------------------------------------------
        viewing other past_experience as hr
        """
        user = self.SYS_USERS[0]
        past_experience = user.past_experiences.all()
        self.kwargs = {
            'user_id': user.id
        }
        response = self.client.get(
            self.employee_past_experience_detail_url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.validate_data(
            results=response.json().get('results'),
            data=past_experience
        )

        """
        --------------------------------------------------------------------------------------------
        viewing employee past experience by other user who is not hr
        """
        self.client.force_login(user=self.SYS_USERS[3])
        response = self.client.get(
            self.employee_past_experience_detail_url
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.json().get('detail'),
            "You do not have permission to perform this action."
        )

        """
        --------------------------------------------------------------------------------------------
        viewing employee past experience by self 
        """
        user = self.SYS_USERS[1]
        self.client.force_login(user=user)
        self.kwargs['user_id'] = user.id
        response = self.client.get(
            self.employee_past_experience_detail_url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.validate_data(
            results=response.json().get('results'),
            data=user.past_experiences.all()
        )
    
    @property
    def past_employee_list_url(self):
        return reverse(
            'api_v1:hris:users-past',
            kwargs=self.kwargs
        )
    def test_past_employees_list_as_hr(self):
        user_experience = self.SYS_USERS[1].current_experience
        end_date = user_experience.start_date + timedelta(days=30)
        user_experience.end_date = end_date
        user_experience.is_current = False
        user_experience.save()
        self.kwargs = {
            'organization_slug': self.organization.slug
        }
        url = self.past_employee_list_url
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()    
        )

        response_headings = response.data['results'][0].keys()
        self.assertTrue(
            "contract_end_date" in response_headings
        )

        contract_end_date = response.data['results'][0]['contract_end_date']
        self.assertEqual(
            end_date,
            contract_end_date,
            response.json()
        )
