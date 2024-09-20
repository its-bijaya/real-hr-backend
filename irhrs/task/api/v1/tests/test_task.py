import json
import random
from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from rest_framework import status

from irhrs.organization.api.v1.tests.factory import EmploymentLevelFactory
from irhrs.task.api.v1.tests import TaskSetUp
from irhrs.task.api.v1.tests.factory import ActivityFactory
from irhrs.task.models import Task, TaskSettings
from irhrs.task.models.settings import Project, UserActivityProject


class TaskOverview(TaskSetUp):

    def setUp(self):
        super().setUp()

    def get_responsible_person(self, users=None):
        self.responsible_person = []
        if users:
            user_list = [user for user in self.sys_user[:-1] if user in users]
        else:
            user_list = self.sys_user[:-1]

        for user in user_list:
            self.responsible_person.append({
                'user': user.id,
                'core_tasks': random.choices(
                    list(
                        user.current_experience.user_result_areas.first().core_tasks.all().values_list(
                            'id', flat=True)
                    )
                )
            })

    def test_for_task_creation(self):
        """
        test for task creation covering different scenario for task creation
        :return:
        """

        """
        --------------------------------------------------------------------------------------------
        test for task creation
        """
        self.get_responsible_person()
        self.observer.append({
            'user': self.sys_user[-1].id
        })

        response = self.client.post(
            path=self.task_list_url,
            data=self.data,
            format='json'
        )
        self._test_for_validation_while_creating_task(response=response)

        """
        --------------------------------------------------------------------------------------------
        scenario => task creator as a responsible person
        result => must not create task for this scenario
        """
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        self._test_for_invalid_task_creation(
            field='non_field_errors',
            message='Task Creator cannot be assigned as Responsible Person'
        )
        """
        --------------------------------------------------------------------------------------------
        scenario => task creator as a observer person
        result => must not create task for this scenario
        """
        self.observer = [{
            'user': self.sys_user[0].id
        }]
        self.responsible_person.pop(0)
        self._test_for_invalid_task_creation(
            field='non_field_errors',
            message='Task Creator cannot be assigned as Observer'
        )
        """
        --------------------------------------------------------------------------------------------
        scenario => trying to create task without any core task for responsible person
        result => must not create task for this scenario
        """
        self.observer = [{
            'user': self.sys_user[-1].id
        }]
        self.responsible_person.append({
            'user': self.user.objects.get(email=self.users[0][0]).id,
            'core_tasks': []
        })
        self._test_for_invalid_task_creation(
            field='responsible_persons',
            message='Core tasks are required for responsible person'
        )
        """
        --------------------------------------------------------------------------------------------
        scenario => trying to create task without any core task for responsible person
        result => must not create task for this scenario
        """
        self.observer = [{
            'user': self.sys_user[-1].id
        }]
        self.responsible_person = [
            {
                'user': self.sys_user[-1].id,
                'core_tasks': random.choices(
                    list(
                        self.sys_user[
                            -1].current_experience.user_result_areas.first().core_tasks.all().values_list(
                            'id', flat=True)
                    )
                )
            }
        ]
        self._test_for_invalid_task_creation(
            field='non_field_errors',
            message='A person cannot be added as Responsible and Observer at the same time'
        )
        """
        --------------------------------------------------------------------------------------------
        scenario => trying to create task with past deadline
        result => must not create task for this scenario
        """
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.get_responsible_person()
        data = self.data
        data.update({
            'deadline': timezone.now() - timedelta(days=2)
        })
        self._test_for_invalid_task_creation(
            field='deadline',
            message='Cannot Set Deadline To Past',
            data=data
        )
        """
        --------------------------------------------------------------------------------------------
        scenario => trying to create task with past start date
        result => must not create task for this scenario
        """
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.get_responsible_person()
        data = self.data
        data.update({
            'starts_at': timezone.now() - timedelta(days=2)
        })
        self._test_for_invalid_task_creation(
            field='starts_at',
            message='Start Time should be in Future',
            data=data
        )

        """
        --------------------------------------------------------------------------------------------
        scenario => added task to a project by project member
        result => must create task for this scenario
        """
        project = Project.objects.create(name=self.fake.word(),
                                             description=self.fake.text(max_nb_chars=100), is_billable=True)
        activity = ActivityFactory()
        UserActivityProject.objects.create(
            project=project,
            activity=activity,
            user=self.created_users[0],
            is_billable=True
        )
        # project.members.add(*self.sys_user[:-1])
        # project.members.add(self.user.objects.get(email=self.users[0][0]))
        data = self.data
        data.update({
            'project': project.id
        })
        response = self.client.post(
            path=self.task_list_url,
            data=data,
            format='json'
        )
        self._test_for_validation_while_creating_task(response=response)

        """
        --------------------------------------------------------------------------------------------
        scenario => added task to a project by non project member
        result => must not create task for this scenario
        """
        self.client.login(email=self.users[-1][0], password=self.users[-1][1])
        self._test_for_invalid_task_creation(
            field='project',
            message='You must be creator or member of this project',
            data=data
        )

    def _test_for_validation_while_creating_task(self, response):
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        task = Task.objects.get(id=response.json().get('id'))
        self.assertEqual(task.check_lists.count(), len(response.json().get('check_lists')))

        responsible_persons = [rp.get('user') for rp in self.responsible_person]
        self.assertTrue(task.responsible_persons.filter(user_id__in=responsible_persons).exists())
        _rp = [rp.get('user') for rp in response.json().get('responsible_persons')]
        responsible_persons.sort()
        _rp.sort()
        self.assertEqual(
            responsible_persons,
            _rp
        )

    def _test_for_invalid_task_creation(self, field, message, data=None):
        response = self.client.post(
            path=self.task_list_url,
            data=self.data if not data else data,
            format='json'
        )
        if message == 'project':
            print(json.dumps(response.json(), default=str, indent=4))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            isinstance(response.json().get(field), list),
            message
        )

    def test_task_assign_with_different_higher_level_allowed_setting(self):

        detail = self.admin.detail
        detail.employment_level = EmploymentLevelFactory(organization=self.organization,
                                                         order_field=5)
        detail.save()

        higher_level = EmploymentLevelFactory(organization=self.organization, order_field=10)
        lower_level = EmploymentLevelFactory(organization=self.organization, order_field=5)

        cases = [
            {
                "can_assign_to_higher_employment_level": True,
                "level": higher_level,
                "is_valid": True
            },
            {
                "can_assign_to_higher_employment_level": False,
                "level": higher_level,
                "is_valid": False
            },
            {
                "can_assign_to_higher_employment_level": True,
                "level": lower_level,
                "is_valid": True
            },
            {
                "can_assign_to_higher_employment_level": False,
                "level": lower_level,
                "is_valid": True
            }
        ]

        for case in cases:
            with self.atomicSubTest(msg=str(case)):
                self.client.force_login(self.admin)

                user = self.created_users[1]
                dt = user.detail
                dt.employment_level = case["level"]
                dt.save()

                self.get_responsible_person(users=[user])
                payload = self.data

                with patch(
                    'irhrs.task.models.settings.TaskSettings.get_for_organization',
                    return_value=TaskSettings(
                        organization=self.organization,
                        can_assign_to_higher_employment_level=case[
                            'can_assign_to_higher_employment_level']
                    )
                ):
                    response = self.client.post(self.task_list_url, payload, format='json')
                    if case["is_valid"]:
                        self.assertEqual(response.status_code, 201, response.data)
                    else:
                        self.assertEqual(response.status_code, 400)
                        self.assertEqual(
                            response.data.get('responsible_persons'),
                            ['Task assignment to higher employment level not allowed.'],
                            response.data
                        )

