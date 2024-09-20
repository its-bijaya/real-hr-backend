import json
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.constants.payroll import EMPLOYEE, REQUESTED, APPROVED, DENIED, CANCELED
from irhrs.reimbursement.api.v1.serializers.reimbursement import \
    AdvanceExpenseRequestDetailSerializer, AdvanceExpenseRequestApprovalsSerializer
from irhrs.reimbursement.api.v1.tests.factory import ExpenseApprovalSettingFactory, \
    ReimbursementSettingFactory
from irhrs.reimbursement.models import AdvanceExpenseRequest
from django.core import mail

from irhrs.reimbursement.models.setting import ExpenseApprovalSetting

def can_send_email(user, email_type):
        return True

class TestAdvanceExpenseRequest(RHRSTestCaseWithExperience):
    organization_name = 'Facebook'

    users = [
        ('emaila@test.com', 'password', 'Male', 'Clerka'),
        ('emailb@test.com', 'password', 'Male', 'Clerkb'),
        ('emailc@test.com', 'password', 'Male', 'Clerkc'),
        ('emaild@test.com', 'password', 'Male', 'Clerkd'),
        ('emaile@test.com', 'password', 'Male', 'Clerke'),
        ('emailf@test.com', 'password', 'Male', 'Clerkf'),
        ('emailg@test.com', 'password', 'Male', 'Clerkg'),
    ]
    kwargs = {}

    def setUp(self):
        super().setUp()
        self.client.force_login(self.created_users[1])
        self.kwargs = {
            'organization_slug': self.organization.slug
        }
        self.set_approval_levels()
        ReimbursementSettingFactory(organization=self.organization)

    def set_approval_levels(self):
        approvals = self.created_users[5:]
        for index, approval in enumerate(approvals, start=1):
            setting = ExpenseApprovalSettingFactory(
                organization=self.organization,
                approve_by=EMPLOYEE,
                approval_level=index,
                select_employee=index==1
            )
            setting.employee.set([approval])

    @property
    def advance_expense_request_url(self):
        action = 'list'
        if 'pk' in self.kwargs:
            action = 'detail'
        return reverse(
            f'api_v1:reimbursement:advance-expense-request-{action}',
            kwargs=self.kwargs
        )

    @property
    def data(self):
        users = [user.id for user in self.created_users[5:]]
        return {
            'reason': 'Test expense',
            'type': 'Other',
            'description': 'Test Expense',
            "detail": [
                {
                    'heading': 'heading 1',
                    'particulars': 'particulars 1',
                    'quantity': 1,
                    'rate': 120,
                    'remarks': 'asdasdsad',
                },
            ],
            "selected_approvers": [
                {
                    "approval_level": 1,
                    "recipient": self.created_users[5].id
                }
            ]
        }

    def create_advance_expense(self, validate=True):
        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.post(
                path=self.advance_expense_request_url,
                data=self.data,
                format='json'
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        instance = AdvanceExpenseRequest.objects.get(id=response.json().get('id'))
        if validate:
            self.validate_create_for_success(self.data, instance)
        return instance

    def test_create_action(self):
        """
        Create setting with HR
        """
        """
        Create by admin with all permission
        """
        instance = self.create_advance_expense()

        """
        Request user within associates
        """
        self.data['associates'] = [self.created_users[1].id]
        response = self.client.post(
            path=self.advance_expense_request_url,
            data=self.data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self._test_retrieve_action(instance)

    def validate_create_for_success(self, data, instance):
        self.assertEqual(data.get('type'), instance.type)
        self.assertEqual(data.get('reason'), instance.reason)

    def _test_retrieve_action(self, instance):
        self.kwargs.update({
            'pk': instance.id
        })
        response = self.client.get(self.advance_expense_request_url+'?expense_type=Other')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        associates = list(
            map(
                lambda x: x.get('id'),
                response.json().pop('associates')
            )
        )
        self.assertEqual(
            associates,
            list(instance.associates.values_list('id', flat=True))
        )
        expense_request_qs = AdvanceExpenseRequest.objects.filter(id=instance.id)
        details = response.json().pop('detail', [])
        approvals = response.json().pop('approvals', [])
        _ = response.json().pop('recipient', [])
        self.validate_data(
            results=[response.json()],
            data=expense_request_qs
        )

        expense_request = expense_request_qs[0]
        query_detail = AdvanceExpenseRequestDetailSerializer(
            json.loads(expense_request.detail),
            many=True
        ).data
        for index, detail in enumerate(details):
            self.assertDictEqual(query_detail[index], detail)

        query_associates = AdvanceExpenseRequestApprovalsSerializer(
            expense_request.approvals.all(),
            many=True
        ).data
        for index, approval in enumerate(approvals):
            self.assertDictEqual(query_associates[index], approval)

    def test_approve_action(self):
        pass

    def _validate_approve_and_deny_actions(self, action):
        action_map = {
            'approve': REQUESTED,
            'deny': DENIED
        }
        instance = self.create_advance_expense(validate=False)
        self.kwargs = {
            'pk': instance.id,
            'organization_slug': self.organization.slug
        }

        url = reverse(
            f'api_v1:reimbursement:advance-expense-request-{action}',
            kwargs=self.kwargs
        ) + '?as=approver'

        """
        Action performed by user who is not approver
        """
        self.client.login(email=self.users[2][0], password=self.users[2][1])
        response = self.client.post(
            url,
            data= {'remarks': 'test remarks'}
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'This is handled by get_queryset'
        )

        """
        Action performed by approver
        """
        self.client.login(email=self.users[5][0], password=self.users[5][1])
        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.post(url, data={'remarks': 'test remarks'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 2)
        instance.refresh_from_db()
        self.assertEqual(instance.status, action_map.get(action))
        return instance, url

    def test_deny_action(self):
        instance, url = self._validate_approve_and_deny_actions(action='deny')

        self.client.login(email=self.users[-1][0], password=self.users[-1][1])
        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.post(
                url,
                data={'remarks': 'test remarks'},
                format='json'
            )
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_action(self):
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        instance = self.create_advance_expense(validate=False)

        self.kwargs.update({
            'pk': instance.id
        })

        url = reverse(
            f'api_v1:reimbursement:advance-expense-request-cancel',
            kwargs=self.kwargs
        )

        """
        request by user who didn't request for advance expense
        """
        self.client.force_login(self.created_users[5])
        response = self.client.post(
            url,
            data={'remarks': 'test remarks'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        """
        canceled by user who requested advance expense
        """
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        response = self.client.post(
            url,
            data={'remarks': 'test remarks'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        instance.refresh_from_db()
        self.assertEqual(instance.status, CANCELED)

        """
        Trying to perform approve action after cancel action
        """
        url = reverse(
            f'api_v1:reimbursement:advance-expense-request-cancel',
            kwargs=self.kwargs
        ) + "?as=approver"
        self.client.force_login(self.created_users[5])
        response = self.client.post(
            url,
            data={'remarks': 'test remarks'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        """
        Trying to perform deny action after cancel action
        """
        url = reverse(
            f'api_v1:reimbursement:advance-expense-request-deny',
            kwargs=self.kwargs
        ) + "?as=approver"
        response = self.client.post(
            url,
            data={'remarks': 'test remarks'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
