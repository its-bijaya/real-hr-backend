import json
import string
from datetime import timedelta
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from faker import Factory
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.constants.user import GENDER_CHOICES
from irhrs.core.utils import get_system_admin
from irhrs.event.constants import OUTSIDE, MEETING
from irhrs.event.models import Event
from irhrs.organization.models import OrganizationBranch


class EventSetUp(RHRSTestCaseWithExperience):
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

    def setUp(self):
        super().setUp()
        self.user = get_user_model()
        self.content_type = ContentType.objects.get_for_model(Event)
        self.sys_users = list(self.user.objects.filter(email__in=[user[0] for user in self.users[1:]]).order_by('id'))
        self.members = [('members', user.id) for user in self.sys_users[:-1]]
        self.branch = OrganizationBranch.objects.create(
            organization=self.organization,
            branch_manager=None,
            name=self.fake.word(),
            description='zzz',
            contacts=json.dumps({
                'Mobile': '1234567890'
            }),
            email='',
            code='',
            mailing_address='',
        )
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.event_list_url = reverse('api_v1:event:-list')


class MeetingSetup(RHRSTestCaseWithExperience):
    users = []
    organization_name = "Google"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123
    fake = Factory.create()
    gender = dict(GENDER_CHOICES).keys()
    ACTIONS = ['early_out', 'late_in', 'absent', 'leave']
    kwargs = {}

    def setUp(self):
        self.generate_users()
        super().setUp()
        self.user_obj = get_user_model()
        self.sys_admin = get_system_admin()
        user_lst = list(
            self.user_obj.objects.filter(
                email__in=[user[0] for user in self.users[1:]]
            ).order_by('id')
        )
        self.USER = user_lst[0]
        self.SYS_USERS = user_lst
        self._data = [
                         ('title', self.fake.text(max_nb_chars=100)),
                         ('start_at', timezone.now() + timedelta(hours=1)),
                         ('end_at', timezone.now() + timedelta(days=2)),
                         ('event_location', OUTSIDE),
                         ('description', self.fake.text(max_nb_chars=10)),
                         ('location', self.fake.address()),
                         ('event_category', MEETING),
                         ('interactive_event', False),
                         ('eventdetail', json.dumps(
                             {
                                 'agenda': [self.fake.text(max_nb_chars=100) for _ in
                                            range(10)],
                                 'notification_time': [10, 20, 30, 40, 50],
                                 'minuter': self.SYS_USERS[1].id,
                                 'time_keeper': self.SYS_USERS[2].id
                             }
                         )),
                     ] + [('members', user.id) for user in self.SYS_USERS[1: 6]]
        self.client.force_login(user=self.USER)
        self._create_meeting()

    def generate_users(self):
        self.users = [
            (
                f'{self.fake.first_name().lower()}.{self.fake.last_name().lower()}{self.fake.word().lower()}@gmail.com',
                f'password',
                'Male',
                f'Clerk {random_char}'
            ) for random_char in list(string.ascii_lowercase)[:10]
        ]

    @property
    def event_list_url(self):
        return reverse(
            viewname='api_v1:event:-list'
        )

    @property
    def data(self):
        return urlencode(self._data)

    def _create_meeting(self):
        response = self.client.post(
            path=self.event_list_url, data=self.data,
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = Event.objects.get(id=response.data.get('id'))
        self.meeting = event.eventdetail
