from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.payroll.models import Operation, OperationCode, OperationRate
from irhrs.payroll.models.unit_of_work_settings import UserOperationRate
from irhrs.payroll.tests.factory import OperationFactory, OperationCodeFactory, \
    OperationRateFactory
from irhrs.users.api.v1.tests.factory import UserFactory

USER = get_user_model()


class UnitOfWorkSettingsTestMixin:
    """
    Nothing much to test, just title unique to organization
    """
    users = [
        ('hr@admin.com', 'password', 'Female'),
        ('normal@user.com', 'password', 'Male')
    ]
    organization_name = 'ORG'
    model_class = None
    api_base_name = None

    @property
    def normal(self):
        return USER.objects.get(email='normal@user.com')

    @staticmethod
    def get_data(title):
        return {
            'title': title,
            'description': 'blah blah blah'
        }

    def _create_instance(self, title):
        return self.model_class.objects.create(
            organization=self.organization,
            **self.get_data(title)
        )

    def get_url(self, pk=None):
        if not pk:
            return reverse(
                f'api_v1:payroll:{self.api_base_name}-list',
                kwargs={
                    'organization_slug': self.organization.slug
                }
            )
        return reverse(
            f'api_v1:payroll:{self.api_base_name}-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': pk
            }
        )

    def test_valid_create(self):
        self.client.force_login(self.admin)
        data = self.get_data('Title')

        response = self.client.post(path=self.get_url(), data=data)
        self.assertEqual(response.status_code, 201)

        pk = response.data.get('id')
        instance = self.model_class.objects.get(id=pk)

        self.assertEqual(instance.title, data['title'])
        self.assertEqual(instance.description, data['description'])

    def test_creation_with_duplicate_title(self):
        self.client.force_login(self.admin)
        title = 'Duplicate Title'
        self._create_instance(title)

        data = self.get_data(title)

        response = self.client.post(path=self.get_url(), data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.data)

    def test_update_with_duplicate_title(self):
        instance_1 = self._create_instance('Title1')
        instance_2 = self._create_instance('Title2')

        self.client.force_login(self.admin)

        data = self.get_data(instance_1.title)

        # should raise error, updating instance_2 with instance_1's title
        response = self.client.put(
            self.get_url(instance_2.pk) + '?as=hr',
            data
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.data)

        # should not raise error, updating instance_1 with its own title (no change)
        response = self.client.put(
            self.get_url(instance_1.pk) + '?as=hr',
            data
        )
        self.assertEqual(response.status_code, 200)

    def test_create_duplicate_title_different_organization(self):
        self.client.force_login(self.admin)
        title = "Title"
        instance = self._create_instance(title)
        instance.organization = OrganizationFactory()
        instance.save()

        data = self.get_data(title)

        response = self.client.post(path=self.get_url(), data=data)
        self.assertEqual(response.status_code, 201)

        pk = response.data.get('id')
        instance = self.model_class.objects.get(id=pk)

        self.assertEqual(instance.title, data['title'])
        self.assertEqual(instance.description, data['description'])

    def test_permission(self):
        self.client.force_login(self.normal)
        response = self.client.post(self.get_url(), self.get_data('title'))
        self.assertEqual(response.status_code, 403)


class OperationTest(UnitOfWorkSettingsTestMixin, RHRSAPITestCase):
    model_class = Operation
    api_base_name = 'unit-of-work-operation'


class OperationCodeTest(UnitOfWorkSettingsTestMixin, RHRSAPITestCase):
    model_class = OperationCode
    api_base_name = 'unit-of-work-operation-code'


class OperationRateText(RHRSAPITestCase):
    users = [
        ('hr@admin.com', 'password', 'Female'),
        ('normal@user.com', 'password', 'Male')
    ]
    organization_name = 'ORG'

    @property
    def url(self):
        return reverse('api_v1:payroll:unit-of-work-operation-rate-list',
                       kwargs={
                           'organization_slug': self.organization.slug
                       })

    def test_valid_create(self):
        data = {
            "operation": OperationFactory(organization=self.organization).id,
            "operation_code": OperationCodeFactory(organization=self.organization).id,
            "rate": 155,
            "unit": "hour"
        }
        self.client.force_login(self.admin)
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 201)

        pk = response.data.get('id')
        rate = OperationRate.objects.get(pk=pk)
        self.assertEqual(rate.operation.id, data['operation'])
        self.assertEqual(rate.operation_code.id, data['operation_code'])

    def test_create_with_operation_from_different_organization(self):
        data = {
            "operation": OperationFactory().id,  # will create new organization
            "operation_code": OperationCodeFactory(organization=self.organization).id,
            "rate": 155
        }
        self.client.force_login(self.admin)
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get('operation'),
                         ["Operation is from different organization"])

    def test_create_with_operation_code_from_different_organization(self):
        data = {
            "operation": OperationFactory(organization=self.organization).id,
            "operation_code": OperationCodeFactory().id,  # will create new organization
            "rate": 155
        }
        self.client.force_login(self.admin)
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get('operation_code'),
                         ["Operation Code is from different organization"])


class UserOperationRateTest(RHRSAPITestCase):
    users = [
        ('hr@admin.com', 'password', 'Female'),
        ('normal@user.com', 'password', 'Male'),
        ('normaltwo@user.com', 'password', 'Male'),
        ('normalthree@user.com', 'password', 'Male'),
        ('normalfour@user.com', 'password', 'Male'),
        ('normalfive@user.com', 'password', 'Male'),
        ('normalsix@user.com', 'password', 'Male'),
    ]
    organization_name = 'ORG'

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.operation = OperationFactory(organization=self.organization)
        self.operation_rate = OperationRateFactory(operation=self.operation)

    @property
    def url(self):
        return reverse(
            'api_v1:payroll:unit-of-work-user-operation-rate-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'operation_rate_id': self.operation_rate.id
            }
        )

    @property
    def user_list_url(self):
        return reverse(
            'api_v1:payroll:unit-of-work-operation-rate-users',
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': self.operation_rate.id
            }
        )

    def test_valid_create_and_update(self):
        user1_id = UserFactory().id
        user2_id = UserFactory().id
        data = {
            "user": [user1_id, user2_id],
        }
        url = self.url + '?as=hr'
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            ['Cannot assign user from different organization to rate']
        )
        user1_id = USER.objects.filter(email='normaltwo@user.com').first().id
        user2_id = USER.objects.filter(email='normalthree@user.com').first().id
        user3_id = USER.objects.filter(email='normalfour@user.com').first().id
        user4_id = USER.objects.filter(email='normalfive@user.com').first().id
        user5_id = USER.objects.filter(email='normalsix@user.com').first().id

        data = {
            "user": [user1_id, user2_id],
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json().get('user'), [user1_id, user2_id])
        self.assertEqual(UserOperationRate.objects.all().count(), 2)

        # updating user scenario
        # checking whether previous user is deleted or not and new user are created or not
        response = self.client.post(
            url,
            data={
                "user": [user3_id, user4_id, user5_id]
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json().get('user'), [user3_id, user4_id, user5_id])
        self.assertEqual(UserOperationRate.objects.all().count(), 3)

        # Check whether previous user can be assigned to same rate or not
        response = self.client.post(
            url,
            data={
                "user": [user1_id, user2_id, user3_id, user4_id, user5_id]
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.json().get('user'),
            [user1_id, user2_id, user3_id, user4_id, user5_id]
        )
        self.assertEqual(UserOperationRate.objects.all().count(), 5)

        # Check the users present in the rate
        url = self.user_list_url + '?as=hr'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.json().get('user')),
            5
        )

        pk = response.data.get('id')
        self.assertTrue(OperationRate.objects.filter(pk=pk).exists())
