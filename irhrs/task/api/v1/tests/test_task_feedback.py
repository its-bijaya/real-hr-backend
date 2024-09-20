import random

from django.db.models import Count, Q
from django.urls import reverse

from irhrs.task.api.v1.tests import TaskSetUp
from irhrs.task.constants import (APPROVAL_PENDING, SCORE_NOT_PROVIDED, FORWARDED_TO_HR,
                                  NOT_ACKNOWLEDGED, APPROVED_BY_HR, ACKNOWLEDGED,
                                  ACKNOWLEDGE_PENDING, RESPONSIBLE_PERSON, COMPLETED)
from irhrs.task.models import Task


class TaskFeedBack(TaskSetUp):
    cycle_status = ['all', APPROVAL_PENDING, SCORE_NOT_PROVIDED,
                    ACKNOWLEDGE_PENDING, FORWARDED_TO_HR,
                    APPROVED_BY_HR, ACKNOWLEDGED, NOT_ACKNOWLEDGED]

    def setUp(self):
        super().setUp()

    def test_task_feedback(self):
        """
        --------------------------------------------------------------------------------------------
        test for task feedback page for normal user
        :return:
        """
        self._create_tasks()
        tasks = Task.objects.all().prefetch_related('task_associations')
        for task in tasks:
            task_associations = task.task_associations.all()
            for association in task_associations:
                association.cycle_status = random.choice(self.cycle_status[1:])
                association.save()
            task.status = COMPLETED
            task.save()

        self.client.login(email=self.users[1][0], password=self.users[1][1])
        fil = {
            'status': COMPLETED,
            'task_associations__user': self.sys_user[0],
            'task_associations__association': RESPONSIBLE_PERSON
        }
        stats = Task.objects.base().filter(
            **fil
        ).distinct().aggregate(
            all=Count('id', distinct=True),
            approval_pending=Count(
                'id',
                filter=Q(task_associations__cycle_status=APPROVAL_PENDING),
                distinct=True
            ),
            acknowledge_pending=Count(
                'id',
                filter=Q(task_associations__cycle_status=ACKNOWLEDGE_PENDING),
                distinct=True
            ),
            not_acknowledged=Count(
                'id',
                filter=Q(task_associations__cycle_status=NOT_ACKNOWLEDGED),
                distinct=True
            ),
            acknowledged=Count(
                'id',
                filter=Q(task_associations__cycle_status=ACKNOWLEDGED),
                distinct=True
            ),
            approved_by_hr=Count(
                'id',
                filter=Q(task_associations__cycle_status=APPROVED_BY_HR),
                distinct=True
            ),
            forwarded_to_hr=Count(
                'id',
                filter=Q(task_associations__cycle_status=FORWARDED_TO_HR),
                distinct=True
            ),
            score_not_provided=Count(
                'id',
                filter=Q(task_associations__cycle_status=SCORE_NOT_PROVIDED),
                distinct=True
            )
        )
        for status in self.cycle_status:
            fil_status = dict()
            data = {'as': 'responsible'}
            if not status == 'all':
                data.update({'cycle_status': status})
                fil_status.update({'task_associations__cycle_status': status})

            queryset = Task.objects.base().filter(
                **fil, **fil_status
            ).order_by('-modified_at').distinct()

            response = self.client.get(
                reverse(
                    'api_v1:task:task-pending-approvals'
                ),
                data=data
            )
            self.assertEqual(response.json().get('count'), queryset.count())
            results = response.json().get('results')
            for i, task in enumerate(queryset):
                self.assertEqual(results[i].get('id'), task.id)
                self.assertEqual(results[i].get('title'), task.title)

            response_stats = response.json().get('stats')
            self.assertEqual(response_stats.get('All'), stats.get('all'))
            self.assertEqual(response_stats.get('Approval Pending'), stats.get('approval_pending'))
            self.assertEqual(response_stats.get('Acknowledge Pending'),
                             stats.get('acknowledge_pending'))
            self.assertEqual(response_stats.get('Not Acknowledged'), stats.get('not_acknowledged'))
            self.assertEqual(response_stats.get('Acknowledged'), stats.get('acknowledged'))
            self.assertEqual(response_stats.get('Approved By HR'), stats.get('approved_by_hr'))
            self.assertEqual(response_stats.get('Forwarded To HR'), stats.get('forwarded_to_hr'))
            self.assertEqual(response_stats.get('Score Not Provided'),
                             stats.get('score_not_provided'))
