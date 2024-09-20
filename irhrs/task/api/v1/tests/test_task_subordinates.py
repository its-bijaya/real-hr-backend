from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from irhrs.task.api.v1.tests import TaskSetUp
from irhrs.task.constants import RESPONSIBLE_PERSON
from irhrs.task.models import Task
from irhrs.task.models.ra_and_core_tasks import ResultArea, CoreTask, UserResultArea
from irhrs.task.models.task import TaskAssociation
from irhrs.users.models import UserSupervisor, UserExperience

User = get_user_model()


class SubordinatesTaskTestCase(TaskSetUp):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        super().setUp()
        self.user_check = self.user.objects.get(email=self.users[0][0])

        # url for test
        self.task_url = reverse('api_v1:task:task-subordinate')

        # create supervisor and subordinates
        UserSupervisor.objects.bulk_create([
            UserSupervisor(
                user=user,
                supervisor=self.user_check,
                approve=True,
                deny=True,
                forward=False)
            for user in self.sys_user

        ])

    def test_task_assigned_to_subordinates(self):
        """
        test task assigned to subordinates list in noticeboard
        """

        # task created
        created_task_list = Task.objects.create(
            title=self.fake.name(),
            deadline=timezone.now() + relativedelta(months=1),
            created_by=self.user_check
        )

        # core task created
        created_core_task = self._create_core_task()

        # task assigned by supervisor to subordinates
        assign_task = TaskAssociation.objects.bulk_create(
            [
                TaskAssociation(
                    created_by=self.user_check,
                    user=user,
                    association=RESPONSIBLE_PERSON,
                    task=created_task_list,
                )
                for user in self.sys_user[1:]
            ])

        # core task added
        for task in assign_task:
            task.core_tasks.add(created_core_task)

        # get tasks assigned to subordinates
        get_task_summary = self.client.get(self.task_url, data={'subordinates': 'assignee'})

        # database query to get the task list
        select_related = [
            'created_by',
            'created_by__detail',
            'created_by__detail__division',
            'created_by__detail__organization',
        ]
        assigned_to_subordinates = Task.objects.base().filter(
            task_associations__user__in=self.user_check.subordinates_pks,
            task_associations__association=RESPONSIBLE_PERSON
        ).distinct().select_related(*select_related)

        assigned_task_subordinates_id = set()
        db_assigned_task_subordinates_id = set()

        # test task created is equal to task from response
        self.assertEqual(get_task_summary.json().get('results')[0].get('id'),
                         assigned_to_subordinates[0]
                         .id)
        for task_assigned_to_subordinates in get_task_summary.json().get(
            'results'
        )[0].get(
            'responsible_persons'
        ):
            # add task assigned subordinates id from response, added to a set
            assigned_task_subordinates_id.add(task_assigned_to_subordinates.get('user').get('id'))
            for user_id in assigned_to_subordinates.values('task_associations__user_id'):

                # task assigned subordinates id obtained from database, added to a set
                db_assigned_task_subordinates_id.add(user_id.get(
                    'task_associations__user_id'))
                if task_assigned_to_subordinates.get('user').get('id') == user_id.get(
                    'task_associations__user_id'):
                    # make sure that task assigned users are subordinates
                    self.assertTrue(task_assigned_to_subordinates.get('user').get('id') in
                                    self.user_check.subordinates_pks)

        # test user from database and user from response are same
        self.assertEqual(assigned_task_subordinates_id, db_assigned_task_subordinates_id)

        # test task is assigned to specific users only
        self.assertNotEqual(assigned_task_subordinates_id, self.user_check.subordinates_pks)

    def test_task_assigned_by_subordinates(self):
        """
        test task assigned by subordinates to supervisor
        """

        # get core task
        created_core_task = self._create_core_task()

        # create task as a subordinate and assign it to supervisor
        created_task_first = Task.objects.create(
            title=self.fake.name(),
            deadline=timezone.now() + relativedelta(months=1),
            created_by=self.sys_user[1]
        )
        assign_task_first = TaskAssociation.objects.create(
            created_by=self.sys_user[1],
            user=self.user_check,
            association=RESPONSIBLE_PERSON,
            task=created_task_first)

        # add core task
        assign_task_first.core_tasks.add(created_core_task)

        # create task as a second subordinate and assign it to supervisor
        created_task_second = Task.objects.create(
            title=self.fake.name(),
            deadline=timezone.now() + relativedelta(months=1),
            created_by=self.sys_user[2]
        )
        assign_task_second = TaskAssociation.objects.create(
            created_by=self.sys_user[2],
            user=self.user_check,
            association=RESPONSIBLE_PERSON,
            task=created_task_second,
        )
        assign_task_second.core_tasks.add(created_core_task)

        # get task assigned by subordinates
        get_task = self.client.get(self.task_url, data={'subordinates': 'assigned'})

        # get data from database
        assigned_by_subordinates = Task.objects.base().filter(
            created_by_id__in=self.user_check.subordinates_pks
        ).count()

        # test data from database is equal to data from response
        for task_assigned in get_task.json().get('results'):
            if task_assigned.get('id') == created_task_first.id:
                self.assertEqual(task_assigned.get('title'), created_task_first.title)
                self.assertEqual(task_assigned.get('created_by').get('id'),
                                 created_task_first.created_by.id)
                self.assertEqual(task_assigned.get('responsible_persons')[0].get('user').get(
                    'id'), assign_task_first.user_id)
            else:
                self.assertEqual(task_assigned.get('title'), created_task_second.title)
                self.assertEqual(task_assigned.get('created_by').get('id'),
                                 created_task_second.created_by.id)
                self.assertEqual(task_assigned.get('responsible_persons')[0].get('user').get(
                    'id'), assign_task_second.user_id)

        self.assertEqual(len(get_task.json().get('results')), assigned_by_subordinates)

    def _create_core_task(self):
        """
                We can assign task only to those users who has core task.
                we need to create the core task of users before assigning the task.
                this function call creates the core task
                :return: core task
                """
        result_area = ResultArea.objects.create(
            title='First Result Area',
            division=self.organization.divisions.first()
        )
        core_task = CoreTask.objects.create(
            result_area=result_area,
            title='First Core Task'
        )
        # core tasks is created and now we will assign to all three users
        for user in self.users:
            user_id = User.objects.get(email=user[0]).id
            experience_id = UserExperience.objects.get(user=user_id)
            user_result_area = UserResultArea.objects.create(
                user_experience=experience_id,
                result_area=result_area,
            )
            user_result_area.core_tasks.add(core_task)
        return core_task
