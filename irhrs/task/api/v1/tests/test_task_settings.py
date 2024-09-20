from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.task.api.v1.tests.factory import ProjectFactory, ActivityFactory
from irhrs.task.models import TaskSettings
from irhrs.task.models.settings import Project, Activity, UserActivityProject
from irhrs.users.api.v1.tests.factory import UserFactory


class TaskSettingsTestCase(RHRSAPITestCase):
    users = [
        ('admin@email.com', 'password', 'Male'),
    ]
    organization_name = "Google"

    def test_setup_task_settings(self):
        self.client.force_login(self.admin)
        url = reverse(
            'api_v1:task:task-setting',
            kwargs={'organization_slug': self.organization.slug}
        )

        # test get before any settings
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)

        self.assertTrue(response.data.get('can_assign_to_higher_employment_level'))

        # update to True
        response = self.client.put(url, {'can_assign_to_higher_employment_level': True})
        self.assertEqual(response.status_code, 200, response.data)
        setting = TaskSettings.get_for_organization(self.organization)
        self.assertTrue(setting.can_assign_to_higher_employment_level)

        # try get
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data.get('can_assign_to_higher_employment_level'))

        # update to False
        response = self.client.put(url, {'can_assign_to_higher_employment_level': False})
        self.assertEqual(response.status_code, 200, response.data)
        setting = TaskSettings.get_for_organization(self.organization)
        self.assertFalse(setting.can_assign_to_higher_employment_level)

        # try get
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data.get('can_assign_to_higher_employment_level'))


class ProjectTestCase(RHRSAPITestCase):
    users = [
        ('admin@email.com', 'password', 'Male'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.project = ProjectFactory()

    @property
    def project_create_payload(self):
        return {
            "name": "RealHrSoft",
            "description": "Complete HR Solution",
            "is_billable": False
        }

    @property
    def project_url(self):
        return reverse(
            'api_v1:task:project-list'
        )

    @property
    def project_detail_url(self):
        return reverse(
            'api_v1:task:project-detail',
            kwargs={
                'pk': self.project.id
            }
        )

    def test_create_project(self):
        response = self.client.post(
            self.project_url, self.project_create_payload, format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertTrue(Project.objects.filter(name='RealHrSoft').exists())

        UserActivityProject.objects.create(
            project=Project.objects.get(name='RealHrSoft'),
            activity=ActivityFactory(),
            is_billable=True,
            user=self.admin
        )
        response = self.client.get(self.project_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('count'),
            1
        )

        response = self.client.get(
            self.project_detail_url, {"as": "hr"}
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        expected_output = {
           "id": self.project.id,
           "name": self.project.name,
           "description": self.project.description,
           "start_date": None,
           "end_date": None,
           "is_billable": False,
           "created_by": None,
           "member_count": 0
        }
        self.assertEqual(
            response.json(),
            expected_output
        )


class ActivityTestCase(RHRSAPITestCase):
    users = [
        ('admin@email.com', 'password', 'Male'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.activity = ActivityFactory()

    @property
    def activity_url(self):
        return reverse(
            'api_v1:task:activity-list'
        )

    @property
    def payload(self):
        return {
            "name": "Typing",
            "description": "Typing Task",
            "unit": "hour",
            "employee_rate": 100,
            "client_rate": 150
        }

    def test_activity(self):
        response = self.client.post(
            self.activity_url, self.payload
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertTrue(Activity.objects.filter(name="Typing").exists())

        response = self.client.get(
            self.activity_url
        )
        expected_output = {
           "id": Activity.objects.first().id,
           "name": "Typing",
           "description": "Typing Task",
           "unit": "hour",
           "employee_rate": 100.0,
           "client_rate": 150.0
        }
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('results')[0],
            expected_output
        )


class AssignEmployeeActivityToProjectTestCase(RHRSAPITestCase):
    users = [
        ('admin@email.com', 'password', 'Male'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.project = ProjectFactory()
        self.user = UserFactory()
        self.activity = ActivityFactory()

    @property
    def url(self):
        return reverse(
            'api_v1:task:project-assign-employee-activity',
            kwargs={
                'pk': self.project.id
            }
        ) + '?as=hr'

    @property
    def user_activity_url(self):
        return reverse(
            'api_v1:task:user-activity-list',
            kwargs={
                'project_id': self.project.id
            }
        )

    @property
    def payload(self):
        return {
           "user": [self.user.id],
           "activity": [self.activity.id],
           "employee_rate": 300,
           "client_rate": 400,
           "is_billable": True
        }

    def test_assign_employee_and_activity_to_project(self):
        response = self.client.post(
            self.url,
            self.payload
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(UserActivityProject.objects.filter(user=self.user.id).exists())

        response = self.client.get(self.user_activity_url, {"as": "hr"})
        self.assertEqual(
            response.json().get('count'),
            1
        )
        self.assertEqual(
            response.json().get('results')[0].get('user').get('id'),
            self.user.id
        )
