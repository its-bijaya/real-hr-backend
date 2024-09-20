"""
test for calendar within Normal User >>Calendar & Event >> Calendar in frontend
"""
import calendar
import random
from datetime import timedelta, datetime
from random import randint

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.core.constants.user import GENDER_CHOICES
from irhrs.core.utils.common import get_today
from irhrs.event.api.v1.tests.factory import EventFactory
from irhrs.event.constants import PUBLIC, SEMINAR
from irhrs.event.models import Event
from irhrs.hris.utils import upcoming_anniversaries, upcoming_birthdays
from irhrs.organization.api.v1.tests.setup import OrganizationSetUp
from irhrs.leave.api.v1.tests.factory import LeaveRequestFactory
from irhrs.leave.models import LeaveRequest
from irhrs.leave.constants.model_constants import APPROVED
from irhrs.organization.api.v1.tests.factory import HolidayFactory
from irhrs.organization.models import Holiday


class TestCalendar(OrganizationSetUp):
    users = [('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager')]
    # TODO: @Shital add leave within FILTER_TYPE list
    FILTER_TYPE = ['holiday', 'anniversary', 'birthday', 'event', 'leave']
    GENDER = list(dict(GENDER_CHOICES).keys())
    EVENT_TYPE = ['Private', 'Public']

    def setUp(self):
        for i in range(30):
            self.users.append(
                (
                    f'{self.fake.first_name()}.{self.fake.last_name()}{self.fake.word()}@gmail.com'.lower(),
                    'hellonepal',
                    random.choice(self.GENDER),
                    self.fake.text(max_nb_chars=100)
                )
            )
        super().setUp()
        self.sys_user.insert(0, self.user.objects.get(email=self.users[0][0]))
        for filter_type in self.FILTER_TYPE:
            getattr(self, f'generate_{filter_type}')()
        self.generate_date_range()

    def generate_date_range(self):
        # Returns today's month start & end
        today = get_today(with_time=True)
        self.date_range = today.replace(day=1), today + relativedelta(months=1) - timedelta(days=1)

    def generate_leave(self):
        # TODO: @Shital Implement test for leave in calendar
        LeaveRequestFactory(
            user=self.created_users[0],
            status=APPROVED
        )

    def generate_holiday(self):
        for date in self.dates:
            HolidayFactory(organization=self.organization, date=date)

    def generate_anniversary(self):
        dates = self.dates
        for date in dates:
            user = random.choice(self.sys_user)
            user.detail.joined_date = date - relativedelta(years=2)
            user.save()

    def generate_birthday(self):
        dates = self.dates
        for date in dates:
            user = random.choice(self.sys_user)
            user.detail.date_of_birth = date - relativedelta(years=randint(18, 40))
            user.save()

    def generate_event(self):
        for date in self.dates:
            date = datetime(date.year, date.month, date.day).astimezone()
            EventFactory(
                start_at=date + timedelta(hours=randint(1, 3)),
                end_at=date + timedelta(days=randint(0, 5), hours=randint(6, 10)),
                event_type=random.choice(self.EVENT_TYPE),
                event_category=SEMINAR
            )

    @property
    def dates(self):
        return {self.fake.date_this_month(before_today=True, after_today=True) for _ in range(20)}

    def get_event(self):
        event = Event.objects.filter(
            (Q(start_at__date__range=self.date_range)) &
            (Q(event_type=PUBLIC) | Q(created_by=self.sys_user[0]) | Q(
                members__in=[self.sys_user[0]]))
        ).distinct()
        return event, event.count()

    def get_birthday(self):
        qs = upcoming_birthdays(
            self.user.objects.filter(is_active=True).current(),
            start_date=self.date_range[0],
            detail__organization=self.organization
        )
        qs = qs.filter(next_birthday__range=self.date_range)
        return qs, qs.count()

    def get_anniversary(self):
        qs = upcoming_anniversaries(
            self.user.objects.filter(is_active=True).current(),
            start_date=self.date_range[0],
            detail__organization=self.organization
        )
        qs = qs.filter(next_anniversary__range=self.date_range)
        return qs, qs.count()

    def get_leave(self):
        qs = LeaveRequest.objects.all()
        # (
        #     self.user.objects.filter(is_active=True).current(),
        #     start_date=self.date_range[0],
        #     detail__organization=self.organization
        # )
        # qs = qs.filter(next_anniversary__range=self.date_range)
        return qs, qs.count()

    def get_holiday(self):
        data = Holiday.objects.filter(
            Q(organization__isnull=True) |
            Q(organization=self.organization))
        data = data.filter(date__range=self.date_range)
        return data, data.count()

    def test_calendar(self):
        """
        test to check all event, birthday, anniversary, leaves, holiday for a given range
        of date time
        :return:
        """
        calendar_data = {}
        calendar_data_count = {}
        for filter_type in self.FILTER_TYPE:
            calendar_data[filter_type], calendar_data_count[filter_type] = getattr(self,
                                                                                   f'get_{filter_type}'
                                                                                   )()

        response = self.client.get(
            reverse(
                'api_v1:organization:org-calender',
                kwargs={
                    'organization_slug': self.organization.slug
                }
            ),
            data={
                'start': self.date_range[0],
                'end': self.date_range[1],
                'type': ','.join(self.FILTER_TYPE)
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # validating counts for (leave, anniversary, birthday, holiday, event) within calender

        response_count = response.json().get('event_counts')
        self.assertEqual(response_count.get('birthday_count'), calendar_data_count.get('birthday'))
        self.assertEqual(response_count.get('anniversary_count'),
                         calendar_data_count.get('anniversary'))
        self.assertEqual(response_count.get('holidays_count'), calendar_data_count.get('holiday'))
        self.assertEqual(response_count.get('events_count'), calendar_data_count.get('event'))
        self.assertEqual(response_count.get('all_count'), sum(calendar_data_count.values()))

        # validate date for (leave, anniversary, birthday, holiday, event) within calender
        response_data = {
            'event': [],
            'holiday': [],
            'birthday': [],
            'anniversary': [],
            'leave': []
        }
        for data in response.json().get('event_data'):
            response_data[data.get('tag')].append(data)

        for filter_type in self.FILTER_TYPE:
            self.validate_data(
                list(calendar_data[filter_type]),
                response_data[filter_type],
                filter_type
            )

    def validate_data(self, calender_data, response, tag):
        # title, id, start, end
        date_filter = {
            'event': 'start_at',
            'birthday': 'next_birthday',
            'anniversary': 'next_anniversary',
            'holiday': 'date',
            'leave': 'start'
        }
        for index, datum in enumerate(calender_data):
            self.assertEqual(datum.id, response[index].get('id'))
            self.assertEqual(tag, response[index].get('tag'))
            if tag == 'event':
                self.assertEqual(
                    getattr(datum, date_filter[tag]),
                    parse(response[index].get('start'))
                )
                self.assertEqual(
                    datum.end_at,
                    parse(response[index].get('end'))
                )
            elif tag == 'leave':
                self.assertEqual(
                    getattr(datum, date_filter[tag]),
                    parse(response[index].get('start'))
                )
                self.assertEqual(
                    datum.end,
                    parse(response[index].get('end'))
                )
            else:
                self.assertEqual(
                    getattr(datum, date_filter[tag]),
                    parse(response[index].get('start')).date()
                )
