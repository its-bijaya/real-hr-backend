
from dateutil.relativedelta import relativedelta
from django.db.models import Q, F
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.task.api.v1.tests import TaskSetUp
from irhrs.task.constants import (RESPONSIBLE_PERSON, ON_HOLD, CLOSED, OBSERVER, MAJOR, MINOR,
                                  CRITICAL, COMPLETED, IN_PROGRESS, PENDING)
from irhrs.task.models.task import Task


class TaskOverview(TaskSetUp):
    def test_task_stat(self):
        """
        tested for stats of task for observed by me, assigned by me and assigned to me
        :return:
        """
        self._create_tasks()
        """
        --------------------------------------------------------------------------------------------
        response from the stat url
        """
        response = self.client.get(
            reverse(
                'api_v1:task:task-overview-v2-stat'
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tasks = Task.objects.all()
        for task in tasks:
            task.start_at = timezone.now() - relativedelta(days=1)
            task.save()

        current_date = timezone.now().date()
        _STATUS__NOT_IN = ~Q(status__in=[CLOSED, ON_HOLD])

        fil = dict(
            starts_at__date__gte=current_date.replace(day=1),
            task_associations__user=self.sys_user[0]
        )
        assigned_to_me = Task.objects.filter(
            Q(**fil) &
            Q(task_associations__association=RESPONSIBLE_PERSON) &
            _STATUS__NOT_IN
        ).count()

        observed_by_me = Task.objects.filter(
            Q(**fil) &
            Q(task_associations__association=OBSERVER) &
            _STATUS__NOT_IN
        ).count()

        start_of_month = timezone.now().date().replace(day=1)
        assigned_by_me = Task.objects.base().filter(
            starts_at__date__gte=start_of_month
        ).filter(
            Q(created_by=self.sys_user[0]) & _STATUS__NOT_IN
        ).distinct().count()

        self.assertEqual(response.json().get('assigned_by_me'), assigned_by_me)
        self.assertEqual(response.json().get('assigned_to_me'), assigned_to_me)
        self.assertEqual(response.json().get('observed'), observed_by_me)

    def test_for_task_info(self):
        self.task_info_url = reverse(
            'api_v1:task:task-overview-v2-list'
        )
        self._create_tasks()

        self.client.login(email=self.users[1][0], password=self.users[1][1])

        """
        --------------------------------------------------------------------------------------------
        as responsible person, as observer, as creator
        """
        for association in self.associations:
            response = self.client.get(self.task_info_url, data={'as': association, 'limit': 0})
            if association == 'responsible':
                my_tasks = Task.objects.as_responsible(self.sys_user[0])
            elif association == 'observer':
                my_tasks = Task.objects.as_observer(self.sys_user[0])
            else:
                my_tasks = Task.objects.as_creator(self.sys_user[0])

            self._check_task_info_for_its_correctness(response=response, my_tasks=my_tasks)

            for _status in self.task_status[:-2]:
                queryset = my_tasks.filter(status=_status)
                for _condition in self._conditions:
                    result = self.client.get(
                        self.task_info_url,
                        data={
                            'as': association,
                            'pre_condition': self.task_status_dict.get(_status).lower(),
                            'post_condition': _condition.lower(),
                            'recent': False
                        }
                    )

                    if _condition == 'on_time':
                        if _status == COMPLETED:
                            queryset = queryset.filter(deadline__gt=F('finish'))
                        else:
                            queryset = queryset.filter(deadline__gte=timezone.now())
                    else:
                        if _status == COMPLETED:
                            queryset = queryset.filter(deadline__lt=F('finish'))
                        else:
                            queryset = queryset.filter(deadline__lte=timezone.now())

                    self._check_task_info_for_its_correctness(
                        response=result,
                        my_tasks=my_tasks,
                        queryset=queryset
                    )

    def _check_task_info_for_its_correctness(self, response, my_tasks, queryset=None):
        def _test_for_stats():
            all_task = my_tasks.count()
            critical = my_tasks.filter(priority=CRITICAL).count()
            minor = my_tasks.filter(priority=MINOR).count()
            major = my_tasks.filter(priority=MAJOR).count()
            recent = my_tasks.filter(created_at__date=timezone.now().date()).count()

            self.assertEqual(response.json().get('info').get('recent'), recent)
            self.assertEqual(response.json().get('info').get('critical'), critical)
            self.assertEqual(response.json().get('info').get('major'), major)
            self.assertEqual(response.json().get('info').get('minor'), minor)
            self.assertEqual(response.json().get('info').get('all'), all_task)

            all_summary = {
                'all': my_tasks.count(),
                'delayed': my_tasks.filter(deadline__lte=timezone.now()).count()
            }
            closed = {
                'all': my_tasks.filter(status=CLOSED).count(),
                'delayed': None,
                'on_time': None
            }
            completed = {
                'all': my_tasks.filter(status=COMPLETED).count(),
                'delayed': my_tasks.filter(status=COMPLETED, deadline__lt=F('finish')).count()
            }
            in_progress = {
                'all': my_tasks.filter(status=IN_PROGRESS).count(),
                'delayed': my_tasks.filter(status=IN_PROGRESS, deadline__lte=timezone.now()).count()
            }
            on_hold = {
                'all': my_tasks.filter(status=ON_HOLD).count(),
                'delayed': None,
                'on_time': None
            }
            pending = {
                'all': my_tasks.filter(status=PENDING).count(),
                'delayed': my_tasks.filter(status=PENDING, deadline__lte=timezone.now()).count()
            }

            completed.update({
                'on_time': completed.get('all') - (
                    completed.get('delayed') if completed.get('delayed') else 0)
            })

            in_progress.update({
                'on_time': in_progress.get('all') - (
                    in_progress.get('delayed') if in_progress.get('delayed') else 0)
            })

            pending.update({
                'on_time': pending.get('all') - (
                    pending.get('delayed') if pending.get('delayed') else 0)
            })

            all_summary.update({
                'on_time': all_summary.get('all') - (
                    all_summary.get('delayed') if all_summary.get('delayed') else 0)
            })

            self.assertDictEqual(all_summary, response.json().get('summary')['all'])
            self.assertDictEqual(pending, response.json().get('summary')['pending'])
            self.assertDictEqual(in_progress, response.json().get('summary')['in_progress'])
            self.assertDictEqual(completed, response.json().get('summary')['completed'])
            self.assertDictEqual(on_hold, response.json().get('summary')['on_hold'])
            self.assertDictEqual(closed, response.json().get('summary')['closed'])

        def _test_for_result():
            count = response.json().get('count')
            results = response.json().get('results')
            self.assertEqual(count, queryset.count(), 'Must be equal')
            ids = [result.get('id') for result in results] if results else []
            if ids:
                self.assertTrue(queryset.filter(id__in=ids).exists())
            else:
                self.assertIsNone(queryset)

        _test_for_stats()
        if queryset:
            _test_for_result()

    def test_for_task_efficiency(self):
        """
        :return:
        """

        # TODO: Shital while testing for hr and supervisor must test this section
        # also write test case covering task report page
        pass
