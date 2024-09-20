import json
import random
from datetime import timedelta
from random import randint

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from faker import Factory
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.organization.models import OrganizationBranch
from irhrs.task.api.v1.serializers.task import TaskSerializer
from irhrs.task.api.v1.tests.factory import (ResultAreaFactory, CoreTaskFactory,
                                             UserResultAreaFactory)
from irhrs.task.constants import (ON_HOLD, CLOSED, MAJOR, MINOR,
                                  CRITICAL, COMPLETED, IN_PROGRESS, PENDING, RESPONSIBLE_PERSON,
                                  OBSERVER)
from irhrs.task.models.task import Task


class TaskSetUp(RHRSTestCaseWithExperience):
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
    task_priority = [MAJOR, MINOR, CRITICAL]
    task_status = [PENDING, IN_PROGRESS, COMPLETED, ON_HOLD, CLOSED]
    task_status_dict = {
        PENDING: 'PENDING',
        IN_PROGRESS: 'IN_PROGRESS',
        COMPLETED: 'COMPLETED',
        ON_HOLD: 'ON_HOLD',
        CLOSED: 'CLOSED'
    }
    _conditions = ['delayed', 'on_time']
    associations = ['responsible', 'observer', 'creator']
    involvement_choices = {
        'responsible': RESPONSIBLE_PERSON,
        'observer': OBSERVER
    }
    recurring = {}

    def setUp(self):
        super().setUp()
        self.user = get_user_model()
        # self.sys_user = [self.user.objects.get(email=user[0]) for user in self.users[1:]]
        self.sys_user = list(self.user.objects.filter(
            email__in=[user[0] for user in self.users[1:]]
        ).order_by('id'))
        self.branch = OrganizationBranch.objects.create(
            organization=self.organization,
            branch_manager=None,
            name=self.fake.word(),
            description='zzzasd',
            contacts=json.dumps({
                'Mobile': '1234567890'
            }),
            email='',
            code='',
            mailing_address='',
        )
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        result_area = ResultAreaFactory(division=self.division)
        core_tasks = [CoreTaskFactory(result_area=result_area, order=i) for i in range(10)]
        for user in self.sys_user:
            ura = UserResultAreaFactory(
                result_area=result_area,
                user_experience=user.current_experience
            )
            ura.core_tasks.add(*core_tasks)
        self.responsible_person = []
        self.observer = []
        self.task_list_url = reverse(
            'api_v1:task:task-list'
        )

    @property
    def data(self):
        data = {
            "observers": self.observer,
            "responsible_persons": self.responsible_person,
            "priority": "MINOR",
            "check_lists": [self.fake.text(max_nb_chars=10) for _ in range(0, 5)],
            "title": self.fake.text(max_nb_chars=100),
            "changeable_deadline": False,
            "deadline": timezone.now() + timedelta(days=5),
            "starts_at": timezone.now() + timedelta(days=1),
            "description": self.fake.text(),
            "project": None,
            "recurring": self.recurring if self.recurring else None,
            "parent": None
        }
        return data

    def _create_tasks(self):
        """
        helps to create all task needed for testing
        :return:
        """

        """
        --------------------------------------------------------------------------------------------
        data to replicate assigned to me
        """
        for user in self.sys_user[:-1]:
            self.responsible_person.append({
                'user': user.id,
                'core_tasks': random.choices(
                    list(
                        user.current_experience.user_result_areas.first().core_tasks.all().values_list(
                            'id', flat=True)
                    )
                )
            })
        self.observer.append({
            'user': self.sys_user[-1].id
        })

        for _ in range(randint(1, 20)):
            response = self.client.post(
                path=self.task_list_url,
                data=self.data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        """
        --------------------------------------------------------------------------------------------
        data to replicate observed by me
        """
        self.responsible_person = []
        for user in self.sys_user[1:]:
            self.responsible_person.append({
                'user': user.id,
                'core_tasks': random.choices(
                    list(
                        user.current_experience.user_result_areas.first().core_tasks.all().values_list(
                            'id', flat=True)
                    )
                )
            })
        self.observer[0].update({
            'user': self.sys_user[0].id
        })

        for _ in range(randint(1, 20)):
            response = self.client.post(
                path=self.task_list_url,
                data=self.data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        """
        --------------------------------------------------------------------------------------------
        data to replicate assigned by me
        """
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        self.observer[0].update({
            'user': self.user.objects.get(email=self.users[0][0]).id
        })

        for _ in range(randint(1, 20)):
            response = self.client.post(
                path=self.task_list_url,
                data=self.data,
                format='json'
            )
            if response.status_code == 400:
                print(json.dumps(response.json(), default=str, indent=4))
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        tasks = Task.objects.all()
        for task in tasks:
            task.priority = random.choice(self.task_priority)
            task.status = random.choice(self.task_status)
            start_at = timezone.now() + timedelta(days=random.randint(-11, 11))
            task.deadline = start_at + timedelta(days=2)
            task.starts_at = start_at
            task.start = start_at + timedelta(random.randint(-1, 1))
            if task.status == COMPLETED:
                task.finish = task.deadline + timedelta(random.randint(-1, 1))
            task.save()

    @staticmethod
    def _add_task_using_serializer(user, data):
        task_ser = TaskSerializer(
            context={
                'request': type(
                    'Request',
                    (object,),
                    {
                        'method': 'POST',
                        'user': user,
                    }
                )
            },
            data=data
        )
        task_ser.is_valid(raise_exception=True)
        task = task_ser.save(created_by=user)
        return task

    def create_single_task(self):
        self.responsible_person = []
        for user in self.sys_user[1:-1]:
            self.responsible_person.append({
                'user': user.id,
                'core_tasks': random.choices(
                    list(
                        user.current_experience.user_result_areas.first().core_tasks.all().values_list(
                            'id', flat=True)
                    )
                )
            })
        self.observer = [
            {
                'user': self.sys_user[-1].id
            }
        ]
        task_creator = self.user.objects.get(email=self.users[0][0])
        return self._add_task_using_serializer(
            user=task_creator,
            data=self.data
        )
