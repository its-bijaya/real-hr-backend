import os
import random

from dateutil.relativedelta import relativedelta
from django.core.files.storage import default_storage
from django.db.models import F, Count, Q
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from xhtml2pdf.document import pisaDocument

from irhrs.task.api.v1.tests import TaskSetUp
from irhrs.task.constants import (MAJOR, MINOR,
                                  CRITICAL, RESPONSIBLE_PERSON)
from irhrs.task.models.task import Task, TaskAssociation, TaskComment
from irhrs.users.models import UserSupervisor


class TaskAssignedToMe(TaskSetUp):
    file = None

    def setUp(self):
        super().setUp()
        self._create_tasks()

    def tearDown(self) -> None:
        super().tearDown()
        if self.file:
            os.remove(self.file.name)

    def test_assigned_by_me(self):
        """
        test different test scenario associated to task assigned to me
        :return:
        """
        self._test_for_top_task_assigner()
        self._test_for_result_area()
        self._test_task_attachments()
        self._test_comment_on_assigned_task()

    def _test_for_top_task_assigner(self):
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        start_date = (timezone.now() - relativedelta(months=1)).date()
        end_date = timezone.now().date()
        for association in self.associations[:-1]:
            _filter = {
                'association': self.involvement_choices.get(association),
            }
            top_assigner = TaskAssociation.objects.filter(
                user=self.sys_user[0],
                **_filter
            ).values('created_by').annotate(
                total_assigned=Count('task', distinct=True),
                user=F('created_by')
            ).order_by('-total_assigned')

            response = self.client.get(
                reverse("api_v1:task:task-overview-v2-top-assigner"),
                data={
                    'as': association,
                    'start_date': start_date,
                    'end_date': end_date
                }
            )
            for i, assigner in enumerate(top_assigner):
                self.assertEqual(
                    response.json().get('results')[i].get('total_assigned'),
                    assigner.get('total_assigned')
                )

                self.assertEqual(
                    response.json().get('results')[i].get('user').get('id'),
                    assigner.get('user')
                )

    def _test_for_result_area(self):
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        start_date = (timezone.now() - relativedelta(months=1)).date()
        end_date = timezone.now().date()
        queryset = Task.objects.base().filter(
            task_associations__user=self.sys_user[0],
            task_associations__association=RESPONSIBLE_PERSON,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values('task_associations__core_tasks__result_area'
                 ).annotate(
            result_area=F('task_associations__core_tasks__result_area__title'),
            result_area_id=F('task_associations__core_tasks__result_area'),
            total=Count('id', distinct=True),
            critical=Count('id', filter=Q(priority=CRITICAL), distinct=True),
            major=Count('id', filter=Q(priority=MAJOR), distinct=True),
            minor=Count('id', filter=Q(priority=MINOR), distinct=True)
        ).order_by('-critical')
        queryset = queryset.filter(result_area_id__isnull=False)

        response = self.client.get(
            reverse('api_v1:task:task-overview-v2-result-area')
        )
        self.assertEqual(queryset.count(), response.json().get('count'))
        results = response.json().get('results')
        for i, result_area in enumerate(queryset):
            result = results[i]
            self.assertEqual(result_area.get('result_area'), result.get('result_area'))
            self.assertEqual(result_area.get('result_area_id'), result.get('result_area_id'))
            self.assertEqual(result_area.get('total'), result.get('total'))
            self.assertEqual(result_area.get('critical'), result.get('critical'))
            self.assertEqual(result_area.get('major'), result.get('major'))
            self.assertEqual(result_area.get('minor'), result.get('minor'))

    def _test_task_attachments(self):
        self.client.login(email=self.users[2][0], password=self.users[2][1])
        self.generate_file()
        task = self.create_single_task()
        self.task_attachment_list_url = reverse(
            "api_v1:task:task-attachment-list",
            kwargs={
                'task_id': task.id
            }
        )
        """
        --------------------------------------------------------------------------------------------
        trying to upload attachment being responsible person of a task
        response -> must be able to upload attachments
        """
        self.validate_attachment_upload(task=task)

        """
        --------------------------------------------------------------------------------------------
        trying to upload attachment being task creator
        response -> must be able to upload attachments
        """
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1]
        )
        self.validate_attachment_upload(task=task)

        """
        --------------------------------------------------------------------------------------------
        trying to upload attachment being observer of a task
        response -> must be able to upload attachments
        """
        self.client.login(
            email=self.users[-1][0],
            password=self.users[-1][1]
        )
        self.validate_attachment_upload(task=task)

        """
        --------------------------------------------------------------------------------------------
        trying to upload attachment by user not associated with task
        response -> Must raise permission issue while uploading attachment
        """
        self.client.login(
            email=self.users[1][0],
            password=self.users[1][1]
        )
        with open(self.file.name, 'rb') as file:
            response = self.client.post(
                self.task_attachment_list_url,
                data={
                    'attachment': file,
                    'caption': self.fake.text(max_nb_chars=150),
                    'task': task.id
                }
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            'Must raise permission issue while uploading attachment'
        )

    def _test_comment_on_assigned_task(self):
        """
        this test covers scenario where person associated to task can comment or not within task
        :return:
        """
        task = self.create_single_task()
        self.task_attachment_list_url = reverse(
            "api_v1:task:task-comments-list",
            kwargs={
                'task_id': task.id
            }
        )

        """
        --------------------------------------------------------------------------------------------
        trying to add comment being task creator
        response -> must be able to upload attachments
        """
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1]
        )
        self.validate_task_comment(task=task)

        """
        --------------------------------------------------------------------------------------------
        trying to add comment being responsible person of a task
        response -> must be able to upload attachments
        """
        self.client.login(email=self.users[2][0], password=self.users[2][1])
        self.validate_task_comment(task=task)

        """
        --------------------------------------------------------------------------------------------
        trying to add comment being observer of a task
        response -> must be able to upload attachments
        """
        self.client.login(
            email=self.users[-1][0],
            password=self.users[-1][1]
        )
        self.validate_task_comment(task=task)

        """
        --------------------------------------------------------------------------------------------
        trying to add comment by user not associated with task
        response -> Must raise permission issue while uploading attachment
        """
        self.client.login(
            email=self.users[1][0],
            password=self.users[1][1]
        )
        with open(self.file.name, 'rb') as file:
            response = self.client.post(
                self.task_attachment_list_url,
                data={
                    'attachment': file,
                    'caption': self.fake.text(max_nb_chars=150),
                    'task': task.id
                }
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            'Must raise permission issue while uploading attachment'
        )
        UserSupervisor.objects.create(
            supervisor=self.created_users[1],
            user=self.created_users[2],
            approve=True,
            deny=True,
            forward=True,
            authority_order=1
        )
        self.client.logout()
        self.client.force_login(self.created_users[1])
        url = reverse(
            'api_v1:task:task-comments-list',
            kwargs={
                'task_id': task.id
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 3)
        actual_comments = {item.get('comment') for item in response.json().get('results')}
        expected_comments = TaskComment.objects.values_list('comment', flat=True)
        self.assertEqual(actual_comments, set(expected_comments))

    def _test_top_task_assigner_for_task_observed_by_me(self):
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        start_date = (timezone.now() - relativedelta(months=1)).date()
        end_date = timezone.now().date()
        for association in self.associations[:-1]:
            _filter = {
                'association': self.involvement_choices.get(association),
            }
            top_assigner = TaskAssociation.objects.filter(
                user=self.sys_user[0],
                **_filter
            ).values('created_by').annotate(
                total_assigned=Count('task', distinct=True),
                user=F('created_by')
            ).order_by('-total_assigned')

            response = self.client.get(
                reverse("api_v1:task:task-overview-v2-top-assigner"),
                data={
                    'as': association,
                    'start_date': start_date,
                    'end_date': end_date
                }
            )
            for i, assigner in enumerate(top_assigner):
                self.assertEqual(
                    response.json().get('results')[i].get('total_assigned'),
                    assigner.get('total_assigned')
                )

                self.assertEqual(
                    response.json().get('results')[i].get('user').get('id'),
                    assigner.get('user')
                )

    def validate_task_comment(self, task, data=None):
        response = self.client.post(
            self.task_attachment_list_url,
            data={
                'comment': self.fake.text(max_nb_chars=150),
                'task': task.id
            } if not data else data
        )

        data = task.task_attachments.filter(id=response.json().get('id'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.validate_data(data=data, results=[response])

    def validate_attachment_upload(self, task):
        with open(self.file.name, 'rb') as file:
            response = self.client.post(
                self.task_attachment_list_url,
                data={
                    'attachment': file,
                    'caption': self.fake.text(max_nb_chars=150),
                    'task': task.id
                }
            )

            data = task.task_attachments.filter(id=response.json().get('id'))
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.validate_data(data=data, results=[response])

    def generate_file(self):
        file = default_storage.open(f'test_{self.fake.word()}.pdf', 'wb')
        pisaDocument(
            f'{self.fake.text()}'.encode(),
            file
        )
        file.close()
        self.file = file
