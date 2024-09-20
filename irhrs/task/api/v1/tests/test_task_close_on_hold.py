from django.db.models import Count, Q
from django.urls import reverse

from irhrs.task.api.v1.tests import TaskSetUp
from irhrs.task.constants import CLOSED, ON_HOLD, RESPONSIBLE_PERSON, OBSERVER
from irhrs.task.models import Task


class TaskCloseOnHold(TaskSetUp):
    def setUp(self):
        super().setUp()

    def test_close_on_hold(self):
        self._create_tasks()
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        _STATUS_IN = Q(status__in=[CLOSED, ON_HOLD])
        close_on_hold_stats = Task.objects.my_tasks(self.sys_user[0]).aggregate(
            created=Count(
                'id',
                filter=_STATUS_IN & Q(created_by=self.sys_user[0]),
                distinct=True
            ),
            created_closed=Count(
                'id',
                filter=Q(created_by=self.sys_user[0]) &
                       Q(status=CLOSED), distinct=True
            ),
            responsible=Count(
                'id',
                filter=_STATUS_IN & Q(
                    task_associations__association=RESPONSIBLE_PERSON) & Q(
                    task_associations__user=self.sys_user[0]),
                distinct=True
            ),
            responsible_closed=Count(
                'id',
                filter=Q(status=CLOSED) & Q(
                    task_associations__association=RESPONSIBLE_PERSON) & Q(
                    task_associations__user=self.sys_user[0]),
                distinct=True
            ),
            observed=Count(
                'id',
                filter=_STATUS_IN & Q(
                    task_associations__association=OBSERVER) & Q(
                    task_associations__user=self.sys_user[0]),
                distinct=True),
            observed_closed=Count(
                'id',
                filter=Q(status=CLOSED) & Q(
                    task_associations__association=OBSERVER) & Q(
                    task_associations__user=self.sys_user[0]),
                distinct=True
            )
        )

        for association in self.associations:
            if association == 'responsible':
                my_tasks = Task.objects.as_responsible(self.sys_user[0])
            elif association == 'observer':
                my_tasks = Task.objects.as_observer(self.sys_user[0])
            else:
                my_tasks = Task.objects.as_creator(self.sys_user[0])

            for _status in self.task_status[-2:]:
                queryset = my_tasks.filter(status=_status)

                result = self.client.get(
                    reverse(
                        'api_v1:task:task-overview-v2-extra-tasks'
                    ),
                    data={
                        'status': _status,
                        'as': association
                    }
                )

                self._check_task_info_for_its_correctness(
                    response=result,
                    queryset=queryset,
                    stats=close_on_hold_stats
                )

    def _check_task_info_for_its_correctness(self, response, queryset, stats):
        created = {
            'all': stats.get('created'),
            'closed': stats.get('created_closed'),
            'on_hold': stats.get('created') - stats.get('created_closed')
        }
        responsible = {
            'all': stats.get('responsible'),
            'closed': stats.get('responsible_closed'),
            'on_hold': stats.get('responsible') - stats.get('responsible_closed')
        }
        observed = {
            'all': stats.get('observed'),
            'closed': stats.get('observed_closed'),
            'on_hold': stats.get('observed') - stats.get('observed_closed')
        }
        closed_and_hold = response.json().get('closed_and_hold')
        self.assertDictEqual(created, closed_and_hold.get('created'))
        self.assertDictEqual(responsible, closed_and_hold.get('responsible'))
        self.assertDictEqual(observed, closed_and_hold.get('observed'))

        count = response.json().get('count')
        results = response.json().get('results')

        self.assertEqual(count, queryset.count(), 'Must be equal')
        for i, task in enumerate(queryset):
            self.assertEqual(task.id, results[i].get('id'))
            self.assertEqual(task.title, results[i].get('title'))
            self.assertEqual(task.priority, results[i].get('priority'))
            self.assertEqual(task.status, results[i].get('status'))
