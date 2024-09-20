import random
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.core.utils.common import get_today
from irhrs.task.api.v1.tests import TaskSetUp
from irhrs.task.constants import RESPONSIBLE_PERSON
from irhrs.task.models.task import Task, RecurringTaskDate
from irhrs.task.tasks.recurring import create_recurring_task


class TestRecurringTask(TaskSetUp):
    recurring_rules = [
        "FREQ=DAILY;INTERVAL=1;COUNT=5",
        "FREQ=WEEKLY;INTERVAL=1;COUNT=5;BYDAY=SU"
    ]
    recurring_time = {
        'DAILY': 1,
        'WEEKLY': 7
    }

    def setUp(self):
        super().setUp()

    def test_recurring_task_api(self):
        """
        tested recurring task api for normal user view
        :return:
        """
        self.recurring = {
            'recurring_first_run': get_today(),
            'recurring_rule': random.choice(self.recurring_rules)
        }

        self._create_tasks()
        create_recurring_task()
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        """
        --------------------------------------------------------------------------------------------
        without filters
        """
        queryset = Task.objects.recurring(self.sys_user[0])
        queryset = queryset.filter(parent__isnull=True)

        response = self.client.get(
            reverse(
                'api_v1:task:task-recurring'
            ),
        )
        self._validate_response(response=response, queryset=queryset)

        """
        --------------------------------------------------------------------------------------------
        with priority filters
        """
        for priority in self.task_priority:
            queryset = Task.objects.recurring(self.sys_user[0])
            queryset = queryset.filter(parent__isnull=True, priority=priority)

            response = self.client.get(
                reverse(
                    'api_v1:task:task-recurring'
                ),
                data={
                    'priority': priority
                }
            )
            self._validate_response(response=response, queryset=queryset)

        """
        --------------------------------------------------------------------------------------------
        with assignee filters
        """
        for user in self.sys_user:
            queryset = Task.objects.recurring(self.sys_user[0])
            queryset = queryset.filter(
                parent__isnull=True,
                task_associations__user_id=user.id,
                task_associations__association=RESPONSIBLE_PERSON
            )

            response = self.client.get(
                reverse(
                    'api_v1:task:task-recurring'
                ),
                data={
                    'assignee': user.id,
                }
            )
            self._validate_response(response=response, queryset=queryset)

    def test_recurring_task(self):
        """
        unit test to check whether recurring rule background task generates task or not
        :return:
        """
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
        recurring_rule = self.recurring_rules[0]
        self.recurring = {
            'recurring_first_run': get_today(),
            'recurring_rule': recurring_rule
        }

        recurring_count = int(recurring_rule.split(';')[2].split('=')[-1])
        task = self.create_single_task()

        # to check whether it creates task for recurring rule or not
        for index in range(1, 3):
            return_date = timezone.now() + timezone.timedelta(
                days=self.recurring_time.get(
                    recurring_rule.split(';')[0].split('=')[-1]
                ) * index
            )
            with patch('django.utils.timezone.now', return_value=return_date):
                create_recurring_task()
                recurring_task_count = RecurringTaskDate.objects.filter(template=task)
                self.assertEqual(
                    recurring_task_count.count(),
                    recurring_count,
                    'Recurring task count must be equal to recurring rule count'
                )
                created_task = recurring_task_count.filter(created_task__isnull=False)
                self.assertEqual(
                    created_task.count(),
                    index,
                    "Must return task count for each day"
                )

        # to check whether it creates pending queued tasks or not while running background task
        task = self.create_single_task()
        with patch('django.utils.timezone.now',
                   return_value=timezone.now() + timezone.timedelta(days=3)):
            create_recurring_task()
            recurring_task_count = RecurringTaskDate.objects.filter(template=task)
            self.assertEqual(
                recurring_task_count.count(),
                recurring_count,
                'Recurring task count must be equal to recurring rule count'
            )
            created_task = recurring_task_count.filter(created_task__isnull=False)
            self.assertEqual(
                created_task.count(),
                1,
                "Must return single instance of task generating only for that day"
            )


    def _validate_response(self, response, queryset):
        result = response.json().get('results')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), queryset.count())
        for i, task in enumerate(queryset):
            self.assertEqual(result[i].get('id'), task.id)
            self.assertEqual(result[i].get('title'), task.title)
            self.assertEqual(result[i].get('priority'), task.priority)
