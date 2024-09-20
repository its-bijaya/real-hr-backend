import random

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from irhrs.core.utils import get_system_admin, nested_get
from irhrs.core.utils.subordinates import (
    find_immediate_subordinates, find_supervisor)
from irhrs.hris.utils.hierarchy_chart import build_hierarchy_chart, get_relationship
from irhrs.organization.api.v1.tests.setup import OrganizationSetUp
from irhrs.users.models import UserSupervisor


class CreateUserAndGenerateSupervisorRelationMixin:
    """
    Mixin class to create numbers of user and generate organization chart by adding supervisor
    to generated users
    """

    def generate_users(self, user_count):
        for i in range(user_count):
            self.users.append((
                f'{self.fake.first_name()}.{self.fake.last_name()}{self.fake.word()}'
                '@gmail.com'.lower(),
                'hellonepal',
                random.choice(self.gender),
                self.fake.text(max_nb_chars=100)
            ))

    def generate_chart(self):
        supervisors = self.sys_user[1:10]
        self.add_supervisor(
            supervisor=self.sys_user[0],
            subordinates=supervisors
        )
        for i, supervisor in enumerate(supervisors):
            sub_ordinates_index = (i + 1) * 10
            self.add_supervisor(
                supervisor=supervisor,
                subordinates=self.sys_user[sub_ordinates_index: (
                    sub_ordinates_index + 10)]
            )

    @staticmethod
    def add_supervisor(supervisor, subordinates: list, forward=True, approve=True, deny=True):
        user_supervisor = []
        for sub_ordinate in subordinates:
            user_supervisor.append(
                UserSupervisor(
                    user=sub_ordinate,
                    supervisor=supervisor,
                    authority_order=1,
                    forward=forward,
                    approve=approve,
                    deny=deny
                )
            )
        UserSupervisor.objects.bulk_create(user_supervisor)


class TestOrganizationChart(OrganizationSetUp, CreateUserAndGenerateSupervisorRelationMixin):
    users = [('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager')]
    gender = ['Male', 'Female']

    kwargs = {}

    def setUp(self):
        self.sys_admin = get_system_admin()
        self.generate_users(user_count=150)
        super().setUp()
        self.sys_user.insert(0, self.user.objects.get(email=self.users[0][0]))
        self.generate_chart()
        self.add_supervisor(
            supervisor=self.sys_admin,
            subordinates=[self.sys_user[0]]
        )
        self.kwargs.update({
            'category': 'parent',
            'pk': self.sys_user[0].id
        })
        cache.clear()

    @property
    def organization_chart_url(self):
        return reverse(
            'api_v1:hris:hierarchy-chart-detail',
            kwargs=self.kwargs
        )

    def test_organization_chart(self):
        """
        :return:
        """
        """
        test function to build hierarchy chart
        """
        self._test_build_hierarchy_chart_helper_method()

        """
        test function to generate relationship
        """
        self._test_get_relationship_helper_method()

        """
        test hierarchy chart for parent and family using API test
        """
        self._test_build_hierarchy_chart_for_parent_and_family()

    def _test_build_hierarchy_chart_for_parent_and_family(self):
        """
        :return:
        """

        # for parent api to build organization chart

        """
        --------------------------------------------------------------------------------------------
        test case for getting parent for head of organization where head of organization
        is determined if users supervisor is set to system admin (Real HR Bot)
        result => it must not return any data rather must return 'parent not found' message with
        404 status code
        """
        response = self.client.get(
            self.organization_chart_url
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json().get('detail'), 'Parent not found.')

        """
        --------------------------------------------------------------------------------------------
        test case for getting parent for other user rather than head of organization
        result => it must return data of parent with proper relationship
        """
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        user = self.sys_user[1]

        # here parent refers to supervisor
        parent = self.user.objects.get(id=find_supervisor(user.id))

        self.kwargs.update({
            'pk': user.id
        })
        response = self.client.get(
            self.organization_chart_url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            nested_get(response.json(), 'user.id'),
            parent.id,
            'Parent id for response and computed must be equal'
        )
        self.assertEqual(
            response.json().get('relationship'),
            get_relationship(parent.id, self.sys_admin.id),
            'Relationship value for response and computed must be equal'
        )

        # for family api to build organization chart

        """
        --------------------------------------------------------------------------------------------
        test case for getting family with children for user
        result => it returns data in respective format
        {
            "user": user detail,
            "relationship": relationship code for user,
            "children": list of dict which contains children data and relationship
        }
        """
        self.kwargs.update({
            'category': 'family',
            'pk': user.id
        })
        response = self.client.get(
            self.organization_chart_url,
            data={
                'children': True
            }
        )
        children = build_hierarchy_chart(supervisors=user.id, user=user.id)
        self.validate_family(children, response, user=user.id)

        """
        --------------------------------------------------------------------------------------------
        test case for getting family with siblings for user
        result => it returns data in respective format
        {
            "user": user detail of supervisor,
            "relationship": relationship code for supervisor,
            "children": list of dict which contains children of supervisor data and relationship
            excluding requesting user
        }
        """
        response = self.client.get(
            self.organization_chart_url,
        )
        supervisor = find_supervisor(user.id)
        children = build_hierarchy_chart(supervisors=supervisor, user=user.id)
        self.validate_family(children, response, user=supervisor)

        """
        --------------------------------------------------------------------------------------------
        test case for getting family with siblings for user whose parent is real hr bot (doesn't
        have any supervisor)
        result => it returns data in respective format
        {
            "user": returns static data,
            "relationship": 001,
            "children": list of dict which contains data and relationship code for sibling of user
        }
        """
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        user = self.sys_user[0]
        self.kwargs.update({
            'pk': user.id
        })
        response = self.client.get(
            self.organization_chart_url,
        )
        supervisor = find_supervisor(user.id)
        children = build_hierarchy_chart(
            supervisors=supervisor, user=user.id)  # return siblings
        self.validate_family(children, response)

    def _test_build_hierarchy_chart_helper_method(self):
        """
        test case for building hierarchy chart for different cases
        :return:
        """
        self.client.login(email=self.users[0][0], password=self.users[0][1])

        @override_settings(ORGANIZATION_SPECIFIC_EMPLOYEE_DIRECTORY=False)
        def get_sub_ordinates(_supervisor, _user):
            subordinates = self.user.objects.filter(
                id__in=find_immediate_subordinates(_supervisor)
            ).exclude(id=_user).order_by('first_name', 'middle_name', 'last_name').current()
            _data = []
            for subordinate in subordinates:
                _data.append({
                    'user': subordinate,
                    'relationship': get_relationship(subordinate.id, self.sys_admin.id)
                })
            return _data

        """
        --------------------------------------------------------------------------------------------
        test case for building hierarchy chart for respective users children ( subordinates )
        result => it must return list of dictionary containing user and their relationship
        """
        user = self.sys_user[0]
        response = build_hierarchy_chart(user.id, user.id)
        data = get_sub_ordinates(_supervisor=user.id, _user=user.id)
        self.assertListEqual(response, data)

        """
        --------------------------------------------------------------------------------------------
        test case for building hierarchy chart for respective users siblings
        result => it must return list of dictionary containing user and their relationship
        """
        user = self.sys_user[1]
        supervisor = find_supervisor(user.id)
        response = build_hierarchy_chart(supervisors=supervisor, user=user.id)
        data = get_sub_ordinates(_supervisor=supervisor, _user=user.id)
        self.assertListEqual(response, data)

        """
        --------------------------------------------------------------------------------------------
        test case for building hierarchy chart for respective users siblings
        result => it must return list of dictionary containing user and their relationship
        """
        user = self.sys_user[1]
        supervisor = find_supervisor(user.id)
        response = build_hierarchy_chart(supervisors=supervisor, user=user.id)
        data = get_sub_ordinates(_supervisor=supervisor, _user=user.id)
        self.assertListEqual(response, data)

        """
        --------------------------------------------------------------------------------------------
        test case for building hierarchy chart if supervisor is None
        result => must return empty list
        """
        response = build_hierarchy_chart(supervisors=None, user=user.id)
        self.assertListEqual(response, [])

    def _test_get_relationship_helper_method(self):
        """
        :return:
        """
        self.client.login(email=self.users[0][0], password=self.users[0][1])

        def validate_relationship(user, value):
            response = get_relationship(
                user=user.id, system_admin=self.sys_admin.id)
            self.assertEqual(response, value)

        """
        test relationship value for system admin
        result => 001
        """
        validate_relationship(user=self.sys_admin, value='001')

        """
        test relationship value for user who neither have supervisor nor children
        result => 000
        """
        validate_relationship(self.sys_user[-1], '000')

        """
        test relationship value for user who is head of organization i.e. whose supervisor is real
        hr bot
        result => depends upon the condition (either 001, 000)
        """
        # for condition 001
        # parent as system admin, doesn't have any siblings, contains subordinates
        validate_relationship(self.sys_user[0], '001')

        # for condition 011
        # parent as system admin, doesn't have any subordinates and siblings
        self.add_supervisor(
            supervisor=self.sys_admin,
            subordinates=[self.sys_user[-1]]
        )
        validate_relationship(self.sys_user[-1], '000')

        """
        test relationship value for user with condition (user have parent and siblings but
        doesn't have any subordinates )
        result => 110
        """
        validate_relationship(self.sys_user[21], '110')

        """
        test relationship value for user with condition(user have parent, siblings and subordinates)
        result => 111
        """
        validate_relationship(self.sys_user[2], '111')

        # """
        # test relationship value for user with condition (user have parent, subordinates
        # but doesn't have siblings)
        # result => 101
        # """
        # self.add_supervisor(
        #     supervisor=self.sys_user[88],
        #     subordinates=[self.sys_user[103]]
        # )
        # self.add_supervisor(
        #     supervisor=self.sys_user[103],
        #     subordinates=[self.sys_user[102]]
        # )
        # set_immediate_subordinates_and_supervisor_cache()
        # validate_relationship(self.sys_user[103], '101')
        #
        # """
        # test relationship value for user with condition (user have parent but no siblings and
        # subordinates)
        # result => 101
        # """
        # validate_relationship(self.sys_user[102], '100')

    def validate_family(self, children: list, response, user=None):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if user:
            self.assertEqual(
                nested_get(response.json(), 'user.id'),
                user,
                'User id from response and computed must be equal'
            )
            self.assertEqual(
                nested_get(response.json(), 'relationship'),
                get_relationship(user, self.sys_admin.id),
                'Relationship value for response and computed must be equal'
            )
        response_children = response.json().get('children')
        for i, child in enumerate(children):
            self.assertEqual(
                nested_get(response_children[i], 'user.id'),
                child.get('user').id,
                'Child id from response and computed must be equal'
            )
            self.assertEqual(
                nested_get(response_children[i], 'relationship'),
                child.get('relationship'),
                'Relationship value for child must be equal'
            )
