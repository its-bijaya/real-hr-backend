from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.urls import reverse
from rest_framework import status

from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import HolidayFactory
from irhrs.organization.api.v1.tests.setup import OrganizationSetUp
from irhrs.organization.models import Holiday


class TestCalendarDetail(OrganizationSetUp):
    def setUp(self):
        super().setUp()
        self.generate_date_range()

    def generate_date_range(self):
        # Returns today's month start & end
        today = get_today(with_time=True)
        self.date_range = today.replace(day=1), today + relativedelta(months=1) - timedelta(
            days=1)

    def generate_holiday(self):
        for date in self.dates:
            HolidayFactory(organization=self.organization, date=date)

    @property
    def dates(self):
        return {self.fake.date_this_month(before_today=True, after_today=True) for _ in range(20)}

    @property
    def url(self):
        return reverse(
            'api_v1:organization:org-calender-detail',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def test_calendar_detail(self):
        self.client.force_login(self.created_users[1])
        self.generate_holiday()
        holiday_id = Holiday.objects.first().id
        url = self.url + f'?type=holiday&id={holiday_id}'
        response = self.client.get(
            url
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('organization').get('value'),
            "Google"
        )
        holiday = Holiday.objects.get(id=holiday_id)
        holiday.organization = None
        holiday.save()
        response = self.client.get(
            url
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('organization').get('value'),
            "N/A"
        )
