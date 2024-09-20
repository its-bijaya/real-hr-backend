from dateutil.relativedelta import relativedelta
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone

from irhrs.task.api.v1.tests import TaskSetUp
from irhrs.task.constants import (RESPONSIBLE_PERSON)
from irhrs.task.models.task import TaskAssociation


class TaskAssignedByMe(TaskSetUp):
    def setUp(self):
        super().setUp()

    def test_for_top_task_assignee(self):
        self._create_tasks()
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        start_date = (timezone.now() - relativedelta(months=1)).date()
        end_date = timezone.now().date()
        top_assignee = TaskAssociation.objects.filter(
            created_by=self.sys_user[0],
            association=RESPONSIBLE_PERSON
        ).values('user').annotate(
            total_assigned=Count('task', distinct=True)
        ).order_by('-total_assigned')

        response = self.client.get(
            reverse("api_v1:task:task-overview-v2-top-assignee"),
            data={
                'as': 'hr',
                'ordering': '-total_assigned',
                'start_date': start_date,
                'end_date': end_date
            }
        )
        for i, assignee in enumerate(top_assignee):
            self.assertEqual(
                response.json().get('results')[i].get('total_assigned'),
                assignee.get('total_assigned')
            )

            self.assertEqual(
                response.json().get('results')[i].get('user').get('id'),
                assignee.get('user')
            )
