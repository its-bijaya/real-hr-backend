import datetime

from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from rest_framework import status

from irhrs.core.utils.common import get_today
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.organization.models.holiday import Holiday
from irhrs.event.constants import PUBLIC, PRIVATE
from irhrs.event.models import Event
from irhrs.users.models import User, UserDetail
from irhrs.event.api.v1.tests.factory import EventFactory


class TestUpcomingEventTestCase(RHRSTestCaseWithExperience):
    users = [('hellomanone@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
             ('hellomantwo@hello.com', 'secretThing', 'Male', 'Sales Person'),
             ]
    organization_name = "Apple"
    division_name = "Programming"
    division_ext = 123

    def setUp(self):
        self.five_days_ago = timezone.now() - datetime.timedelta(days=5)
        self.seven_days_ago = timezone.now() - datetime.timedelta(days=7)
        self.today = timezone.now()
        super().setUp()
        self.user = get_user_model()
        self.client.login(email=self.users[0][0], password=self.users[0][1])

        # get details of all users and update organization
        self.user_detail_first = User.objects.get(email=self.users[0][0])
        UserDetail.objects.filter(user=self.user_detail_first).update(
            organization=self.organization)
        self.user_detail_second = User.objects.get(email=self.users[1][0])
        UserDetail.objects.filter(user=self.user_detail_second).update(
            organization=self.organization)

    def test_get_upcoming_birthday(self):
        """
        test upcoming birthday
        :return:none
        """
        # url to get birthday
        upcoming_birthdays = reverse(
            'api_v1:hris:upcoming-birthdays-list',
            kwargs={
                'organization_slug': self.organization.slug,
            }
        )

        """
            update the birthday of user, if date_of_birth is not updated then by default it sets
             to 19 years from today, so now we update the birthday to 1999-Dec-7
             #TODO @Utsav: Refactor comment likewise
        """
        updated_birth_date = self.today.date() - datetime.timedelta(days=20 * 364)
        UserDetail.objects.filter(user=self.user_detail_second).update(
            date_of_birth=updated_birth_date)

        # start_date and end_date to get birthdays between two dates
        start_date = self.today.date() - datetime.timedelta(days=14)
        end_date = self.today.date() + datetime.timedelta(days=16)

        # passing start date and end date as a url
        upcoming_birthdays += f'?start_date=' \
                              f'{start_date}&end_date=' \
                              f'{end_date}'

        # request for upcoming birthdays in between given date
        response = self.client.get(upcoming_birthdays)

        # test get request is successful or not
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        get_result = response.json().get('results')

        # function test either the birthday is accurate or not
        self._event_date_test(get_result, start_date, end_date)

        """update birth date should not lie between one month period, that is between start date and
        end date. Birthday must be greater than end date"""
        self.assertGreater(end_date, updated_birth_date)

    def test_upcoming_anniversaries(self):

        """
        test upcoming anniversaries
        :return:
        """

        # upcoming anniversaries url
        upcoming_anniversaries = reverse(
            'api_v1:hris:upcoming-anniversaries-list',
            kwargs={
                'organization_slug': self.organization.slug,
            }
        )

        # update join_date of user, by default join date is set to today
        join_date_second = self.today.date() - datetime.timedelta(days=420)
        UserDetail.objects.filter(user=self.user_detail_second).update(
            joined_date=join_date_second)
        join_date_first = self.today.date() - datetime.timedelta(days=2 * 365)
        UserDetail.objects.filter(user=self.user_detail_first).update(
            joined_date=join_date_first)

        # start_date and end_date to get anniversaries between two dates
        start_date = self.today.date() - datetime.timedelta(days=15)
        end_date = self.today.date() + datetime.timedelta(days=15)

        # passing start date and end date as a url
        upcoming_anniversaries += f'?start_date=' \
                                  f'{start_date}&end_date=' \
                                  f'{end_date}'

        # request for upcoming anniversaries in between given date
        response = self.client.get(upcoming_anniversaries)

        # test get request is successful or not
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        get_result = response.json().get('results')

        # function test either the anniversaries is accurate or not
        self._event_date_test(get_result, start_date, end_date)

        """updated join date should not lie between one month period, that is between start date and
               end date. Anniversary date must be greater than end date"""
        self.assertGreater(end_date, join_date_second)

    def _event_date_test(self, response, start_date, end_date):
        for event_data in response:
            user_id = event_data.get('id')
            user_birthday = event_data.get('birthday')
            user_anniversary = event_data.get('anniversary')
            if user_birthday:
                birth_date = UserDetail.objects.get(user_id=user_id).date_of_birth
                year = self.today.year
                if birth_date.month == 2 and birth_date.day > 28:
                    birth_date = birth_date.replace(day=28)
                current_birth_date = birth_date.replace(year=year)
                if current_birth_date < start_date:
                    year += 1
                current_birth_date = birth_date.replace(year=year)
                birthday_date = parse(user_birthday).date()

                # test anniversaries from database is equal to response joined_date or not
                self.assertEqual(current_birth_date, birthday_date)

                # test anniversaries lies between specified start_date and end_date
                self.assertGreaterEqual(birthday_date,
                                        start_date)
                self.assertLessEqual(birthday_date, end_date)
            elif user_anniversary:
                joined_date = UserDetail.objects.get(user_id=user_id).joined_date
                year = self.today.year
                current_anniversary = joined_date.replace(year=year)
                if current_anniversary < start_date:
                    year += 1
                current_anniversary = joined_date.replace(year=year)
                anniversary_date = parse(user_anniversary).date()

                # test anniversaries from database is equal to response joined_date or not
                self.assertEqual(anniversary_date, current_anniversary)

                # test anniversaries lies between specified start_date and end_date
                self.assertGreaterEqual(anniversary_date,
                                        start_date)
                self.assertLessEqual(anniversary_date, end_date)
            else:
                # holiday test
                holiday_slug = event_data.get('slug')
                holiday_date_response = event_data.get('date')

                # get date from database
                holiday_date_db = Holiday.objects.get(slug=holiday_slug).date
                holiday_date = parse(holiday_date_response).date()

                # test holiday from database is equal to response holiday_date or not
                self.assertEqual(holiday_date, holiday_date_db)

                # test holiday date lies between specified start_date and end_date
                self.assertGreaterEqual(holiday_date_db,
                                        start_date)
                self.assertLessEqual(holiday_date_db, end_date)

    def test_create_holiday(self):
        holiday_first_date = self.today.date() + datetime.timedelta(days=2)
        holiday_second_date = self.today.date() + datetime.timedelta(days=25)
        holiday_third_date = self.today.date() - datetime.timedelta(days=25)
        Holiday.objects.create(organization=self.organization,
                               name='Chill Day',
                               date=holiday_first_date)
        Holiday.objects.create(organization=self.organization,
                               name='Hike Day',
                               date=holiday_second_date)
        Holiday.objects.create(organization=self.organization,
                               name='Ride Day',
                               date=holiday_third_date)

        # url to test upcoming holiday
        holiday_url = reverse('api_v1:organization:organization-holiday-list',
                              kwargs={
                                  'organization_slug': self.organization.slug,
                              }
                              )

        # start_date and end_date to get birthdays between two dates
        start_date = self.today.date() - datetime.timedelta(days=13)
        end_date = self.today.date() + datetime.timedelta(days=17)

        # passing start date and end date as a url
        holiday_url += f'?start_date=' \
                       f'{start_date}&end_date=' \
                       f'{end_date}'

        # request for upcoming anniversaries in between given date
        response = self.client.get(holiday_url)

        # test response is successful or not
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        get_result = response.json().get('results')

        # function test either the holiday is accurate or not
        self._event_date_test(get_result, start_date, end_date)

        """
        Holiday date one month before and after should not be between start and end date,
        i.e one month is a period between start_date
        and end_date
        """
        self.assertGreater(holiday_second_date, end_date)
        self.assertLess(holiday_third_date, start_date)

    @property
    def upcoming_events_url(self):
        url = reverse(
            'api_v1:hris:upcoming-events-list',
            kwargs = {
                'organization_slug': self.organization.slug
            }
        )
        return url

    def test_upcoming_events(self):
        for i in range(10):
            EventFactory(
                start_at=self.seven_days_ago + datetime.timedelta(days=i),
                end_at=self.five_days_ago + datetime.timedelta(days=i)
            )
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        query_params = {
            "start_date": self.today.date(),
            "end_date": self.today.date() + datetime.timedelta(days=30),
        }
        response = self.client.get(self.upcoming_events_url, query_params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['upcoming_events']),
                         5)

    def test_upcoming_private_event_created_by_user(self):
        for i in range(10):
            EventFactory(
                start_at=self.seven_days_ago + datetime.timedelta(days=i, hours=10),
                end_at=self.five_days_ago + datetime.timedelta(days=i, hours=10)
            )
        # make one event created by current user
        events = Event.objects.all().order_by('start_at')
        last_event = events.last()
        last_event.event_type=PRIVATE
        last_event.created_by = self.created_users[0]
        last_event.save()

        self.client.login(email=self.users[0][0], password=self.users[0][1])
        query_params = {
            "start_date": self.today.date(),
            "end_date": self.today.date() + datetime.timedelta(days=30),
        }
        response = self.client.get(self.upcoming_events_url, query_params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # event created by user should be displayed
        response_ids = list(
            map(
                lambda x: x['id'],
                response.json()['upcoming_events'])
        )
        self.assertIn(last_event.id, response_ids)
