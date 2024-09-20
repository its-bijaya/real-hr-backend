from django.urls import reverse
from rest_framework import status

from irhrs.organization.api.v1.tests.factory import HolidayFactory, OrganizationFactory
from irhrs.organization.api.v1.tests.setup import OrganizationSetUp


class TestOrganizationHoliday(OrganizationSetUp):
    def setUp(self):
        super().setUp()
        self.org2 = OrganizationFactory()
        self.organizations = [self.organization, self.org2]
        self.generate_holidays()
        self.kwargs = {}

    @property
    def dates(self):
        # returns random fake dates used to create holidays for organization
        return {self.fake.date_this_year(before_today=True, after_today=True) for _ in range(50)}

    @property
    def holiday_url(self):
        return reverse(
            'api_v1:organization:organization-holiday-list',
            kwargs=self.kwargs
        )

    def generate_holidays(self):
        for date in self.dates:
            HolidayFactory(organization=self.organization, date=date)
            HolidayFactory(organization=self.org2, date=date)

    def test_organization_holiday_from_normal_user_view(self):
        """
        test for listing holiday from normal user view
        :return:
        """
        """
        --------------------------------------------------------------------------------------------
        trying to get list of holidays for associated organization and  another organization 
        result => returns data for the user for given organization 
        """
        for org in self.organizations:
            self.kwargs = {
                'organization_slug': org.slug
            }
            holidays = org.holiday_set.all()

            response = self.client.get(
                self.holiday_url,
                data={
                    'limit': holidays.count()
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self._check_valid_conditions(
                holidays=holidays,
                results=response.json().get('results')
            )

        """
        --------------------------------------------------------------------------------------------
        trying to get list of holidays from non existing organization 
        result => returns 404 error
        """
        self.kwargs = {
            'organization_slug': "non-existing-organization"
        }
        response = self.client.get(
            self.holiday_url,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def _check_valid_conditions(self, holidays, results):
        for i, holiday in enumerate(holidays):
            self.assertEqual(results[i].get('name'), holiday.name)
            self.assertEqual(results[i].get('slug'), holiday.slug)
            self.assertEqual(results[i].get('date'), holiday.date.strftime('%Y-%m-%d'))

            # for rule of holiday
            self.assertListEqual(
                results[i].get('rule').get('division'),
                list(holiday.rule.division.all().values_list('slug', flat=True))
            )
            self.assertListEqual(
                results[i].get('rule').get('religion'),
                list(holiday.rule.religion.all().values_list('slug', flat=True))
            )
            self.assertListEqual(
                results[i].get('rule').get('ethnicity'),
                list(holiday.rule.ethnicity.all().values_list('slug', flat=True))
            )
            self.assertListEqual(
                results[i].get('rule').get('branch'),
                list(holiday.rule.branch.all().values_list('slug', flat=True))
            )
            self.assertEqual(results[i].get('rule').get('gender'), holiday.rule.gender)
            self.assertEqual(results[i].get('rule').get('lower_age'), holiday.rule.lower_age)
            self.assertEqual(results[i].get('rule').get('upper_age'), holiday.rule.upper_age)
