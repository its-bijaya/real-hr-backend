import random

from dateutil.relativedelta import relativedelta
from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSUnitTestCase
from irhrs.core.utils.common import get_today
from irhrs.users.api.v1.tests.factory import (UserEducationFactory)


class TestEmployeeEducationDetail(RHRSUnitTestCase):
    user = []

    def setUp(self):
        super().setUp()
        self.create_educational_detail()
        self.kwargs = {
            'organization_slug': self.organization.slug
        }

    def create_users(self, count=10):
        super().create_users(count=5)

    @property
    def employee_education_detail_url(self):
        return reverse(
            'api_v1:users:user-education-list',
            kwargs=self.kwargs
        )

    def create_educational_detail(self):
        for user in self.SYS_USERS:
            is_current = random.choice([True, False])
            years = random.randint(5, 10)
            UserEducationFactory(
                user=user,
                from_year=get_today() - relativedelta(years=3) if is_current \
                    else get_today() - relativedelta(years=years),
                to_year=None if is_current else get_today() - relativedelta(years=years - 4),
                is_current=is_current
            )

    def test_employee_educational_detail(self):
        """
        test for viewing employee education detail
        :return:
        """
        self._test_list_view()

    def _test_list_view(self):
        """
        :return:
        """
        """
        --------------------------------------------------------------------------------------------
        viewing other educational_detail as hr
        """
        user = self.SYS_USERS[0]
        educational_detail = user.user_education.all()
        self.kwargs = {
            'user_id': user.id
        }
        response = self.client.get(
            self.employee_education_detail_url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.validate_data(
            results=response.json().get('results'),
            data=educational_detail
        )

        """
        --------------------------------------------------------------------------------------------
        viewing employee medical information by other user who is not hr
        """
        self.client.force_login(user=self.SYS_USERS[-1])
        response = self.client.get(
            self.employee_education_detail_url
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.json().get('detail'),
            "You do not have permission to perform this action."
        )

        """
        --------------------------------------------------------------------------------------------
        viewing employee medical information by self
        """
        self.client.force_login(user=user)
        response = self.client.get(
            self.employee_education_detail_url
        )
        self.validate_data(
            results=response.json().get('results'),
            data=educational_detail
        )
