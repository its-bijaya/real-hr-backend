from datetime import timedelta

from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.task.api.v1.tests.factory import ProjectFactory, WorkLogFactory, ActivityFactory, \
    TaskFactory, CoreTaskFactory
from irhrs.task.models import WorkLog, WorkLogAction, DRAFT, REQUESTED, APPROVED, DENIED, \
    FORWARDED, CONFIRMED, CANCELED, ACKNOWLEDGED, TODO, SENT
from irhrs.task.models.settings import UserActivityProject
from irhrs.users.models import UserSupervisor


class TestWorkLog(RHRSAPITestCase):
    users = [
        ('admin@email.com', 'password', 'Male'),
        ('normal@email.com', 'password', 'Male'),
        ('supervisor@email.com', 'password', 'Male'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.activity = ActivityFactory()
        self.project = ProjectFactory()
        self.task = TaskFactory(
            deadline=get_today(with_time=True) + timedelta(days=7)
        )
        self.core_task = CoreTaskFactory()
        self.worklog = WorkLogFactory(sender=self.admin)
        self.worklog2 = WorkLogFactory(sender=self.created_users[1], receiver=self.admin)

        UserSupervisor.objects.create(
            user=self.created_users[1],
            supervisor=self.admin,
            approve=True, deny=True, forward=True,
            authority_order=1
        )
        UserSupervisor.objects.create(
            user=self.created_users[1],
            supervisor=self.created_users[2],
            approve=True, deny=True, forward=True,
            authority_order=2
        )
        UserSupervisor.objects.create(
            user=self.admin,
            supervisor=self.created_users[2],
            approve=True, deny=True, forward=True,
            authority_order=1
        )

    @property
    def create_todo_url(self):
        return reverse(
            'api_v1:task:worklog-create-todo'
        )

    @property
    def start_todo_url(self):
        return reverse(
            'api_v1:task:worklog-start-todo',
            kwargs={
                'pk': self.worklog.id
            }
        )

    @property
    def create_daily_task_url(self):
        return reverse(
            'api_v1:task:worklog-update-daily-task',
            kwargs={
                'pk': self.worklog.id
            }
        )

    @property
    def send_worklog_url(self):
        return reverse(
            'api_v1:task:worklog-send-worklog',
            kwargs={
                'pk': self.worklog.id
            }
        )

    @property
    def approve_worklog_url(self):
        return reverse(
            'api_v1:task:worklog-approve-create-request'
        ) + "?as=hr"

    @property
    def deny_worklog_url(self):
        return reverse(
            'api_v1:task:worklog-deny-create-request'
        ) + "?as=hr"

    @property
    def forward_worklog_url(self):
        return reverse(
            'api_v1:task:worklog-forward-create-request'
        ) + "?as=supervisor"

    @property
    def confirm_worklog_url(self):
        return reverse(
            'api_v1:task:worklog-confirm-action'
        ) + "?as=hr"

    @property
    def cancel_worklog_url(self):
        return reverse(
            'api_v1:task:worklog-cancel-action',
            kwargs={
                'pk': self.worklog.id
            }
        )

    @property
    def acknowledge_worklog_url(self):
        return reverse(
            'api_v1:task:worklog-acknowledge-action',
            kwargs={
                'pk': self.worklog.id
            }
        )

    @property
    def create_todo_payload(self):
        return {
           "requests": [
              {
                 "activity_description": "Task1"
              },
              {
                 "activity_description": "Task2"
              }
           ]
        }

    @property
    def start_todo_paylod(self):
        return {
            "start_time": get_today(with_time=True)
        }

    @property
    def create_daily_task_paylod(self):
        return {
            "project": self.project.id,
            "activity": self.activity.id,
            "unit": 10,
            "task": self.task.id,
            "core_task": [self.core_task.id],
            "start_time": get_today(with_time=True),
            "end_time": get_today(with_time=True),
            "activity_description": "Description"
        }

    @property
    def send_worklog_payload(self):
        return {
            "remarks": "Sending Worklog"
        }

    @property
    def approve_worklog_payload(self):
        return {
           "requests": [
              {
                 "worklog": self.worklog.id,
                 "remarks": "Approved",
                 "score": 10
              }
           ]
        }

    @property
    def deny_worklog_payload(self):
        return {
            "requests": [
                {
                    "worklog": self.worklog.id,
                    "remarks": "Denied"
                }
            ]
        }

    @property
    def forward_worklog_payload(self):
        return {
            "requests": [
                {
                    "worklog": self.worklog2.id,
                    "remarks": "Forwarded"
                }
            ]
        }

    @property
    def confirm_worklog_payload(self):
        return {
            "requests": [
                {
                    "worklog": self.worklog2.id,
                    "remarks": "Confirmed"
                }
            ]
        }

    @property
    def cancel_worklog_payload(self):
        return {
            "worklog": self.worklog2.id,
            "remarks": "Canceled"
        }

    @property
    def acknowledge_worklog_payload(self):
        return {
            "worklog": self.worklog.id,
            "remarks": "Acknowledged"
        }

    def test_create_todo(self):
        response = self.client.post(
            self.create_todo_url,
            self.create_todo_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertTrue(WorkLog.objects.get(activity_description="Task1"))
        self.assertTrue(WorkLog.objects.get(activity_description="Task2"))

    def test_start_todo(self):
        response = self.client.put(
            self.start_todo_url,
            data=self.start_todo_paylod,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('start_time')[:10],
            get_today().strftime("%Y-%m-%d")
        )

    def test_create_daily_task(self):
        WorkLogAction.objects.create(
            action_performed_by=self.admin,
            worklog=self.worklog,
            action=TODO,
            remarks="Daily Log created by user"
        )
        response = self.client.put(
            self.create_daily_task_url,
            data=self.create_daily_task_paylod,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('project'),
            self.project.id
        )

    def test_send_worklog(self):
        WorkLogAction.objects.create(
            action_performed_by=self.admin,
            worklog=self.worklog,
            action=DRAFT,
            remarks="Daily Log created by user"
        )
        response = self.client.post(
            self.send_worklog_url,
            self.send_worklog_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(WorkLogAction.objects.get(action=REQUESTED))

    def test_approve_create_request(self):
        WorkLogAction.objects.create(
            action_performed_by=self.admin,
            worklog=self.worklog,
            action=REQUESTED,
            remarks="Daily Log created by user"
        )
        response = self.client.post(
            self.approve_worklog_url,
            self.approve_worklog_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(WorkLogAction.objects.get(action=APPROVED))
        self.assertTrue(WorkLogAction.objects.get(remarks="Approved"))

    def test_deny_create_request(self):
        WorkLogAction.objects.create(
            action_performed_by=self.admin,
            worklog=self.worklog,
            action=REQUESTED,
            remarks="Daily Log created by user"
        )
        response = self.client.post(
            self.deny_worklog_url,
            self.deny_worklog_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(WorkLogAction.objects.get(action=DENIED))
        self.assertTrue(WorkLogAction.objects.get(remarks="Denied"))

    def test_forward_create_request(self):
        WorkLogAction.objects.create(
            action_performed_by=self.admin,
            worklog=self.worklog2,
            action=REQUESTED,
            remarks="Daily Log created by user"
        )
        response = self.client.post(
            self.forward_worklog_url,
            self.forward_worklog_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(WorkLogAction.objects.get(action=FORWARDED))
        self.assertTrue(WorkLogAction.objects.get(remarks="Forwarded"))

    def test_confirm_action_request(self):
        WorkLogAction.objects.create(
            action_performed_by=self.admin,
            worklog=self.worklog2,
            action=ACKNOWLEDGED,
            remarks="Daily Log created by user"
        )
        response = self.client.post(
            self.confirm_worklog_url,
            self.confirm_worklog_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(WorkLogAction.objects.get(action=CONFIRMED))
        self.assertTrue(WorkLogAction.objects.get(remarks="Confirmed"))

    def test_cancel_action(self):
        WorkLogAction.objects.create(
            action_performed_by=self.admin,
            worklog=self.worklog,
            action=REQUESTED,
            remarks="Daily Log created by user"
        )
        response = self.client.post(
            self.cancel_worklog_url,
            self.cancel_worklog_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(WorkLogAction.objects.get(action=CANCELED))
        self.assertTrue(WorkLogAction.objects.get(remarks="Canceled"))

    def test_acknowledge_action(self):
        WorkLogAction.objects.create(
            action_performed_by=self.admin,
            worklog=self.worklog,
            action=APPROVED,
            remarks="Daily Log created by user"
        )
        response = self.client.post(
            self.acknowledge_worklog_url,
            self.acknowledge_worklog_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(WorkLogAction.objects.get(action=ACKNOWLEDGED))
        self.assertTrue(WorkLogAction.objects.get(remarks="Acknowledged"))

    def tearDown(self) -> None:
        WorkLogAction.objects.all().delete()
        return super().tearDown()


class TestWorkLogReport(RHRSAPITestCase):
    users = [
        ('admin@email.com', 'password', 'Male')
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.activity = ActivityFactory()
        self.project = ProjectFactory(is_billable=True)
        UserActivityProject.objects.create(
            user=self.admin,
            project=self.project,
            activity=self.activity,
            is_billable=True,
            employee_rate=500
        )
        self.worklog = WorkLogFactory(sender=self.admin, project=self.project, activity=self.activity)

    @property
    def report_get_url(self):
        return reverse(
            'api_v1:task:report-list'
        )

    @property
    def report_send_to_payroll_url(self):
        return reverse(
            'api_v1:task:report-send-worklog-to-payroll'
        )

    @property
    def report_send_to_payroll_payload(self):
        return {
            "requests": [
                {
                    "worklog": self.worklog.id
                }
            ]
        }

    def test_worklog_report(self):
        WorkLogAction.objects.create(
            action_performed_by=self.admin,
            worklog=self.worklog,
            action=CONFIRMED,
            score=9,
            action_date=get_today(with_time=True),
            remarks="Daily Log created by user"
        )
        response = self.client.get(self.report_get_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('count'),
            1
        )

    def test_worklog_sent_to_payroll(self):
        response = self.client.post(
            self.report_send_to_payroll_url,
            self.report_send_to_payroll_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json(),
            ['Worklog action not found.']
        )

        WorkLogAction.objects.create(
            action_performed_by=self.admin,
            worklog=self.worklog,
            action=ACKNOWLEDGED,
            score=9,
            action_date=get_today(with_time=True),
            remarks="Daily Log created by user"
        )
        response = self.client.post(
            self.report_send_to_payroll_url,
            self.report_send_to_payroll_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json(),
            ['Worklog must be in confirmed state before sending to payroll.']
        )

        WorkLogAction.objects.create(
            action_performed_by=self.admin,
            worklog=self.worklog,
            action=CONFIRMED,
            score=9,
            action_date=get_today(with_time=True),
            remarks="Daily Log created by user"
        )
        response = self.client.post(
            self.report_send_to_payroll_url,
            self.report_send_to_payroll_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(WorkLogAction.objects.get(action=SENT))

    def tearDown(self) -> None:
        WorkLogAction.objects.all().delete()
        return super().tearDown()
