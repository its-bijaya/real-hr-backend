
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.task.constants import OBSERVER, RESPONSIBLE_PERSON
from irhrs.task.models import Task
from irhrs.task.models.ra_and_core_tasks import ResultArea, CoreTask, UserResultArea
from irhrs.users.models import User
from irhrs.users.models import UserExperience


class TaskTestCase(RHRSTestCaseWithExperience):
    """
    -----------------------------------------------------------------------------------
    scenario:
    Task may be assigned by me or assigned to me or observed by me.
    test is written to count the recent task and total task in assigned by me , observed by be
    and assigned to me.
    """
    users = [
        ('hellomanone@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
        ('hellomantwo@hello.com', 'secretThing', 'Male', 'Sales Person'),
        ('hellomanthree@hello.com', 'secretThingIsThis', 'Male', 'Clerk')
    ]
    organization_name = "Google"
    division_name = "Programming"
    division_ext = 123

    post_list_url = reverse('api_v1:task:task-list')
    task_summary_url = reverse('api_v1:task:task-summary-list')

    def setUp(self):
        super().setUp()
        self.user = get_user_model()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        # get details of all users
        self.user_detail_first = User.objects.get(email=self.users[0][0])
        self.user_detail_second = User.objects.get(email=self.users[1][0])
        self.user_detail_third = User.objects.get(email=self.users[2][0])

    def test_task_assign_summary(self):
        """
        test task assign count of each user
        :return:
        """
        core_task_created = self._create_core_task()
        assigned_task = self._assign_task(core_task_created)

        # test task is created by same user or not
        self.assertEqual(get_user_model().objects.get(id=assigned_task.data.get('created_by')).email, self.users[0][0])

        # test task is created on same date or not
        created_date_str = assigned_task.data.get('created_at')[:10]
        created_date = parse(created_date_str).date()
        self.assertEqual(created_date, timezone.now().date())

        # test either task data displayed in noticeboard is correct or not
        response_summary = self.client.get(self.task_summary_url)

        get_assigned_by_me = response_summary.data.get('assigned_by_me')

        # get users task summary from database
        assigned_by_me_count = Task.objects.filter(created_by=self.user_detail_first).count()
        self.assertEqual(get_assigned_by_me, assigned_by_me_count)

        # test by creating another data
        data = {
            'title': 'Second Task',
            'starts_at': timezone.now() + timezone.timedelta(days=5),
            'deadline': timezone.now() + timezone.timedelta(days=20),
            'responsible_persons': [
                {
                    'user': self.user_detail_third.id,
                    'core_tasks': [core_task_created.id, ]
                },
            ],
            'observers': [
                {
                    "user": self.user_detail_second.id
                },
            ]
        }

        assigned_task = self._assign_task(core_task_created, data)
        # test task is created by same user or not
        self.assertEqual(get_user_model().objects.get(id=assigned_task.data.get('created_by')).email, self.users[0][0])

        # test task is created on same date or not
        created_date_str = assigned_task.data.get('created_at')[:10]
        created_date = parse(created_date_str).date()
        self.assertEqual(created_date, timezone.now().date())

        # now  check the count of total task assigned by me
        response_summary = self.client.get(self.task_summary_url)

        get_assigned_by_me = response_summary.data.get('assigned_by_me')
        assigned_by_me_count = Task.objects.filter(created_by=self.user_detail_first).count()
        self.assertEqual(get_assigned_by_me, assigned_by_me_count)

        # change the created date to past to test assigned by me recently
        task_created = Task.objects.get(id=assigned_task.data.get('id'))
        task_created.created_at = timezone.now()-relativedelta(days=10)
        task_created.save()

        # now check the count created today i.e recently
        response_summary = self.client.get(self.task_summary_url)
        get_assigned_by_me_recently = response_summary.data.get('assigned_by_me_recently')
        assigned_by_me_count = Task.objects.filter(created_by=self.user_detail_first,
                                                   created_at__date=timezone.now().date()).count()
        self.assertEqual(get_assigned_by_me_recently, assigned_by_me_count)

        # assigner cannot be a responsible person
        data = {
            'title': 'Second Task',
            'starts_at': timezone.now() + relativedelta(days=5),
            'deadline': timezone.now() + relativedelta(days=20),
            'responsible_persons': [
                {
                    'user': self.user_detail_first.id,
                    'core_tasks': [core_task_created.id, ]
                },
            ],
            'observers': [
                {
                    "user": self.user_detail_third.id
                },
            ]
        }

        # Here assigner and responsible person are same
        response = self.client.post(self.post_list_url, data=data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data.get('non_field_errors')[0]),
                         'Task Creator cannot be assigned as Responsible Person')

        # Now login from another user
        self.client.login(email=self.users[1][0], password=self.users[1][1])

        # test either task data displayed in noticeboard is correct or not
        get_task_summary = self.client.get(self.task_summary_url)
        observed_by_count = Task.objects.filter(task_associations__user=self.user_detail_second,
                                                task_associations__association=OBSERVER).count()
        assigned_by_me_count = Task.objects.filter(created_by=self.user_detail_second).count()
        assigned_to_me_count = Task.objects.filter(task_associations__user=self.user_detail_second,
                                                   task_associations__association=RESPONSIBLE_PERSON).count()
        self.assertEqual(get_task_summary.data.get('observed_by_me'),
                         observed_by_count)
        self.assertEqual(get_task_summary.data.get('assigned_to_me'), assigned_to_me_count)
        self.assertEqual(get_task_summary.data.get('assigned_by_me'), assigned_by_me_count)

        # now again task is created from another user i.e now second user is assigner
        data = {
            'title': 'Second Task',
            'starts_at': timezone.now() + relativedelta(days=5),
            'deadline': timezone.now() + relativedelta(days=20),
            'responsible_persons': [
                {
                    'user': self.user_detail_first.id,
                    'core_tasks': [core_task_created.id, ]
                },
            ],
            'observers': [
                {
                    "user": self.user_detail_third.id
                },
            ]
        }
        assigned_task = self._assign_task(core_task_created, data)
        # test either logged user and task created user is same or not
        self.assertEqual(get_user_model().objects.get(id=assigned_task.data.get('created_by')).email, self.users[1][0])

        # Is created on same date or not
        created_date_str = assigned_task.data.get('created_at')[:10]
        created_date = parse(created_date_str).date()
        self.assertEqual(created_date, timezone.now().date())

        # get count from database
        observed_by_count = Task.objects.filter(task_associations__user=self.user_detail_second,
                                                task_associations__association=OBSERVER).count()
        assigned_by_me_count = Task.objects.filter(created_by=self.user_detail_second).count()
        assigned_to_me_count = Task.objects.filter(task_associations__user=self.user_detail_second,
                                                   task_associations__association=RESPONSIBLE_PERSON).count()

        # now  check the count of assigned by me either it is correctly displayed in noticeboard or not
        get_task_summary = self.client.get(self.task_summary_url)
        self.assertEqual(get_task_summary.data.get('observed_by_me'),
                         observed_by_count)
        self.assertEqual(get_task_summary.data.get('assigned_to_me'), assigned_to_me_count)
        self.assertEqual(get_task_summary.data.get('assigned_by_me'), assigned_by_me_count)

        # We assigned the task to first user, now we will login from first user and check the count
        self.client.login(email=self.users[0][0], password=self.users[0][1])

        # get count of first users from database
        observed_by_count = Task.objects.filter(task_associations__user=self.user_detail_first,
                                                task_associations__association=OBSERVER).count()
        assigned_by_me_count = Task.objects.filter(created_by=self.user_detail_first).count()
        assigned_to_me_count = Task.objects.filter(task_associations__user=self.user_detail_first,
                                                   task_associations__association=RESPONSIBLE_PERSON).count()
        get_task_summary = self.client.get(self.task_summary_url)

        # test the count
        self.assertEqual(get_task_summary.data.get('observed_by_me'),
                         observed_by_count)
        self.assertEqual(get_task_summary.data.get('assigned_to_me'), assigned_to_me_count)
        self.assertEqual(get_task_summary.data.get('assigned_by_me'), assigned_by_me_count)

        # Now log in as a third user and test
        self.client.login(email=self.users[2][0], password=self.users[2][1])

        observed_by_count = Task.objects.filter(task_associations__user=self.user_detail_third,
                                                task_associations__association=OBSERVER).count()
        assigned_by_me_count = Task.objects.filter(created_by=self.user_detail_third).count()
        assigned_to_me_count = Task.objects.filter(task_associations__user=self.user_detail_third,
                                                   task_associations__association=RESPONSIBLE_PERSON).count()

        # test count
        get_task_summary = self.client.get(self.task_summary_url)
        self.assertEqual(get_task_summary.data.get('observed_by_me'),
                         observed_by_count)
        self.assertEqual(get_task_summary.data.get('assigned_to_me'), assigned_to_me_count)
        self.assertEqual(get_task_summary.data.get('assigned_by_me'), assigned_by_me_count)

    def _assign_task(self, core_task_created, data=None):
        """
        function creates the task of users
        :param core_task_created: created core task is required to assign a task
        :param data: task data
        :return: repose after task is created
        """
        if not data:
            data = {
                'title': 'First Task',
                'starts_at': timezone.now() + relativedelta(days=10),
                'deadline': timezone.now() + relativedelta(days=30),
                'responsible_persons': [
                    {
                        'user': self.user_detail_second.id,
                        'core_tasks': [core_task_created.id, ]
                    },
                ],
                'observers': [
                    {
                        "user": self.user_detail_third.id
                    },
                ]
            }
        response = self.client.post(self.post_list_url, data=data, format='json')
        # test task is created or not
        self.assertEqual(response.status_code, 201)

        return response

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
