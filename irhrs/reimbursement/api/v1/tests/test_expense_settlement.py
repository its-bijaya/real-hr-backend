import json
import os
from urllib.parse import urlencode
from unittest.mock import patch

from django.conf import settings
from django.contrib import auth
from django.core.files.storage import default_storage
from django.urls import reverse
from rest_framework import status
from xhtml2pdf.document import pisaDocument
from django.core import mail

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.constants.payroll import EMPLOYEE, REQUESTED, APPROVED
from irhrs.organization.api.v1.tests.factory import EmailNotificationSettingFactory
from irhrs.organization.models import organization
from irhrs.reimbursement.api.v1.serializers.settlement import SettlementDetailSerializer, \
    SettlementApprovalsSerializer
from irhrs.reimbursement.api.v1.tests.factory import ExpenseApprovalSettingFactory, \
    AdvanceExpenseRequestFactory, ReimbursementSettingFactory, \
    ExpenseSettlementFactory
from irhrs.reimbursement.constants import CASH, BUSINESS, TRAVEL, MEDICAL
from irhrs.reimbursement.models import (
    ExpenseSettlement,
    SettlementApprovalSetting
)
from irhrs.reimbursement.models.setting import SettlementOptionSetting

def can_send_email(user, email_type):
    return True

class SettlementSetUp(RHRSAPITestCase):
    organization_name = 'Test1'

    users = [
        ('emaila@test.com', 'password', 'Male'),
        ('emailb@test.com', 'password', 'Male'),
        ('emailc@test.com', 'password', 'Male'),
        ('emaild@test.com', 'password', 'Male'),
        ('emaile@test.com', 'password', 'Male'),
        ('emailf@test.com', 'password', 'Male'),
        ('emailg@test.com', 'password', 'Male'),
    ]
    kwargs = {}
    file = None

    def setUp(self):
        super().setUp()
        self.test_file = self.generate_document()
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        self.kwargs = {
            'organization_slug': self.organization.slug
        }
        self.approvers = self.set_approval_levels()
        self.setting = ReimbursementSettingFactory(organization=self.organization)

    def set_approval_levels(self):
        approvals = self.created_users[5:]
        for index, approval in enumerate(approvals, start=1):
            setting = ExpenseApprovalSettingFactory(
                organization=self.organization,
                approve_by=EMPLOYEE,
                approval_level=index
            )
            setting.employee.set([approval])

        for index, approval in enumerate(approvals, start=1):
            setting = SettlementApprovalSetting.objects.create(
                organization=self.organization,
                approve_by=EMPLOYEE,
                approval_level=index,
                select_employee=index==1
            )
            setting.employee.set([approval])
        return approvals

    @property
    def settlement_url(self):
        action = 'list'
        if 'pk' in self.kwargs:
            action = 'detail'
        return reverse(
            f'api_v1:reimbursement:expense-settlement-{action}',
            kwargs=self.kwargs
        )

    def tearDown(self) -> None:
        super().tearDown()
        if self.test_file:
            os.remove(self.test_file.name)

    @staticmethod
    def file_path(file):
        return os.path.join(
            settings.MEDIA_ROOT,
            file.name.split('media')[-1]
        )

    @staticmethod
    def generate_document():
        file = default_storage.open(f'test_settlement.pdf', 'wb')
        pisaDocument(
            'test asd asdjjas jaskjk'.encode(),
            file
        )
        file.close()
        return file

    def settlement_action_url(self, action_='approve', as_=None):
        as_text = ''
        if as_:
            as_text = f'?as={as_}'
        return reverse(
            f'api_v1:reimbursement:expense-settlement-{action_}',
            kwargs=self.kwargs
        ) + as_text


class TestExpenseSettlement(SettlementSetUp):
    @property
    def data(self):
        data = [
            ('reason', 'Test expense'),
            ('description', 'This is description'),
            ('type', 'Other'),
            ('remark', 'Test Expense'),
            ('detail[0]heading', 'heading 1'),
            ('detail[0]particulars', 'particulars 1'),
            ('detail[0]quantity', 1),
            ('detail[0]rate', 120),
            ('detail[0]remarks', 'asdasdsad'),
            ('detail[0]bill_no', '123123'),
            ('selected_approvers[0]approval_level', 1),
            ('selected_approvers[0]recipient', self.created_users[5].id)
            # ('detail[1]heading', 'heading 2'),
            # ('detail[1]particulars', 'particulars 2'),
            # ('detail[1]quantity', 3),
            # ('detail[1]rate', 120),
            # ('detail[1]remarks', 'asdasdsad'),
            # ('detail[1]bill_no', '123123'),
        ]
        return data

    @property
    def factory_data(self):
        detail = [
            {
                'heading': 'heading 1',
                'particulars': 'particulars 1',
                'quantity': 1,
                'rate': 120,
                'remarks': 'asdasdsad',
                'bill_no': '123123'
            },
            {
                'heading': 'heading 2',
                'particulars': 'particulars 2',
                'quantity': 3,
                'rate': 120,
                'remarks': 'asdasdsad',
                'bill_no': '123123'
            }
        ]

        data = {
            'reason': 'Test expense',
            'type': 'Other',
            'remark': 'Test Expense',
            'detail': json.dumps(detail),
            'employee': self.created_users[1],
            'recipient': self.created_users[5],
            'status': REQUESTED
        }
        return data

    def create_advance_expense(self, validate=True):
        data = self.data.copy()
        with default_storage.open(self.test_file.name, 'rb') as f:
            data.append(('travel_report', f))
            response = self.client.post(
                self.settlement_url,
                data=dict(data),
                format='multipart'
            )
        return response

    def test_create_action(self):
        """
        Create setting with HR
        """
        """
        Create by admin with all permission
        """
        response = self.create_advance_expense()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        instance = ExpenseSettlement.objects.get(id=response.json().get('id'))
        _data = dict(self.data)
        self.assertEqual(_data.get('reason'), instance.reason)
        self.assertEqual(_data.get('type'), instance.type)
        self.assertEqual(_data.get('remark'), instance.remark)
        self.assertEqual(instance.status, REQUESTED)
        self._test_retrieve_action(instance)

    def _test_retrieve_action(self, instance):
        self.kwargs.update({
            'pk': instance.id
        })
        response = self.client.get(self.settlement_url + '?settle_type=Other')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        settlement_qs = ExpenseSettlement.objects.filter(id=instance.id)
        details = response.json().pop('detail', [])
        approvals = response.json().pop('approvals', [])
        _ = response.json().pop('recipient', [])

        _= response.json().pop('travel_report', None)
        self.validate_data(
            results=[response.json()],
            data=settlement_qs
        )

        settlement = settlement_qs[0]
        query_detail = SettlementDetailSerializer(
            json.loads(settlement.detail),
            many=True
        ).data
        for index, detail in enumerate(details):
            self.assertDictEqual(query_detail[index], detail)

        query_associates = SettlementApprovalsSerializer(
            settlement.approvals.all(),
            many=True
        ).data
        for index, approval in enumerate(approvals):
            self.assertDictEqual(query_associates[index], approval)


class TestExpenseSettlementWithExpense(SettlementSetUp):
    def setUp(self):
        super().setUp()
        self.expense = AdvanceExpenseRequestFactory(**self.factory_data)
        self.expense.recipient.set([self.created_users[5]])
        SettlementOptionSetting.objects.create(setting=self.setting, option=CASH)

    @property
    def data(self):
        data = [
            ('reason', 'Test expense'),
            ('description', 'This is test description.'),
            ('type', 'Other'),
            ('remark', 'Test Expense'),
            ('detail[0]heading', 'heading 1'),
            ('detail[0]particulars', 'particulars 1'),
            ('detail[0]quantity', 2),
            ('detail[0]rate', 120),
            ('detail[0]remarks', 'asdasdsad'),
            ('detail[0]bill_no', '1231212asasd'),
            ('advance_expense', self.expense.id),
            ('option.settle_with', 'Cash'),
            ('option.remark', 'test'),
            ('selected_approvers[0]approval_level', 1),
            ('selected_approvers[0]recipient', self.created_users[5].id)
        ]
        return data

    @property
    def factory_data(self):
        detail = [
            {
                'heading': 'heading 1',
                'particulars': 'particulars 1',
                'quantity': 1,
                'rate': 120,
                'remarks': 'asdasdsad'
            },
            {
                'heading': 'heading 2',
                'particulars': 'particulars 2',
                'quantity': 3,
                'rate': 120,
                'remarks': 'asdasdsad'
            }
        ]

        data = {
            'type': 'Travel',
            'description': 'Test Expense',
            'detail': json.dumps(detail),
            'employee': self.created_users[1],
            'status': APPROVED,
            'total_amount': 480
        }
        return data

    def test_create_action(self):
        """
        test for positive test case
        """
        data = self.data.copy()
        with default_storage.open(self.test_file.name, 'rb') as f:
            data.append(('option.attachment', f))
            with patch('irhrs.core.utils.email.can_send_email', can_send_email):
                response = self.client.post(
                    self.settlement_url,
                    data=dict(data),
                    format='multipart'
                )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        self.assertEqual(len(mail.outbox), 1)
        instance = ExpenseSettlement.objects.get(id=response.json().get('id'))

        _data = dict(self.data)
        self.assertEqual(_data.get('reason'), instance.reason)
        self.assertEqual(_data.get('type'), instance.type)
        self.assertEqual(_data.get('remark'), instance.remark)
        self.assertEqual(self.expense, instance.advance_expense)
        self.assertEqual(instance.status, REQUESTED)
        instance.delete()

        """
        Unapproved advance expense set for settlement
        Negative Test Case
        """

        self.expense.status = REQUESTED
        self.expense.save()

        del data[-1]
        with default_storage.open(self.test_file.name, 'rb') as f:
            data.append(('option.attachment', f))
            response = self.client.post(
                self.settlement_url,
                data=dict(data),
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_is_taxable_field(self):
        logged_in_user = auth.get_user(self.client)
        expense_settlement_request = ExpenseSettlementFactory(
            reason = "Medical expense during survey.",
            advance_expense=self.expense,
            created_by=logged_in_user,
            status = REQUESTED,
            type=MEDICAL,
            employee=logged_in_user,
            recipient=self.approvers
        )
        payload = {
            'remarks': "Ok",
            'is_taxable': True
        }
        self.kwargs = {
            'pk': expense_settlement_request.id,
            'organization_slug': self.organization.slug
        }
        approve_url = self.settlement_action_url(
            action_='approve',
            as_='approver'
        )
        # login as approver
        self.client.force_login(user=self.approvers[0])
        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            res = self.client.post(
                approve_url,
                data=payload,
                format='json'
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            ExpenseSettlement.objects.get(
                id=expense_settlement_request.id
            ).is_taxable,
            True
        )


    def test_is_taxable_True_throws_validation_error_for_business_expense(self):
        logged_in_user = auth.get_user(self.client)
        expense_settlement_request = ExpenseSettlementFactory(
            reason = "Business Trip.",
            advance_expense=self.expense,
            status = REQUESTED,
            type=BUSINESS,
            employee=logged_in_user,
            recipient=self.approvers
        )
        payload = {
            'remarks': "Ok",
            'is_taxable': True
        }
        self.kwargs = {
            'pk': expense_settlement_request.id,
            'organization_slug': self.organization.slug
        }
        approve_url = self.settlement_action_url(
            action_='approve',
            as_='approver'
        )
        # login as approver
        self.client.force_login(user=self.approvers[0])
        res = self.client.post(
            approve_url,
            data=payload,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            res.json()['is_taxable'],
            ['Business and Travel expense type cannot be taxable.']
        )

    def test_is_taxable_edit_endpoint_works(self):
        logged_in_user = auth.get_user(self.client)
        expense_settlement_request = ExpenseSettlementFactory(
            reason = "Medical expense during survey.",
            advance_expense=self.expense,
            status = REQUESTED,
            type=MEDICAL,
            employee=logged_in_user,
            recipient=self.approvers,
            is_taxable=True,
        )
        exp_id = expense_settlement_request.id
        payload = {
            "is_taxable": False
        }
        self.url = reverse('api_v1:reimbursement:expense-settlement-is-taxable',
                           kwargs={
                               'organization_slug':self.organization.slug,
                               'pk':exp_id
                           }) + "?as=hr"
        response = self.client.post(
            self.url,
            data = payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_login(user=self.admin)
        response = self.client.post(
            self.url,
            data = payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            ExpenseSettlement.objects.get(id=expense_settlement_request.id).is_taxable,
            False
        )
